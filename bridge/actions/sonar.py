from __future__ import annotations

import json
import logging
import os
import ssl
import urllib.error
import urllib.request
from pathlib import Path

LOG = logging.getLogger(__name__)

CORE_PROPS_CANDIDATES = [
    r"%PROGRAMDATA%\SteelSeries\SteelSeries Engine 3\coreProps.json",
    r"%PROGRAMDATA%\SteelSeries\GG\coreProps.json",
    r"%LOCALAPPDATA%\SteelSeries\GG\coreProps.json",
]

PROBE_ENDPOINTS = [
    "/",
    "/subApps",
    "/sonar",
    "/sonar/volumeSettings/classic",
    "/sonar/volumeSettings",
    "/sonar/volumeSettings/streamer",
]


class SonarClient:
    """Small SteelSeries Sonar local-API wrapper.

    SteelSeries GG exposes a local API address via coreProps.json on Windows.
    Endpoint names have changed across GG/Sonar versions, so this client keeps
    discovery and requests isolated. The first live Windows test should run
    `python -m bridge.tools.sonar_probe` and paste the output back.
    """

    def __init__(self, config: dict):
        self.config = config or {}
        self.step = float(self.config.get("step", 0.03))
        self.channels = self.config.get("channels", {})
        self.api_base = self.config.get("api_base", "auto")
        self.tls_verify = bool(self.config.get("tls_verify", False))
        self._ssl_context = None if self.tls_verify else ssl._create_unverified_context()
        if self.api_base == "auto":
            self.api_base = self.discover_api_base()

    def discover_api_base(self) -> str | None:
        for template in CORE_PROPS_CANDIDATES:
            path = Path(os.path.expandvars(template))
            if not path.exists():
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                LOG.warning("Could not read %s: %s", path, exc)
                continue
            for key in ("ggEncryptedAddress", "address", "apiAddress", "ggAddress"):
                value = data.get(key)
                if value:
                    value = self.normalize_api_base(str(value), encrypted=(key == "ggEncryptedAddress"))
                    LOG.info("Discovered SteelSeries API from %s key %s: %s", path, key, value)
                    return value
        LOG.warning("Could not auto-discover SteelSeries GG API base. Set actions.sonar.api_base in config.json after probing.")
        return None

    @staticmethod
    def normalize_api_base(value: str | None, encrypted: bool = False) -> str | None:
        if not value:
            return None
        value = str(value).strip().rstrip("/")
        if not value:
            return None
        # SteelSeries coreProps.json commonly stores just "127.0.0.1:<port>".
        # urllib needs a real URL scheme. ggEncryptedAddress is HTTPS.
        if "://" not in value:
            value = ("https://" if encrypted else "http://") + value
        return value

    def alternate_api_base(self) -> str | None:
        if not self.api_base:
            return None
        if self.api_base.startswith("https://"):
            return "http://" + self.api_base[len("https://"):]
        if self.api_base.startswith("http://"):
            return "https://" + self.api_base[len("http://"):]
        return None

    def request(self, method: str, path: str, payload: dict | None = None):
        if not self.api_base:
            raise RuntimeError("SteelSeries GG API base not found. Is SteelSeries GG/Sonar running?")
        normalized_base = self.normalize_api_base(self.api_base)
        if not normalized_base:
            raise RuntimeError("SteelSeries GG API base not found. Is SteelSeries GG/Sonar running?")
        self.api_base = normalized_base
        url = normalized_base.rstrip("/") + path
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = urllib.request.Request(url, data=body, method=method.upper())
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=2, context=self._ssl_context) as resp:
                text = resp.read().decode("utf-8", errors="replace")
                if not text:
                    return None
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return text
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Sonar API HTTP {exc.code} for {path}: {detail}") from exc
        except Exception as exc:
            alternate = self.alternate_api_base()
            # If HTTP vs HTTPS was guessed wrong, try the other scheme once.
            if alternate:
                old_base = self.api_base
                self.api_base = alternate
                try:
                    return self.request(method, path, payload)
                except Exception:
                    self.api_base = old_base
            raise

    def probe(self) -> list[dict]:
        results = []
        original_base = self.api_base
        bases = [b for b in [original_base, self.alternate_api_base()] if b]
        seen = set()
        for base in bases:
            if base in seen:
                continue
            seen.add(base)
            self.api_base = base
            for endpoint in PROBE_ENDPOINTS:
                try:
                    data = self.request("GET", endpoint)
                    results.append({"base": self.api_base, "endpoint": endpoint, "ok": True, "data": data})
                except Exception as exc:
                    results.append({"base": self.api_base, "endpoint": endpoint, "ok": False, "error": str(exc)})
        self.api_base = original_base
        return results

    def get_volume_settings(self):
        # Known common endpoint from community reverse-engineering; may need adjustment per GG version.
        return self.request("GET", "/sonar/volumeSettings/classic")

    def set_channel_volume(self, channel: str, volume: float):
        channel_id = self.channels.get(channel, channel)
        volume = max(0.0, min(1.0, float(volume)))
        # Community endpoints have varied. Keep this isolated for quick correction after live probe.
        return self.request("PUT", f"/sonar/volumeSettings/classic/{channel_id}/Volume/{volume}")

    def adjust_channel(self, channel: str, delta: float):
        current = self.get_volume_settings()
        current_volume = self._extract_volume(current, self.channels.get(channel, channel))
        if current_volume is None:
            raise RuntimeError(f"Could not find current Sonar volume for {channel}. Probe output needed.")
        return self.set_channel_volume(channel, current_volume + delta)

    def _extract_volume(self, settings, channel_id: str) -> float | None:
        if isinstance(settings, dict):
            # Try common shapes defensively.
            for key, value in settings.items():
                if str(key).lower() == str(channel_id).lower():
                    if isinstance(value, dict):
                        for volume_key in ("volume", "Volume", "level"):
                            if volume_key in value:
                                return float(value[volume_key])
                    if isinstance(value, (int, float)):
                        return float(value)
            for value in settings.values():
                found = self._extract_volume(value, channel_id)
                if found is not None:
                    return found
        elif isinstance(settings, list):
            for item in settings:
                if isinstance(item, dict) and str(item.get("channel") or item.get("id") or item.get("name", "")).lower() == str(channel_id).lower():
                    for volume_key in ("volume", "Volume", "level"):
                        if volume_key in item:
                            return float(item[volume_key])
                found = self._extract_volume(item, channel_id)
                if found is not None:
                    return found
        return None

    def volume_up(self, channel: str):
        return self.adjust_channel(channel, self.step)

    def volume_down(self, channel: str):
        return self.adjust_channel(channel, -self.step)

    def toggle_mute(self, channel: str):
        # Placeholder until live probe confirms mute endpoint shape.
        channel_id = self.channels.get(channel, channel)
        return self.request("POST", f"/sonar/volumeSettings/classic/{channel_id}/Mute/Toggle")

    def rotate_output(self):
        # Placeholder until live probe confirms endpoint shape.
        return self.request("POST", "/sonar/output/rotate")

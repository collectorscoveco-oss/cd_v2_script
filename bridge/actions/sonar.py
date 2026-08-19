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
    "/mode",
    "/audioDevices",
    "/streamRedirections/",
    "/volumeSettings/classic",
    "/volumeSettings/streamer",
    "/subApps",
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
        self._mute_cache: dict[str, bool] = {}
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
                if not value:
                    continue
                engine_base = self.normalize_api_base(str(value), encrypted=(key == "ggEncryptedAddress"))
                LOG.info("Discovered SteelSeries Engine API from %s key %s: %s", path, key, engine_base)
                sonar_base = self.discover_sonar_from_engine(engine_base)
                if sonar_base:
                    LOG.info("Discovered Sonar API base from /subApps: %s", sonar_base)
                    return sonar_base
                # Fall back to the engine base only so the probe can still print /subApps.
                return engine_base
        LOG.warning("Could not auto-discover SteelSeries GG API base. Set actions.sonar.api_base in config.json after probing.")
        return None

    def discover_sonar_from_engine(self, engine_base: str | None) -> str | None:
        if not engine_base:
            return None
        for base in [engine_base, self.swap_scheme(engine_base)]:
            if not base:
                continue
            try:
                data = self.request_url("GET", base.rstrip("/") + "/subApps")
            except Exception as exc:
                LOG.debug("/subApps failed on %s: %s", base, exc)
                continue
            sonar = data.get("subApps", {}).get("sonar", {}) if isinstance(data, dict) else {}
            metadata = sonar.get("metadata", {}) if isinstance(sonar, dict) else {}
            address = metadata.get("webServerAddress")
            if address:
                return self.normalize_api_base(str(address), encrypted=False)
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

    @staticmethod
    def swap_scheme(value: str | None) -> str | None:
        if not value:
            return None
        if value.startswith("https://"):
            return "http://" + value[len("https://"):]
        if value.startswith("http://"):
            return "https://" + value[len("http://"):]
        return None

    def alternate_api_base(self) -> str | None:
        return self.swap_scheme(self.api_base)

    def request_url(self, method: str, url: str, payload: dict | None = None):
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = urllib.request.Request(url, data=body, method=method.upper())
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=2, context=self._ssl_context) as resp:
            text = resp.read().decode("utf-8", errors="replace")
            if not text:
                return None
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text

    def request(self, method: str, path: str, payload: dict | None = None):
        if not self.api_base:
            raise RuntimeError("SteelSeries GG API base not found. Is SteelSeries GG/Sonar running?")
        normalized_base = self.normalize_api_base(self.api_base)
        if not normalized_base:
            raise RuntimeError("SteelSeries GG API base not found. Is SteelSeries GG/Sonar running?")
        self.api_base = normalized_base
        url = normalized_base.rstrip("/") + path
        try:
            return self.request_url(method, url, payload)
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

    def get_mode(self) -> str:
        mode = self.request("GET", "/mode")
        return str(mode).strip('"') if mode else "classic"

    def get_volume_settings(self):
        mode = self.get_mode()
        return self.request("GET", f"/volumeSettings/{mode}")

    def set_channel_volume(self, channel: str, volume: float):
        channel_id = self.channels.get(channel, channel)
        volume = max(0.0, min(1.0, float(volume)))
        # Community endpoints have varied. Keep this isolated for quick correction after live probe.
        mode = self.get_mode()
        if mode == "streamer":
            return self.request("PUT", f"/volumeSettings/streamer/monitoring/{channel_id}/Volume/{volume}")
        return self.request("PUT", f"/volumeSettings/classic/{channel_id}/Volume/{volume}")

    def adjust_channel(self, channel: str, delta: float):
        current = self.get_volume_settings()
        current_volume = self._extract_volume(current, self.channels.get(channel, channel))
        if current_volume is None:
            raise RuntimeError(f"Could not find current Sonar volume for {channel}. Probe output needed.")
        return self.set_channel_volume(channel, current_volume + delta)

    def _find_nested_key(self, value, keys: tuple[str, ...]):
        if isinstance(value, dict):
            for key in keys:
                if key in value:
                    return value[key]
            # Prefer classic/monitoring branch when present so Streamer shapes are stable.
            preferred = ["classic", "monitoring", "stream", "streaming"]
            for key in preferred:
                if key in value:
                    found = self._find_nested_key(value[key], keys)
                    if found is not None:
                        return found
            for child in value.values():
                found = self._find_nested_key(child, keys)
                if found is not None:
                    return found
        elif isinstance(value, list):
            for child in value:
                found = self._find_nested_key(child, keys)
                if found is not None:
                    return found
        return None

    def _extract_channel_object(self, settings, channel_id: str):
        if isinstance(settings, dict):
            devices = settings.get("devices")
            if isinstance(devices, dict) and channel_id in devices:
                return devices[channel_id]
            for key, value in settings.items():
                if str(key).lower() == str(channel_id).lower():
                    return value
                found = self._extract_channel_object(value, channel_id)
                if found is not None:
                    return found
        elif isinstance(settings, list):
            for item in settings:
                if isinstance(item, dict) and str(item.get("channel") or item.get("id") or item.get("name", "")).lower() == str(channel_id).lower():
                    return item
                found = self._extract_channel_object(item, channel_id)
                if found is not None:
                    return found
        return None

    def _extract_volume(self, settings, channel_id: str) -> float | None:
        channel_obj = self._extract_channel_object(settings, channel_id)
        if channel_obj is None:
            return None
        found = self._find_nested_key(channel_obj, ("volume", "Volume", "level"))
        return float(found) if isinstance(found, (int, float)) else None

    def _extract_muted(self, settings, channel_id: str) -> bool | None:
        channel_obj = self._extract_channel_object(settings, channel_id)
        if channel_obj is None:
            return None
        found = self._find_nested_key(channel_obj, ("muted", "isMuted", "Mute"))
        return bool(found) if found is not None else None

    def volume_up(self, channel: str):
        return self.adjust_channel(channel, self.step)

    def volume_down(self, channel: str):
        return self.adjust_channel(channel, -self.step)

    def toggle_mute(self, channel: str):
        channel_id = self.channels.get(channel, channel)
        current = self.get_volume_settings()
        muted = self._extract_muted(current, channel_id)
        if muted is None:
            # Some Sonar builds return volume data without an obvious mute field.
            # If we always default to False, every press sends Mute=true and the
            # button can mute but never unmute. Keep a tiny bridge-side fallback
            # so repeated presses still alternate until a live probe teaches us
            # the exact shape for this GG version.
            muted = self._mute_cache.get(str(channel_id), False)
        return self.set_channel_mute(channel, not muted)

    def set_channel_mute(self, channel: str, muted: bool):
        channel_id = self.channels.get(channel, channel)
        mode = self.get_mode()
        target = "true" if muted else "false"
        paths = []
        if mode == "streamer":
            paths.extend([
                f"/volumeSettings/streamer/monitoring/{channel_id}/Mute/{target}",
                f"/volumeSettings/streamer/streaming/{channel_id}/Mute/{target}",
            ])
        paths.extend([
            f"/volumeSettings/{mode}/{channel_id}/Mute/{target}",
            f"/volumeSettings/{mode}/{channel_id}/muted/{target}",
            f"/volumeSettings/{mode}/{channel_id}/isMuted/{target}",
            f"/volumeSettings/classic/{channel_id}/Mute/{target}",
            f"/volumeSettings/classic/{channel_id}/muted/{target}",
            f"/volumeSettings/classic/{channel_id}/isMuted/{target}",
        ])
        last_error: Exception | None = None
        for path in dict.fromkeys(paths):
            try:
                result = self.request("PUT", path)
                self._mute_cache[str(channel_id)] = bool(muted)
                return result
            except Exception as exc:
                last_error = exc
                LOG.debug("Sonar mute endpoint failed for %s: %s", path, exc)
        raise RuntimeError(f"Could not set Sonar mute for {channel} ({channel_id}) to {target}: {last_error}")

    def rotate_output(self):
        # Placeholder until live probe confirms endpoint shape.
        raise NotImplementedError("Output rotation needs device selection config; Sonar API discovery works first.")

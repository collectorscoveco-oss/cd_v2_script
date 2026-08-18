from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterator

try:
    import serial
    import serial.tools.list_ports
except Exception:  # pragma: no cover - allows non-Windows/dev syntax tests without pyserial
    serial = None

LOG = logging.getLogger(__name__)
ARDUINO_KEYWORDS = ("arduino", "ch340", "ch341", "ftdi", "usb serial", "usb-serial")


@dataclass
class SerialSettings:
    port: str = "auto"
    baudrate: int = 9600
    reconnect_seconds: float = 2.0


def find_port() -> str | None:
    if serial is None:
        raise RuntimeError("pyserial is not installed. Run: pip install -r bridge/requirements.txt")
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        haystack = f"{port.description or ''} {port.manufacturer or ''}".lower()
        if any(keyword in haystack for keyword in ARDUINO_KEYWORDS):
            return port.device
    return ports[0].device if ports else None


def read_events(settings: SerialSettings) -> Iterator[str]:
    if serial is None:
        raise RuntimeError("pyserial is not installed. Run: pip install -r bridge/requirements.txt")
    port = find_port() if settings.port == "auto" else settings.port
    if not port:
        raise RuntimeError("No serial ports found. Plug in the Console Deck and retry.")
    LOG.info("Opening serial port %s at %s baud", port, settings.baudrate)
    with serial.Serial(port, settings.baudrate, timeout=1) as ser:
        while True:
            raw = ser.readline()
            if not raw:
                continue
            event = raw.decode("utf-8", errors="replace").strip()
            if event:
                yield event

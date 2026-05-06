"""
Arduino serial bridge: parses the $SENSORS stream from the Arduino Mega.

Output format from Arduino:
    $SENSORS,<lc_raw>,<lc_mv>,<enc_deg>,<enc_rev>,<enc_rpm>\r\n

Usage
-----
    bridge = ArduinoBridge('/dev/ttyUSB0', 115200)
    bridge.start()
    frame = bridge.get_frame()   # SensorFrame namedtuple
    bridge.stop()
"""

import serial
import threading
from dataclasses import dataclass
from typing import Optional


@dataclass
class SensorFrame:
    lc_raw:   int   = 0       # 24-bit signed ADC count
    lc_mv:    float = 0.0     # Differential voltage [mV]
    enc_deg:  float = 0.0     # Absolute angle [0.0, 359.9] degrees
    enc_rev:  float = 0.0     # Cumulative revolutions
    enc_rpm:  int   = 0       # RPM


class ArduinoBridge:
    """
    Background thread that continuously reads $SENSORS lines from the
    Arduino Mega over USB serial and stores the latest parsed frame.
    """

    HEADER = b'$SENSORS,'

    def __init__(self, port: str = '/dev/ttyUSB0', baud: int = 115200):
        self._ser = serial.Serial(
            port=port,
            baudrate=baud,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=2.0,
        )
        self._frame   = SensorFrame()
        self._lock    = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.parse_errors = 0

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        if self._ser.is_open:
            self._ser.close()

    def get_frame(self) -> SensorFrame:
        """Return a copy of the most recent sensor frame (thread-safe)."""
        with self._lock:
            return SensorFrame(
                lc_raw=self._frame.lc_raw,
                lc_mv=self._frame.lc_mv,
                enc_deg=self._frame.enc_deg,
                enc_rev=self._frame.enc_rev,
                enc_rpm=self._frame.enc_rpm,
            )

    # ------------------------------------------------------------------ #

    def _loop(self):
        while self._running:
            try:
                line = self._ser.readline()
                if not line:
                    continue
                frame = self._parse(line)
                if frame is not None:
                    with self._lock:
                        self._frame = frame
                elif line and not line.startswith(b'#'):
                    self.parse_errors += 1
            except serial.SerialException:
                break
            except Exception:
                self.parse_errors += 1

    @staticmethod
    def _parse(raw: bytes) -> Optional[SensorFrame]:
        """
        Parse one $SENSORS line.
        Returns None on any error.
        """
        try:
            text = raw.decode('ascii').strip()
            if not text.startswith('$SENSORS,'):
                return None
            parts = text[len('$SENSORS,'):].split(',')
            if len(parts) != 5:
                return None
            return SensorFrame(
                lc_raw=int(parts[0]),
                lc_mv=float(parts[1]),
                enc_deg=float(parts[2]),
                enc_rev=float(parts[3]),
                enc_rpm=int(parts[4]),
            )
        except (UnicodeDecodeError, ValueError, IndexError):
            return None

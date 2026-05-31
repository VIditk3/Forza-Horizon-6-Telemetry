from PyQt6.QtCore import QObject, pyqtSignal
import socket
import struct
import threading
import time
from typing import Optional

from TelemetryModels import TelemetryFrame


class TelemetryReceiver(QObject):
    telemetry_received = pyqtSignal(object)  # emits TelemetryFrame
    connection_state = pyqtSignal(bool)

    def __init__(self, host: str = "127.0.0.1", port: int = 1050, recv_buf: int = 8192):
        super().__init__()
        self.host = host
        self.port = port
        self.recv_buf = recv_buf
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.packet_count = 0

    def start(self):
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1.0)

    def _run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except Exception:
            pass
        try:
            sock.bind((self.host, self.port))
            self.connection_state.emit(True)
        except Exception:
            self.connection_state.emit(False)
            return
        sock.settimeout(1.0)

        while not self._stop_event.is_set():
            try:
                data, addr = sock.recvfrom(self.recv_buf)
            except socket.timeout:
                continue
            except Exception:
                break

            self.packet_count += 1
            t = TelemetryFrame()
            t.packet_count = self.packet_count
            t.timestamp_ms = int(time.time() * 1000)

            # Try to decode FH6 324-byte layout; safe fallbacks for missing fields
            try:
                if len(data) >= 324:
                    # offsets based on FH6 layout
                    t.is_race_on = struct.unpack_from("<i", data, 0)[0]
                    t.timestamp_ms = struct.unpack_from("<I", data, 4)[0]
                    t.engine_rpm = struct.unpack_from("<f", data, 16)[0]
                    t.speed_mps = struct.unpack_from("<f", data, 256)[0]
                    t.speed_kph = t.speed_mps * 3.6 if t.speed_mps is not None else None
                    t.power = struct.unpack_from("<f", data, 260)[0]
                    t.torque = struct.unpack_from("<f", data, 264)[0]
                    t.position_x = struct.unpack_from("<f", data, 244)[0]
                    t.position_y = struct.unpack_from("<f", data, 248)[0]
                    t.position_z = struct.unpack_from("<f", data, 252)[0]
                    t.velocity_x = struct.unpack_from("<f", data, 32)[0]
                    t.velocity_y = struct.unpack_from("<f", data, 36)[0]
                    t.velocity_z = struct.unpack_from("<f", data, 40)[0]
                    t.lap_number = struct.unpack_from("<H", data, 312)[0]
                    t.distance_traveled = struct.unpack_from("<f", data, 292)[0]
                    # controls
                    t.throttle = struct.unpack_from("<B", data, 315)[0] / 255.0
                    t.brake = struct.unpack_from("<B", data, 316)[0] / 255.0
                    raw_gear = struct.unpack_from("<B", data, 319)[0]
                    t.gear = int(raw_gear)
                    steer_raw = struct.unpack_from("<b", data, 320)[0]
                    t.steering = steer_raw / 127.0
                else:
                    # minimal legacy decode attempt
                    if len(data) >= 30:
                        t.engine_rpm = struct.unpack_from("<f", data, 22)[0]
                        t.speed_mps = struct.unpack_from("<f", data, 26)[0]
                        t.speed_kph = t.speed_mps * 3.6
            except struct.error:
                # ignore malformed packet
                pass

            self.telemetry_received.emit(t)

        try:
            sock.close()
        except Exception:
            pass

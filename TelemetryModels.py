from dataclasses import dataclass
from typing import Optional


@dataclass
class TelemetryFrame:
    timestamp_ms: Optional[int] = None
    packet_count: int = 0

    speed_mps: Optional[float] = None
    speed_kph: Optional[float] = None
    engine_rpm: Optional[float] = None
    gear: Optional[int] = None
    throttle: Optional[float] = None
    brake: Optional[float] = None
    steering: Optional[float] = None
    power: Optional[float] = None
    torque: Optional[float] = None

    position_x: Optional[float] = None
    position_y: Optional[float] = None
    position_z: Optional[float] = None

    velocity_x: Optional[float] = None
    velocity_y: Optional[float] = None
    velocity_z: Optional[float] = None

    lap_number: Optional[int] = None
    distance_traveled: Optional[float] = None


@dataclass
class SystemMetrics:
    timestamp: float = 0.0
    cpu_percent: Optional[float] = None
    ram_percent: Optional[float] = None
    cpu_temp: Optional[float] = None
    cpu_freq: Optional[float] = None
    gpu_percent: Optional[float] = None
    gpu_temp: Optional[float] = None
    vram_used: Optional[float] = None
    vram_total: Optional[float] = None

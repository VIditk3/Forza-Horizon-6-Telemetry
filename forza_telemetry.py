"""Forza Horizon 6 Data Out UDP listener and decoder.

This script listens on a UDP port and decodes the exact Forza Horizon 6 Data Out
packet format (324 bytes) when available. It also keeps a legacy fallback for
older Forza UDP packet layouts.

Exact packet layout used here:
- Offset 0 (S32): IsRaceOn
- Offset 4 (U32): TimestampMS
- Offset 8 (F32): EngineMaxRpm
- Offset 12 (F32): EngineIdleRpm
- Offset 16 (F32): CurrentEngineRpm
- Offset 20 (F32 x 3): AccelerationX/Y/Z (local space)
- Offset 32 (F32 x 3): VelocityX/Y/Z (local space)
- Offset 44 (F32 x 3): AngularVelocityX/Y/Z (rad/s)
- Offset 56 (F32 x 3): Yaw/Pitch/Roll (radians)
- Offset 68 (F32 x 4): NormalizedSuspensionTravelFrontLeft/FrontRight/RearLeft/RearRight
- Offset 84 (F32 x 4): TireSlipRatioFrontLeft/FrontRight/RearLeft/RearRight
- Offset 100 (F32 x 4): WheelRotationSpeedFrontLeft/FrontRight/RearLeft/RearRight
- Offset 116 (S32 x 4): WheelOnRumbleStripFrontLeft/FrontRight/RearLeft/RearRight
- Offset 132 (S32 x 4): WheelInPuddleFrontLeft/FrontRight/RearLeft/RearRight
- Offset 148 (F32 x 4): SurfaceRumbleFrontLeft/FrontRight/RearLeft/RearRight
- Offset 164 (F32 x 4): TireSlipAngleFrontLeft/FrontRight/RearLeft/RearRight
- Offset 180 (F32 x 4): TireCombinedSlipFrontLeft/FrontRight/RearLeft/RearRight
- Offset 196 (F32 x 4): SuspensionTravelMetersFrontLeft/FrontRight/RearLeft/RearRight
- Offset 212 (S32): CarOrdinal
- Offset 216 (S32): CarClass
- Offset 220 (S32): CarPerformanceIndex
- Offset 224 (S32): DrivetrainType
- Offset 228 (S32): NumCylinders
- Offset 232 (U32): CarGroup
- Offset 236 (F32): SmashableVelDiff
- Offset 240 (F32): SmashableMass
- Offset 244 (F32 x 3): PositionX/Y/Z (world space)
- Offset 256 (F32): Speed (m/s)
- Offset 260 (F32): Power (watts)
- Offset 264 (F32): Torque (Nm)
- Offset 268 (F32 x 4): TireTempFrontLeft/FrontRight/RearLeft/RearRight
- Offset 284 (F32): Boost
- Offset 288 (F32): Fuel
- Offset 292 (F32): DistanceTraveled
- Offset 296 (F32): BestLap
- Offset 300 (F32): LastLap
- Offset 304 (F32): CurrentLap
- Offset 308 (F32): CurrentRaceTime
- Offset 312 (U16): LapNumber
- Offset 314 (U8): RacePosition
- Offset 315 (U8): Accel
- Offset 316 (U8): Brake
- Offset 317 (U8): Clutch
- Offset 318 (U8): HandBrake
- Offset 319 (U8): Gear
- Offset 320 (S8): Steer
- Offset 321 (S8): NormalizedDrivingLine
- Offset 322 (S8): NormalizedAIBrakeDifference

Why these offsets were chosen:
- They come directly from the official Forza Horizon 6 Data Out documentation.
- The format is fixed and 324 bytes long, so the decoder can map every field precisely.
- FH6 uses native types like S32/U32/F32/U8/S8 in a stable order, which is ideal for struct decoding.
- Legacy packet decoding is preserved only as fallback for older non-FH6 packet sizes.
"""

from __future__ import annotations

import argparse
import csv
import logging
import socket
import struct
import sys
import threading
import time
from collections import deque
from dataclasses import dataclass, field, fields
from typing import Any, Dict, List, Optional

try:
    import matplotlib.animation as animation
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


SUPPORTED_PACKET_SIZES = {
    324: "ForzaTelemetry-FH6",  # Exact Forza Horizon 6 Data Out packet size.
    1444: "ForzaTelemetry-1444",  # Legacy Forza Data Out packet size.
    1476: "ForzaTelemetry-1476",  # Extended or later Forza packet layout.
}

MINIMUM_KNOWN_SIZE = 160  # Allow a fallback decode for legacy packet formats when needed.


class PacketDecodeError(Exception):
    """Raised when a packet cannot be decoded."""


@dataclass
class ForzaTelemetry:
    packet_format: Optional[int] = None
    game_major_version: Optional[int] = None
    game_minor_version: Optional[int] = None
    packet_version: Optional[int] = None
    packet_id: Optional[int] = None

    # FH6 Data Out fields
    is_race_on: Optional[int] = None
    timestamp_ms: Optional[int] = None
    engine_max_rpm: Optional[float] = None
    engine_idle_rpm: Optional[float] = None
    engine_rpm: Optional[float] = None
    acceleration_x: Optional[float] = None
    acceleration_y: Optional[float] = None
    acceleration_z: Optional[float] = None
    velocity_x: Optional[float] = None
    velocity_y: Optional[float] = None
    velocity_z: Optional[float] = None
    angular_velocity_x: Optional[float] = None
    angular_velocity_y: Optional[float] = None
    angular_velocity_z: Optional[float] = None
    yaw: Optional[float] = None
    pitch: Optional[float] = None
    roll: Optional[float] = None
    normalized_suspension_travel: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    tire_slip: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    tire_slip_ratio: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    wheel_rotation_speed: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    tire_temperature: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    wheel_on_rumble_strip: List[int] = field(default_factory=lambda: [0, 0, 0, 0])
    wheel_in_puddle: List[int] = field(default_factory=lambda: [0, 0, 0, 0])
    surface_rumble: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    tire_slip_angle: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    tire_combined_slip: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    suspension_travel: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    car_ordinal: Optional[int] = None
    car_class: Optional[int] = None
    car_performance_index: Optional[int] = None
    drivetrain_type: Optional[int] = None
    num_cylinders: Optional[int] = None
    car_group: Optional[int] = None
    smashable_vel_diff: Optional[float] = None
    smashable_mass: Optional[float] = None
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    position_z: Optional[float] = None
    speed_mps: Optional[float] = None
    speed_kph: Optional[float] = None
    power: Optional[float] = None
    torque: Optional[float] = None
    boost: Optional[float] = None
    fuel: Optional[float] = None
    distance_traveled: Optional[float] = None
    best_lap: Optional[float] = None
    last_lap: Optional[float] = None
    current_lap: Optional[float] = None
    current_race_time: Optional[float] = None
    lap_number: Optional[int] = None
    race_position: Optional[int] = None
    accel_input: Optional[int] = None
    brake_input: Optional[int] = None
    clutch_input: Optional[int] = None
    handbrake_input: Optional[int] = None
    gear: Optional[int] = None
    steer_input: Optional[int] = None
    steering: Optional[float] = None
    normalized_driving_line: Optional[int] = None
    normalized_ai_brake_difference: Optional[int] = None
    raw_length: int = 0
    format_name: str = "unknown"
    unsupported_packet: Optional[str] = None


def _unpack_float_array(data: bytes, offset: int, count: int) -> List[float]:
    format_string = "<" + "f" * count
    return list(struct.unpack_from(format_string, data, offset))


def hexdump(data: bytes, length: int = 64) -> str:
    """Return a simple hex dump (space-separated) of the first `length` bytes."""
    display = data[:length]
    hex_pairs = " ".join(f"{b:02X}" for b in display)
    return hex_pairs


def guess_offsets(data: bytes) -> Dict[str, List[int]]:
    """Heuristically search the packet for likely offsets for RPM, speed (m/s), and gear.

    Returns a dict of lists of candidate offsets for each field.
    """
    candidates: Dict[str, List[int]] = {"rpm": [], "speed": [], "gear": []}
    L = len(data)

    # Search for float candidates (4 bytes)
    for off in range(0, max(0, L - 4)):
        try:
            val = struct.unpack_from("<f", data, off)[0]
        except struct.error:
            continue
        # RPM: plausible 0..20000
        if 0.0 <= val <= 20000.0:
            candidates["rpm"].append(off)
        # Speed (m/s): plausible 0..120 (0..432 km/h)
        if 0.0 <= val <= 120.0:
            candidates["speed"].append(off)

    # Search for gear as signed int8 (-1..10)
    for off in range(0, L):
        try:
            g = struct.unpack_from("<b", data, off)[0]
        except struct.error:
            continue
        if -1 <= g <= 10:
            candidates["gear"].append(off)

    # Reduce candidates by uniqueness and return
    for k in candidates:
        # keep unique and sorted
        candidates[k] = sorted(set(candidates[k]))[:10]
    return candidates


def decode_packet(data: bytes) -> ForzaTelemetry:
    """Decode a raw UDP packet into a ForzaTelemetry dataclass."""
    raw_length = len(data)
    format_name = SUPPORTED_PACKET_SIZES.get(raw_length, "ForzaTelemetry-unknown")
    telemetry = ForzaTelemetry(raw_length=raw_length, format_name=format_name)

    if raw_length < MINIMUM_KNOWN_SIZE:
        telemetry.unsupported_packet = (
            f"Packet too short for known Forza telemetry layouts: {raw_length} bytes"
        )
        raise PacketDecodeError(telemetry.unsupported_packet)

    try:
        if raw_length == 324:
            telemetry.format_name = SUPPORTED_PACKET_SIZES[raw_length]
            telemetry.is_race_on = struct.unpack_from("<i", data, 0)[0]
            telemetry.timestamp_ms = struct.unpack_from("<I", data, 4)[0]
            telemetry.engine_max_rpm = struct.unpack_from("<f", data, 8)[0]
            telemetry.engine_idle_rpm = struct.unpack_from("<f", data, 12)[0]
            telemetry.engine_rpm = struct.unpack_from("<f", data, 16)[0]

            telemetry.acceleration_x = struct.unpack_from("<f", data, 20)[0]
            telemetry.acceleration_y = struct.unpack_from("<f", data, 24)[0]
            telemetry.acceleration_z = struct.unpack_from("<f", data, 28)[0]
            telemetry.velocity_x = struct.unpack_from("<f", data, 32)[0]
            telemetry.velocity_y = struct.unpack_from("<f", data, 36)[0]
            telemetry.velocity_z = struct.unpack_from("<f", data, 40)[0]
            telemetry.angular_velocity_x = struct.unpack_from("<f", data, 44)[0]
            telemetry.angular_velocity_y = struct.unpack_from("<f", data, 48)[0]
            telemetry.angular_velocity_z = struct.unpack_from("<f", data, 52)[0]
            telemetry.yaw = struct.unpack_from("<f", data, 56)[0]
            telemetry.pitch = struct.unpack_from("<f", data, 60)[0]
            telemetry.roll = struct.unpack_from("<f", data, 64)[0]

            telemetry.normalized_suspension_travel = _unpack_float_array(data, 68, 4)
            telemetry.tire_slip_ratio = _unpack_float_array(data, 84, 4)
            telemetry.wheel_rotation_speed = _unpack_float_array(data, 100, 4)
            telemetry.wheel_on_rumble_strip = list(struct.unpack_from("<iiii", data, 116))
            telemetry.wheel_in_puddle = list(struct.unpack_from("<iiii", data, 132))
            telemetry.surface_rumble = _unpack_float_array(data, 148, 4)
            telemetry.tire_slip_angle = _unpack_float_array(data, 164, 4)
            telemetry.tire_combined_slip = _unpack_float_array(data, 180, 4)
            telemetry.suspension_travel = _unpack_float_array(data, 196, 4)

            telemetry.car_ordinal = struct.unpack_from("<i", data, 212)[0]
            telemetry.car_class = struct.unpack_from("<i", data, 216)[0]
            telemetry.car_performance_index = struct.unpack_from("<i", data, 220)[0]
            telemetry.drivetrain_type = struct.unpack_from("<i", data, 224)[0]
            telemetry.num_cylinders = struct.unpack_from("<i", data, 228)[0]
            telemetry.car_group = struct.unpack_from("<I", data, 232)[0]
            telemetry.smashable_vel_diff = struct.unpack_from("<f", data, 236)[0]
            telemetry.smashable_mass = struct.unpack_from("<f", data, 240)[0]

            telemetry.position_x = struct.unpack_from("<f", data, 244)[0]
            telemetry.position_y = struct.unpack_from("<f", data, 248)[0]
            telemetry.position_z = struct.unpack_from("<f", data, 252)[0]
            telemetry.speed_mps = struct.unpack_from("<f", data, 256)[0]
            telemetry.speed_kph = telemetry.speed_mps * 3.6
            telemetry.power = struct.unpack_from("<f", data, 260)[0]
            telemetry.torque = struct.unpack_from("<f", data, 264)[0]
            telemetry.tire_temperature = _unpack_float_array(data, 268, 4)
            telemetry.boost = struct.unpack_from("<f", data, 284)[0]
            telemetry.fuel = struct.unpack_from("<f", data, 288)[0]
            telemetry.distance_traveled = struct.unpack_from("<f", data, 292)[0]
            telemetry.best_lap = struct.unpack_from("<f", data, 296)[0]
            telemetry.last_lap = struct.unpack_from("<f", data, 300)[0]
            telemetry.current_lap = struct.unpack_from("<f", data, 304)[0]
            telemetry.current_race_time = struct.unpack_from("<f", data, 308)[0]
            telemetry.lap_number = struct.unpack_from("<H", data, 312)[0]
            telemetry.race_position = struct.unpack_from("<B", data, 314)[0]
            telemetry.accel_input = struct.unpack_from("<B", data, 315)[0]
            telemetry.brake_input = struct.unpack_from("<B", data, 316)[0]
            telemetry.clutch_input = struct.unpack_from("<B", data, 317)[0]
            telemetry.handbrake_input = struct.unpack_from("<B", data, 318)[0]
            telemetry.gear = struct.unpack_from("<B", data, 319)[0]
            telemetry.steer_input = struct.unpack_from("<b", data, 320)[0]
            telemetry.steering = telemetry.steer_input / 127.0 if telemetry.steer_input is not None else None
            telemetry.normalized_driving_line = struct.unpack_from("<b", data, 321)[0]
            telemetry.normalized_ai_brake_difference = struct.unpack_from("<b", data, 322)[0]
        else:
            # Preserve older decode behavior for legacy packet lengths
            telemetry.packet_format, telemetry.game_major_version, telemetry.game_minor_version,
            telemetry.packet_version, telemetry.packet_id = struct.unpack_from("<HBBBB", data, 0)

            telemetry.session_time = struct.unpack_from("<f", data, 6)[0]
            telemetry.frame_identifier = struct.unpack_from("<I", data, 10)[0]
            telemetry.player_car_index, telemetry.viewed_player_index,
            telemetry.num_cars, telemetry.num_players = struct.unpack_from("<BBBB", data, 14)
            telemetry.car_class = struct.unpack_from("<B", data, 18)[0]
            telemetry.car_performance_index = struct.unpack_from("<B", data, 19)[0]
            telemetry.drivetrain_type = struct.unpack_from("<B", data, 20)[0]
            telemetry.gear = struct.unpack_from("<b", data, 21)[0]
            telemetry.engine_rpm = struct.unpack_from("<f", data, 22)[0]
            telemetry.speed_mps = struct.unpack_from("<f", data, 26)[0]
            telemetry.speed_kph = telemetry.speed_mps * 3.6 if telemetry.speed_mps is not None else None
            telemetry.throttle = struct.unpack_from("<f", data, 30)[0]
            telemetry.brake = struct.unpack_from("<f", data, 34)[0]
            telemetry.steering = struct.unpack_from("<f", data, 38)[0]
            telemetry.clutch = struct.unpack_from("<f", data, 42)[0]
            telemetry.power = struct.unpack_from("<f", data, 46)[0]
            telemetry.torque = struct.unpack_from("<f", data, 50)[0]
            telemetry.position_x, telemetry.position_y, telemetry.position_z = struct.unpack_from("<fff", data, 54)
            telemetry.velocity_x, telemetry.velocity_y, telemetry.velocity_z = struct.unpack_from("<fff", data, 66)
            telemetry.acceleration_x, telemetry.acceleration_y, telemetry.acceleration_z = struct.unpack_from("<fff", data, 78)
            telemetry.tire_slip = _unpack_float_array(data, 90, 4)
            telemetry.tire_temperature = _unpack_float_array(data, 106, 4)
            telemetry.suspension_travel = _unpack_float_array(data, 122, 4)
            telemetry.wheel_rotation_speed = _unpack_float_array(data, 138, 4)
            telemetry.lap_number = struct.unpack_from("<B", data, 154)[0]
            telemetry.race_position = struct.unpack_from("<B", data, 155)[0]
            telemetry.distance_traveled = struct.unpack_from("<f", data, 156)[0]
            telemetry.format_name = SUPPORTED_PACKET_SIZES.get(raw_length, f"ForzaTelemetry-unknown-{raw_length}")

    except struct.error as exc:
        telemetry.unsupported_packet = f"Malformed packet: {exc}"
        raise PacketDecodeError(telemetry.unsupported_packet) from exc

    return telemetry


def format_telemetry_table(telemetry: ForzaTelemetry) -> str:
    """Render telemetry fields in a readable, aligned table."""
    rows = []
    for field in fields(telemetry):
        value = getattr(telemetry, field.name)
        rows.append((field.name, value))

    name_width = max(len(name) for name, _ in rows)
    lines = [f"{name:<{name_width}} : {value}" for name, value in rows]
    return "\n".join(lines)


def write_csv_row(writer: csv.DictWriter, telemetry: ForzaTelemetry) -> None:
    """Write one telemetry row to CSV."""
    row: Dict[str, Any] = {
        "timestamp": time.time(),
        "packet_length": telemetry.raw_length,
        "format_name": telemetry.format_name,
        "packet_format": telemetry.packet_format,
        "game_version": f"{telemetry.game_major_version}.{telemetry.game_minor_version}",
        "packet_version": telemetry.packet_version,
        "packet_id": telemetry.packet_id,
        "session_time": telemetry.session_time,
        "frame_identifier": telemetry.frame_identifier,
        "player_car_index": telemetry.player_car_index,
        "viewed_player_index": telemetry.viewed_player_index,
        "num_cars": telemetry.num_cars,
        "num_players": telemetry.num_players,
        "car_class": telemetry.car_class,
        "car_performance_index": telemetry.car_performance_index,
        "drivetrain_type": telemetry.drivetrain_type,
        "gear": telemetry.gear,
        "engine_rpm": telemetry.engine_rpm,
        "speed_mps": telemetry.speed_mps,
        "speed_kph": telemetry.speed_kph,
        "throttle": telemetry.throttle,
        "brake": telemetry.brake,
        "steering": telemetry.steering,
        "clutch": telemetry.clutch,
        "power": telemetry.power,
        "torque": telemetry.torque,
        "position_x": telemetry.position_x,
        "position_y": telemetry.position_y,
        "position_z": telemetry.position_z,
        "velocity_x": telemetry.velocity_x,
        "velocity_y": telemetry.velocity_y,
        "velocity_z": telemetry.velocity_z,
        "acceleration_x": telemetry.acceleration_x,
        "acceleration_y": telemetry.acceleration_y,
        "acceleration_z": telemetry.acceleration_z,
        "lap_number": telemetry.lap_number,
        "race_position": telemetry.race_position,
        "distance_traveled": telemetry.distance_traveled,
    }
    for i in range(4):
        row[f"tire_slip_{i+1}"] = telemetry.tire_slip[i] if telemetry.tire_slip else None
        row[f"tire_temp_{i+1}"] = telemetry.tire_temperature[i] if telemetry.tire_temperature else None
        row[f"suspension_travel_{i+1}"] = telemetry.suspension_travel[i] if telemetry.suspension_travel else None
        row[f"wheel_rotation_speed_{i+1}"] = telemetry.wheel_rotation_speed[i] if telemetry.wheel_rotation_speed else None
    writer.writerow(row)


def create_csv_writer(csv_file_path: str) -> csv.DictWriter:
    """Create a CSV writer and write the header row."""
    fieldnames = [
        "timestamp",
        "packet_length",
        "format_name",
        "packet_format",
        "game_version",
        "packet_version",
        "packet_id",
        "session_time",
        "frame_identifier",
        "player_car_index",
        "viewed_player_index",
        "num_cars",
        "num_players",
        "car_class",
        "car_performance_index",
        "drivetrain_type",
        "gear",
        "engine_rpm",
        "speed_mps",
        "speed_kph",
        "throttle",
        "brake",
        "steering",
        "clutch",
        "power",
        "torque",
        "position_x",
        "position_y",
        "position_z",
        "velocity_x",
        "velocity_y",
        "velocity_z",
        "acceleration_x",
        "acceleration_y",
        "acceleration_z",
        "lap_number",
        "race_position",
        "distance_traveled",
    ]
    for i in range(4):
        fieldnames.extend(
            [
                f"tire_slip_{i+1}",
                f"tire_temp_{i+1}",
                f"suspension_travel_{i+1}",
                f"wheel_rotation_speed_{i+1}",
            ]
        )

    csv_file = open(csv_file_path, mode="w", newline="", encoding="utf-8")
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()
    return writer


def run_udp_listener(
    host: str,
    port: int,
    csv_path: Optional[str] = None,
    enable_dashboard: bool = False,
    enable_live: bool = False,
) -> None:
    """Listen for Forza telemetry UDP packets and decode them continuously."""
    logging.info("Starting UDP listener on %s:%s", host, port)
    print(f"Listening for telemetry on udp://{host}:{port} ...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Allow reuse of address/port — helpful when restarting the listener quickly
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except Exception:
        logging.debug("SO_REUSEADDR not available on this platform")
    # Bind explicitly to the given host/port (verify binding success below)
    sock.bind((host, port))
    sock.settimeout(1.0)

    # Report actual bound address (useful if host='0.0.0.0' or port 0 requested)
    try:
        bound = sock.getsockname()
        print(f"Socket bound to: {bound[0]}:{bound[1]}")
        logging.info("Socket bound to: %s", bound)
    except Exception:
        logging.exception("Failed to query socket name after bind")

    csv_writer: Optional[csv.DictWriter] = None
    csv_file = None
    if csv_path:
        csv_writer = create_csv_writer(csv_path)
        csv_file = csv_writer.writerows  # type: ignore
        logging.info("CSV logging enabled: %s", csv_path)

    history = deque(maxlen=200)
    latest: Dict[str, Any] = {"telemetry": None}
    last_csv_write = 0.0
    packet_count = 0
    hex_dump_samples = 8

    def udp_receiver() -> None:
        nonlocal last_csv_write
        nonlocal packet_count
        while True:
            try:
                print("Waiting for packet...")
                data, addr = sock.recvfrom(8192)
                packet_count += 1
                receive_line = f"Packet #{packet_count} received: {len(data)} bytes from {addr[0]}:{addr[1]}"
                print(receive_line)
                logging.debug("Received %d bytes from %s (count=%d)", len(data), addr, packet_count)

                # Print raw hex for the first few packets to help verify structure
                if packet_count <= hex_dump_samples:
                    hexd = hexdump(data, 128)
                    print(f"Packet #{packet_count} hex (first 128 bytes):\n{hexd}")
                    logging.debug("Packet #%d hex: %s", packet_count, hexd)
                try:
                    try:
                        telemetry = decode_packet(data)
                    except PacketDecodeError as pexc:
                        print(f"Packet #{packet_count} decode error: {pexc}")
                        logging.warning("Decode failed for packet %d: %s", packet_count, pexc)
                        # continue loop after logging; preserve raw packet for inspection
                        continue
                    latest["telemetry"] = telemetry
                    history.append(telemetry)

                    # If the packet size is not a known supported format, print a concise hexdump
                    if telemetry.format_name.startswith("ForzaTelemetry-unknown"):
                        dump = hexdump(data, 64)
                        logging.info(
                            "Unknown packet size %d; hexdump (first 64 bytes): %s",
                            telemetry.raw_length,
                            dump,
                        )
                        print("\nHexdump (first 64 bytes):")
                        print(dump)
                        # Run heuristic to suggest likely offsets for RPM/speed/gear
                        try:
                            suggestions = guess_offsets(data)
                            logging.info("Heuristic suggestions: %s", suggestions)
                            print("Heuristic candidate offsets:")
                            print(suggestions)
                        except Exception:
                            logging.exception("Heuristic scanning failed")
                    # Print a full dump of decoded fields for the first few packets
                    if packet_count <= hex_dump_samples:
                        print("Decoded telemetry fields:")
                        print(format_telemetry_table(telemetry))
                        if telemetry.speed_kph is not None:
                            print(f"Speed: {telemetry.speed_kph:.1f} km/h")

                    if csv_writer is not None:
                        now = time.monotonic()
                        if now - last_csv_write >= 0.1:
                            write_csv_row(csv_writer, telemetry)
                            last_csv_write = now
                    # If live mode is disabled, print the full table for debugging
                    if not enable_live:
                        table = "\n" + format_telemetry_table(telemetry)
                        print(table)

                    # Live console summary: always update the single-line view when enabled
                    if enable_live:
                        try:
                            speed = telemetry.speed_kph or 0.0
                            gear = telemetry.gear if telemetry.gear is not None else 0
                            print(f"Live => Speed: {speed:6.1f} km/h | Gear: {gear:>2}")
                        except Exception:
                            pass
                except PacketDecodeError as exc:
                    logging.warning("Could not decode packet (%d bytes): %s", len(data), exc)
            except socket.timeout:
                continue
            except KeyboardInterrupt:
                logging.info("Listener stopped by user.")
                break
            except Exception as exc:
                logging.exception("Unexpected error while receiving telemetry: %s", exc)
                break

    receiver_thread = threading.Thread(target=udp_receiver, daemon=True)
    receiver_thread.start()

    if enable_dashboard:
        if not MATPLOTLIB_AVAILABLE:
            logging.error("matplotlib is not installed; dashboard cannot be started.")
        else:
            run_dashboard(latest)

    try:
        while receiver_thread.is_alive():
            receiver_thread.join(timeout=0.5)
    except KeyboardInterrupt:
        logging.info("Shutting down listener.")
    finally:
        sock.close()


def run_dashboard(latest: Dict[str, Any]) -> None:
    """Display a real-time matplotlib dashboard for RPM, speed, throttle, and brake."""
    logging.info("Starting matplotlib dashboard.")
    window_seconds = 10
    sample_rate = 0.1
    sample_count = int(window_seconds / sample_rate)

    rpm_values = deque(maxlen=sample_count)
    speed_values = deque(maxlen=sample_count)
    throttle_values = deque(maxlen=sample_count)
    brake_values = deque(maxlen=sample_count)
    timestamps = deque(maxlen=sample_count)

    fig, axes = plt.subplots(4, 1, figsize=(10, 8), sharex=True)
    (rpm_line,) = axes[0].plot([], [], label="RPM", color="tab:red")
    (speed_line,) = axes[1].plot([], [], label="Speed (km/h)", color="tab:blue")
    (throttle_line,) = axes[2].plot([], [], label="Throttle", color="tab:green")
    (brake_line,) = axes[3].plot([], [], label="Brake", color="tab:orange")

    axes[0].set_ylabel("RPM")
    axes[1].set_ylabel("km/h")
    axes[2].set_ylabel("Throttle")
    axes[3].set_ylabel("Brake")
    axes[3].set_xlabel("Time (s)")

    for ax in axes:
        ax.grid(True)
        ax.legend(loc="upper left")

    def animate(_: int) -> None:
        telemetry = latest.get("telemetry")
        if telemetry is None:
            return

        now = time.time()
        timestamps.append(now)
        rpm_values.append(telemetry.engine_rpm or 0.0)
        speed_values.append(telemetry.speed_kph or 0.0)
        throttle_values.append((telemetry.throttle or 0.0) * 100.0)
        brake_values.append((telemetry.brake or 0.0) * 100.0)

        relative_times = [t - timestamps[0] for t in timestamps]
        rpm_line.set_data(relative_times, list(rpm_values))
        speed_line.set_data(relative_times, list(speed_values))
        throttle_line.set_data(relative_times, list(throttle_values))
        brake_line.set_data(relative_times, list(brake_values))

        for ax, values in zip(axes, [rpm_values, speed_values, throttle_values, brake_values]):
            ax.relim()
            ax.autoscale_view()

        axes[-1].set_xlim(0, max(10.0, relative_times[-1] if relative_times else 10.0))

    ani = animation.FuncAnimation(fig, animate, interval=int(sample_rate * 1000))
    plt.tight_layout()
    plt.show()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Forza Horizon UDP telemetry listener and decoder.")
    parser.add_argument("--host", default="127.0.0.1", help="UDP host to bind to")
    parser.add_argument("--port", type=int, default=1050, help="UDP port to listen on")
    parser.add_argument("--csv", help="Optional CSV path for logging telemetry at up to 10 Hz")
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Enable optional real-time matplotlib dashboard for RPM, speed, throttle, and brake",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Show a concise live console line with speed and gear (suppresses full table)",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    try:
        run_udp_listener(args.host, args.port, args.csv, args.dashboard, args.live)
    except Exception as exc:
        logging.exception("Fatal error in listener: %s", exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

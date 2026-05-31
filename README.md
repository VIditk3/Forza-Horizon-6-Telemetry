# ForzaTelemetry

Python listener and decoder for Forza Horizon 6 Data Out telemetry.

## Overview

This repository contains:

- `forza_telemetry.py` - a UDP telemetry listener, decoder, live console output, and optional CSV logging.
- `TelemetryReceiver.py` - threaded UDP receiver that emits decoded telemetry frames.
- `SystemMonitor.py` - threaded system telemetry collector using `psutil` and optional NVIDIA NVML.
- `DashboardWindow.py` - a PyQt6 dashboard with live gauges, plots, and status panels.
- `PlotWidgets.py` - reusable pyqtgraph plot widgets.
- `TelemetryModels.py` - typed dataclasses for telemetry and system data.
- `main.py` - application entry point for the dashboard.
- `udp_port_1050_receiver.py` - minimal UDP test receiver.
- `kill_port.py` - helper to locate and optionally kill the process using a UDP port.

## Requirements

- Python 3.11+
- Windows is preferred for this workspace but the dashboard code is cross-platform.
- `PyQt6`, `pyqtgraph`, `psutil`, `pynvml`, and `numpy`

## Setup

```powershell
cd C:\Users\vidit\Documents\Projects\ForzaTelemetry
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Configure Forza Horizon 6 Data Out

In Forza Horizon 6, set the telemetry output to your local machine:

1. Open `Settings`.
2. Go to `HUD & Gameplay`.
3. Open `Telemetry`.
4. Set `Data Out` to `On`.
5. Set `Data Out IP Address` to `127.0.0.1`.
6. Set `Data Out IP Port` to `1050`.

> If you change the port in-game, update the corresponding port in `forza_telemetry.py`, `main.py`, or use `--port` when launching.

## Running the console listener

```powershell
python forza_telemetry.py --host 127.0.0.1 --port 1050 --live
```

Available options:

- `--debug` - enable verbose logging.
- `--csv telemetry.csv` - save telemetry data to CSV.
- `--dashboard` - enable the optional matplotlib dashboard in `forza_telemetry.py`.
- `--live` - show live speed/gear output in the terminal.

## Running the dashboard

```powershell
python main.py
```

The dashboard uses the default telemetry bind address and port `127.0.0.1:1050`. If your game uses a different port, edit the `TelemetryReceiver(...)` instantiation in `main.py`.

## Testing UDP reception

If you need to confirm that UDP packets are being received on port 1050, run:

```powershell
python udp_port_1050_receiver.py
```

If the port is already in use, identify and free it with:

```powershell
python kill_port.py --port 1050
```



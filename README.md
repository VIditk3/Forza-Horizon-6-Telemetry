# ForzaTelemetry

Python listener and decoder for Forza Horizon 6 Data Out telemetry.

## Files

- `forza_telemetry.py` - UDP listener, decoder, CSV logging, and optional matplotlib dashboard.
- `requirements.txt` - Python dependencies for optional dashboard support.

## Setup

```powershell
cd C:\Users\vidit\Documents\Projects\ForzaTelemetry
. .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

```powershell
python forza_telemetry.py --host 127.0.0.1 --port 1050 --live
```

Use `--debug` for more logging, and `--csv telemetry.csv` to save telemetry.

## Notes

- Forza Horizon 6 Data Out uses a fixed 324-byte packet format.
- Avoid ports 5200-5300 for receiving, since the game binds those outgoing sockets.

## Dashboard

This workspace now includes a PyQt6 real-time telemetry dashboard prototype.

Run the dashboard after installing dependencies:

```powershell
python -m venv .venv
. \.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

The dashboard is a work-in-progress and demonstrates a responsive GUI, live plots
and system monitoring. See the source files for extension points.

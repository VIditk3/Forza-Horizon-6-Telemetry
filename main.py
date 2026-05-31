import sys
from PyQt6.QtWidgets import QApplication
from DashboardWindow import DashboardWindow
from TelemetryReceiver import TelemetryReceiver
from SystemMonitor import SystemMonitor


def main(argv):
    app = QApplication(argv)
    win = DashboardWindow()

    # telemetry receiver
    receiver = TelemetryReceiver(host="127.0.0.1", port=1050)
    receiver.telemetry_received.connect(win.update_telemetry)
    receiver.connection_state.connect(lambda ok: print("Telemetry socket OK" if ok else "Telemetry socket failed"))
    receiver.start()

    # system monitor
    monitor = SystemMonitor()
    monitor.system_update.connect(win.update_system)
    monitor.start()

    win.show()
    try:
        return app.exec()
    finally:
        receiver.stop()
        monitor.stop()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGridLayout,
    QApplication,
    QProgressBar,
    QFrame,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor
import pyqtgraph as pg

from TelemetryModels import TelemetryFrame, SystemMetrics
from PlotWidgets import TimeSeriesPlot

from collections import deque
import time


class DashboardWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Forza Telemetry Dashboard")
        self.setMinimumSize(1280, 800)
        self._init_style()
        self._init_ui()
        self.telemetry_history = deque(maxlen=1200)
        self.system_history = deque(maxlen=1200)

        # update plots at ~15 FPS
        self.plot_timer = QTimer()
        self.plot_timer.timeout.connect(self._refresh_plots)
        self.plot_timer.start(66)

        # packet rate smoothing
        self._last_packet_count = 0
        self._last_packet_time = time.time()

    def _init_style(self):
        # Dark motorsport-inspired palette
        pal = QPalette()
        pal.setColor(QPalette.ColorRole.Window, QColor(10, 10, 10))
        pal.setColor(QPalette.ColorRole.WindowText, QColor(200, 200, 200))
        pal.setColor(QPalette.ColorRole.Base, QColor(18, 18, 18))
        pal.setColor(QPalette.ColorRole.AlternateBase, QColor(24, 24, 24))
        pal.setColor(QPalette.ColorRole.Text, QColor(230, 230, 230))
        self.setPalette(pal)

    def _init_ui(self):
        font_digital = QFont("DS-Digital", 36)
        font_large = QFont("Sans Serif", 28, QFont.Weight.Bold)
        font_med = QFont("Sans Serif", 12)

        main = QVBoxLayout()

        # Top readouts
        top = QHBoxLayout()
        readouts = QHBoxLayout()
        self.lbl_speed = QLabel("0.0")
        self.lbl_speed.setFont(font_digital)
        self.lbl_speed.setStyleSheet("color: #00ff66")
        self.lbl_speed.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_rpm = QLabel("0")
        self.lbl_rpm.setFont(font_large)
        self.lbl_rpm.setStyleSheet("color: #ff4444")
        self.lbl_rpm.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_gear = QLabel("N")
        self.lbl_gear.setFont(QFont("Sans Serif", 48, QFont.Weight.Bold))
        self.lbl_gear.setStyleSheet("color: #ffffff; background: #222; padding: 10px; border-radius: 8px;")
        self.lbl_gear.setAlignment(Qt.AlignmentFlag.AlignCenter)

        readouts.addWidget(self.lbl_speed, 2)
        readouts.addWidget(self.lbl_rpm, 2)
        readouts.addWidget(self.lbl_gear, 1)

        top.addLayout(readouts)

        # System mini readouts
        sys_layout = QVBoxLayout()
        self.lbl_fps = QLabel("FPS: 0")
        self.lbl_cpu = QLabel("CPU: 0%")
        self.lbl_gpu = QLabel("GPU: 0%")
        for w in (self.lbl_fps, self.lbl_cpu, self.lbl_gpu):
            w.setFont(font_med)
            w.setStyleSheet("color: #aaffaa")
        sys_layout.addWidget(self.lbl_fps)
        sys_layout.addWidget(self.lbl_cpu)
        sys_layout.addWidget(self.lbl_gpu)

        top.addLayout(sys_layout)

        # Buttons
        btn_layout = QVBoxLayout()
        self.btn_record = QPushButton("Start Recording")
        self.btn_stop = QPushButton("Stop Recording")
        btn_layout.addWidget(self.btn_record)
        btn_layout.addWidget(self.btn_stop)

        top.addLayout(btn_layout)
        main.addLayout(top)

        # Main content: left gauges, center plots, right stats
        middle = QHBoxLayout()

        # Left gauges & controls
        left = QVBoxLayout()
        self.gauge_speed = QProgressBar()
        self.gauge_speed.setOrientation(Qt.Orientation.Vertical)
        self.gauge_speed.setMinimum(0)
        self.gauge_speed.setMaximum(400)
        self.gauge_speed.setFormat("%v km/h")
        self.gauge_speed.setStyleSheet("QProgressBar { background: #111; color: #0f0; }")

        self.gauge_throttle = QProgressBar()
        self.gauge_throttle.setOrientation(Qt.Orientation.Vertical)
        self.gauge_throttle.setMaximum(100)
        self.gauge_throttle.setFormat("Throttle %p")

        self.gauge_brake = QProgressBar()
        self.gauge_brake.setOrientation(Qt.Orientation.Vertical)
        self.gauge_brake.setMaximum(100)
        self.gauge_brake.setFormat("Brake %p")

        left.addWidget(self.gauge_speed)
        left.addWidget(self.gauge_throttle)
        left.addWidget(self.gauge_brake)

        middle.addLayout(left, 1)

        # Center plots
        center = QVBoxLayout()
        plots_row = QHBoxLayout()

        self.speed_plot = TimeSeriesPlot(title="Speed (km/h)")
        self.rpm_plot = TimeSeriesPlot(title="RPM")
        self.tb_plot = TimeSeriesPlot(title="Throttle / Brake")
        self.steer_plot = TimeSeriesPlot(title="Steering (%)")
        self.pt_plot = TimeSeriesPlot(title="Power / Torque")

        self.s_curve = self.speed_plot.add_curve(pen=pg.mkPen("#00ff66"))
        self.r_curve = self.rpm_plot.add_curve(pen=pg.mkPen("#ff4444"))
        self.t_curve = self.tb_plot.add_curve(pen=pg.mkPen("#00aaff"))
        self.b_curve = self.tb_plot.add_curve(pen=pg.mkPen("#ffaa00"))
        self.steer_curve = self.steer_plot.add_curve(pen=pg.mkPen("#9999ff"))
        self.p_curve = self.pt_plot.add_curve(pen=pg.mkPen("#66ff66"))
        self.tq_curve = self.pt_plot.add_curve(pen=pg.mkPen("#66aaff"))

        plots_row.addWidget(self.speed_plot)
        plots_row.addWidget(self.rpm_plot)
        center.addLayout(plots_row)

        plots_row2 = QHBoxLayout()
        plots_row2.addWidget(self.tb_plot)
        plots_row2.addWidget(self.steer_plot)
        plots_row2.addWidget(self.pt_plot)
        center.addLayout(plots_row2)

        middle.addLayout(center, 3)

        # Right stats
        right = QVBoxLayout()
        stats = QGridLayout()
        self.stat_packet_count = QLabel("Packets: 0")
        self.stat_packet_rate = QLabel("Packet Rate: 0 Hz")
        self.stat_cpu = QLabel("CPU: 0%")
        self.stat_ram = QLabel("RAM: 0%")
        self.stat_gpu_temp = QLabel("GPU Temp: N/A")

        for lbl in (self.stat_packet_count, self.stat_packet_rate, self.stat_cpu, self.stat_ram, self.stat_gpu_temp):
            lbl.setFont(font_med)
            lbl.setStyleSheet("color: #cfcfcf")

        stats.addWidget(self.stat_packet_count, 0, 0)
        stats.addWidget(self.stat_packet_rate, 0, 1)
        stats.addWidget(self.stat_cpu, 1, 0)
        stats.addWidget(self.stat_ram, 1, 1)
        stats.addWidget(self.stat_gpu_temp, 2, 0)

        right.addLayout(stats)
        middle.addLayout(right, 1)

        main.addLayout(middle)

        self.setLayout(main)

    def update_telemetry(self, frame: TelemetryFrame):
        # update readouts
        if frame.speed_kph is not None:
            self.lbl_speed.setText(f"{frame.speed_kph:.1f}")
            self.gauge_speed.setValue(int(frame.speed_kph))
        if frame.engine_rpm is not None:
            self.lbl_rpm.setText(f"{frame.engine_rpm:.0f} RPM")
            # rpm plot gets raw value
        if frame.gear is not None:
            self.lbl_gear.setText(str(frame.gear))

        self.stat_packet_count.setText(f"Packets: {frame.packet_count}")

        # append to plots
        sp = frame.speed_kph if frame.speed_kph is not None else 0.0
        rp = frame.engine_rpm if frame.engine_rpm is not None else 0.0
        th = (frame.throttle * 100.0) if getattr(frame, 'throttle', None) is not None else 0.0
        br = (frame.brake * 100.0) if getattr(frame, 'brake', None) is not None else 0.0
        st = (frame.steering * 100.0) if getattr(frame, 'steering', None) is not None else 0.0
        pw = frame.power if getattr(frame, 'power', None) is not None else 0.0
        tq = frame.torque if getattr(frame, 'torque', None) is not None else 0.0

        self.speed_plot.append(sp)
        self.rpm_plot.append(rp)
        self.tb_plot.append(th, br)
        self.steer_plot.append(st)
        self.pt_plot.append(pw, tq)

        # simple packet rate calc
        now = time.time()
        dt = now - self._last_packet_time if self._last_packet_time else 1.0
        rate = 0.0
        if dt > 0:
            rate = (frame.packet_count - self._last_packet_count) / dt
        self.stat_packet_rate.setText(f"Packet Rate: {rate:.1f} Hz")
        self._last_packet_count = frame.packet_count
        self._last_packet_time = now

        self.telemetry_history.append(frame)

    def update_system(self, metrics: SystemMetrics):
        if metrics.cpu_percent is not None:
            self.stat_cpu.setText(f"CPU: {metrics.cpu_percent:.0f}%")
            self.lbl_cpu.setText(f"CPU: {metrics.cpu_percent:.0f}%")
        if metrics.ram_percent is not None:
            self.stat_ram.setText(f"RAM: {metrics.ram_percent:.0f}%")
        if metrics.gpu_percent is not None:
            self.lbl_gpu.setText(f"GPU: {metrics.gpu_percent:.0f}%")
        if metrics.gpu_temp is not None:
            self.stat_gpu_temp.setText(f"GPU Temp: {metrics.gpu_temp} C")
        self.system_history.append(metrics)

    def _refresh_plots(self):
        self.speed_plot.update_plot()
        self.rpm_plot.update_plot()
        self.tb_plot.update_plot()
        self.steer_plot.update_plot()
        self.pt_plot.update_plot()

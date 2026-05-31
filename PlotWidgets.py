from PyQt6.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg
from collections import deque
from typing import Deque
import time


class TimeSeriesPlot(QWidget):
    def __init__(self, maxlen: int = 600, title: str = ""):
        super().__init__()
        self.maxlen = maxlen
        self.x = deque(maxlen=maxlen)
        self.curves = []

        self.plot = pg.PlotWidget(title=title)
        self.plot.showGrid(x=True, y=True, alpha=0.3)
        layout = QVBoxLayout()
        layout.addWidget(self.plot)
        self.setLayout(layout)

    def add_curve(self, pen=None, name: str = ""):
        c = self.plot.plot(pen=pen, name=name)
        self.curves.append((c, deque(maxlen=self.maxlen)))
        return c

    def append(self, *values):
        # values is tuple of floats matching number of curves
        t = time.time()
        for idx, val in enumerate(values):
            if idx >= len(self.curves):
                break
            _, dq = self.curves[idx]
            dq.append(val if val is not None else 0.0)

    def update_plot(self):
        for c, dq in self.curves:
            c.setData(list(dq))

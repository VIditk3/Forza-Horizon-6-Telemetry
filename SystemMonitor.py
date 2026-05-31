from PyQt6.QtCore import QObject, pyqtSignal
import threading
import time
from typing import Optional

import psutil

try:
    import pynvml
    NVML_AVAILABLE = True
    pynvml.nvmlInit()
except Exception:
    NVML_AVAILABLE = False

from TelemetryModels import SystemMetrics


class SystemMonitor(QObject):
    system_update = pyqtSignal(object)  # emits SystemMetrics

    def __init__(self, interval: float = 0.2):
        super().__init__()
        self.interval = interval
        self._stop_event = threading.Event()
        self._thread = None

    def start(self):
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1.0)

    def _run(self):
        while not self._stop_event.is_set():
            m = SystemMetrics()
            m.timestamp = time.time()
            try:
                m.cpu_percent = psutil.cpu_percent(interval=None)
                vm = psutil.virtual_memory()
                m.ram_percent = vm.percent
                try:
                    freq = psutil.cpu_freq()
                    m.cpu_freq = freq.current if freq else None
                except Exception:
                    m.cpu_freq = None
            except Exception:
                pass

            if NVML_AVAILABLE:
                try:
                    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                    util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    m.gpu_percent = util.gpu
                    mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    m.vram_used = mem.used / (1024.0 * 1024.0)
                    m.vram_total = mem.total / (1024.0 * 1024.0)
                    try:
                        m.gpu_temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                    except Exception:
                        m.gpu_temp = None
                except Exception:
                    pass

            self.system_update.emit(m)
            time.sleep(self.interval)

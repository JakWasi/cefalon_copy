# src/gui/gui_main.py
import os
import sys
import signal
import subprocess
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QHBoxLayout, QVBoxLayout, QPushButton,
    QToolBar, QTabWidget
)
from PyQt5.QtCore import Qt

# ------------------ PATH FIX ------------------
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", ".."))
_SRC_DIR = os.path.join(_PROJECT_ROOT, "src")

# Dodajemy src na początek sys.path
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

# ------------------ IMPORTY ------------------
# Teraz import działa absolutnie w obrębie src
from gui.widgets import LivePlotWidget, FlowTableWidget
from gui.multi_plots_widget import MultiPlotsWidget
from gui.report_manager_widget import ReportManagerWidget

CAPTURE_SCRIPT = os.path.join(_SRC_DIR, "capture", "capture_live.py")

# ------------------ DARK THEME ------------------
DARK_STYLE = """
QWidget {
    background-color: #121212;
    color: #dddddd;
    font-size: 14px;
}

QToolBar {
    background-color: #1f1f1f;
}

QPushButton {
    background-color: #2a2a2a;
    color: #dddddd;
    padding: 6px;
    border: 1px solid #444;
    border-radius: 4px;
}
QPushButton:hover {
    background-color: #3a3a3a;
}
QPushButton:checked {
    background-color: #444;
}

QTableWidget {
    background-color: #1e1e1e;
    gridline-color: #444;
}
QHeaderView::section {
    background-color: #2a2a2a;
    color: #ddd;
    padding: 4px;
    border: 1px solid #444;
}
"""

# ------------------ MAIN WINDOW ------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Network Flow Monitor")
        self.resize(1400, 900)
        self.capture_proc = None
        self._build_ui()
        self.setStyleSheet(DARK_STYLE)

    def _build_ui(self):
        # ------------------ Toolbar ------------------
        toolbar = QToolBar("Main")
        self.addToolBar(toolbar)

        start_btn = QPushButton("Start Capture")
        stop_btn = QPushButton("Stop Capture")
        restart_btn = QPushButton("Restart Capture")

        start_btn.clicked.connect(self.start_capture)
        stop_btn.clicked.connect(self.stop_capture)
        restart_btn.clicked.connect(self.restart_capture)

        toolbar.addWidget(start_btn)
        toolbar.addWidget(stop_btn)
        toolbar.addWidget(restart_btn)

        # ------------------ Tabs ------------------
        tabs = QTabWidget()

        # ------ Live Metrics ------
        live_tab = QWidget()
        live_layout = QHBoxLayout(live_tab)
        live_layout.addWidget(LivePlotWidget(), 2)
        live_layout.addWidget(FlowTableWidget(), 3)
        tabs.addTab(live_tab, "Live Metrics")

        # ------ Analysis Dashboard ------
        analysis_tab = QWidget()
        analysis_layout = QHBoxLayout(analysis_tab)
        multi_plots = MultiPlotsWidget()
        analysis_layout.addWidget(multi_plots)
        tabs.addTab(analysis_tab, "Analysis Dashboard")

        # ------ Reports ------
        reports_tab = QWidget()
        reports_layout = QVBoxLayout(reports_tab)
        reports_layout.addWidget(ReportManagerWidget())
        tabs.addTab(reports_tab, "Reports")

        self.setCentralWidget(tabs)

    # ------------------ Capture control ------------------
    def start_capture(self):
        if self.capture_proc is not None and self.capture_proc.poll() is None:
            print("[GUI] capture already running")
            return
        print("[GUI] starting capture process...")
        self.capture_proc = subprocess.Popen([sys.executable, CAPTURE_SCRIPT])
        print("[GUI] capture pid:", self.capture_proc.pid)

    def stop_capture(self):
        if self.capture_proc is None:
            return
        try:
            pid = self.capture_proc.pid
            print("[GUI] stopping capture pid:", pid)
            self.capture_proc.send_signal(signal.SIGINT)
            try:
                self.capture_proc.wait(timeout=3)
            except Exception:
                self.capture_proc.terminate()
                self.capture_proc.wait(timeout=3)
        except Exception as e:
            print("stop error:", e)
        finally:
            self.capture_proc = None

    def restart_capture(self):
        self.stop_capture()
        QtWidgets.QApplication.processEvents()
        self.start_capture()


# ------------------ MAIN ------------------
def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

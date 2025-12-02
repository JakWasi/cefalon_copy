# src/gui/widgets.py
import os
import sys
import pandas as pd
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QTableWidget, QTableWidgetItem, QPushButton
from PyQt5.QtCore import QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# ensure src on path
_THIS_DIR = os.path.dirname(__file__)
_PROJECT_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", ".."))
_SRC_DIR = os.path.join(_PROJECT_ROOT, "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from models.analyzer import Analyzer

CSV_FILE_DEFAULT = os.path.join(_PROJECT_ROOT, "data", "flows", "processed", "live_flows.csv")


# ------------------ WSPÓLNA KLASA DLA WYKRESÓW ------------------
class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=6, height=3, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi, facecolor="#121212")
        self.ax = fig.add_subplot(111)
        self.ax.set_facecolor("#121212")
        super().__init__(fig)

    def plot(self, x, y, metric, logy=False):
        self.ax.clear()
        self.ax.plot(x, y, color="#66ccff" if metric == "anomaly_score" else "#ffcc66")

        # logarytmiczna skala Y dla anomaly_score
        if logy:
            self.ax.set_yscale("log")

        # stałe zakresy dla pozostałych metryk
        if metric == "anomaly_score":
            self.ax.set_ylim(0.001, max(y) * 1.2 if len(y) else 0.5)
        elif metric == "total_bytes":
            ymax = max(y) if len(y) else 0
            self.ax.set_ylim(0, ymax * 1.2 if ymax > 0 else 1000)
        elif metric == "total_pkts":
            ymax = max(y) if len(y) else 0
            self.ax.set_ylim(0, ymax * 1.2 if ymax > 0 else 100)

        self.ax.set_xlabel("samples", color="#ffffff")
        self.ax.set_ylabel(metric, color="#ffffff")
        self.ax.set_title(metric.replace("_", " ").capitalize(), color="#ffffff")
        self.ax.tick_params(colors="#dddddd")
        self.ax.grid(True, color="#444444")
        self.draw()


# ------------------ WYKRESY NA ŻYWO ------------------
class LivePlotWidget(QWidget):
    def __init__(self, csv_file=CSV_FILE_DEFAULT, parent=None):
        super().__init__(parent)
        self.csv_file = csv_file
        self.current_metric = "total_bytes"

        layout = QVBoxLayout(self)

        # Przyciski metryk
        button_layout = QHBoxLayout()
        self.buttons = {}
        for metric in ["total_bytes", "total_pkts", "anomaly_score"]:
            btn = QPushButton(metric.replace("_", " ").capitalize())
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, m=metric: self.set_metric(m))
            self.buttons[metric] = btn
            button_layout.addWidget(btn)
        layout.addLayout(button_layout)
        self.buttons[self.current_metric].setChecked(True)

        # Canvas wykresu
        self.canvas = MplCanvas(self)
        layout.addWidget(self.canvas)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1000)

    def set_metric(self, metric):
        for m, btn in self.buttons.items():
            btn.setChecked(m == metric)
        self.current_metric = metric
        self.refresh()

    def refresh(self):
        if not os.path.exists(self.csv_file):
            return
        try:
            df = pd.read_csv(self.csv_file)
            if df.empty or self.current_metric not in df.columns:
                return
            y = df[self.current_metric].astype(float).tail(120).values
            x = list(range(len(y)))
            logy = self.current_metric == "anomaly_score"
            self.canvas.plot(x, y, self.current_metric, logy=logy)
        except Exception:
            return


# ------------------ TABELA FLOW ------------------
class FlowTableWidget(QWidget):
    def __init__(self, csv_file=CSV_FILE_DEFAULT, parent=None):
        super().__init__(parent)
        self.csv_file = csv_file

        try:
            self.analyzer = Analyzer()
        except Exception as e:
            print("[FlowTableWidget] Analyzer init failed:", e)
            self.analyzer = None

        self.active_labels = {"benign": True, "suspicious": True, "attack": True}

        layout = QVBoxLayout(self)

        # Checkboxy filtrów
        filter_layout = QHBoxLayout()
        self.checkboxes = {}
        for label in ["benign", "suspicious", "attack"]:
            cb = QCheckBox(label.capitalize())
            cb.setChecked(True)
            cb.stateChanged.connect(self.on_filter_changed)
            self.checkboxes[label] = cb
            filter_layout.addWidget(cb)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        self.table = QTableWidget()
        layout.addWidget(self.table)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1000)

    def on_filter_changed(self):
        for label, cb in self.checkboxes.items():
            self.active_labels[label] = cb.isChecked()
        self.refresh()

    def refresh(self):
        if not os.path.exists(self.csv_file):
            return
        try:
            df = pd.read_csv(self.csv_file)
            if df.empty:
                self.table.clear()
                return

            df = df.tail(200).reset_index(drop=True)

            if self.analyzer:
                try:
                    df = self.analyzer.annotate_df(df)
                except Exception as e:
                    print("[FlowTableWidget] annotate_df failed:", e)

            # filtr wg checkboxów
            if "label" in df.columns:
                df["label"] = df["label"].astype(str).str.strip().str.lower()
                active = [lbl for lbl, val in self.active_labels.items() if val]
                df = df[df["label"].isin(active)]

            # anomaly_score w procentach
            if "anomaly_score" in df.columns:
                df["anomaly_score"] = (df["anomaly_score"].astype(float) * 100).round(2)

            # usuwamy duration
            cols = [c for c in df.columns if c != "duration"]

            self.table.setRowCount(len(df))
            self.table.setColumnCount(len(cols))
            self.table.setHorizontalHeaderLabels(cols)

            # Wypełnianie tabeli stabilnie przy checkboxach
            for i, row in enumerate(df[cols].itertuples(index=False)):
                for j, val in enumerate(row):
                    item = QTableWidgetItem(str(val))
                    if cols[j] == "label":
                        if str(val).lower() == "attack":
                            item.setBackground(QtGui.QColor(180, 40, 40))
                        elif str(val).lower() == "suspicious":
                            item.setBackground(QtGui.QColor(200, 160, 20))
                        elif str(val).lower() == "benign":
                            item.setBackground(QtGui.QColor(40, 110, 40))
                    self.table.setItem(i, j, item)

            self.table.resizeColumnsToContents()

        except Exception as e:
            print("[FlowTableWidget] refresh error:", e)
            return

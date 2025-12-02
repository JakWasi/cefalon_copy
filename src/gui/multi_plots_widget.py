#src/gui/multi_plots_widget.py
import os
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as Canvas
from matplotlib.figure import Figure

_THIS_DIR = os.path.dirname(__file__)
_PROJECT_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", ".."))
CSV_FILE_DEFAULT = os.path.join(_PROJECT_ROOT, "data", "flows", "processed", "live_flows.csv")


class MplFigure(Canvas):
    def __init__(self, width=5, height=3, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi, facecolor="#121212")
        self.ax = fig.add_subplot(111)
        self.ax.set_facecolor("#121212")
        super().__init__(fig)

    def finalize(self):
        # ustawienia kolorów napisów i siatki
        self.ax.title.set_color("#ffffff")
        self.ax.xaxis.label.set_color("#ffffff")
        self.ax.yaxis.label.set_color("#ffffff")
        self.ax.tick_params(colors="#dddddd")
        self.ax.grid(True, color="#444444")
        self.draw()


class MultiPlotsWidget(QWidget):
    def __init__(self, csv=CSV_FILE_DEFAULT, parent=None):
        super().__init__(parent)
        self.csv = csv

        layout = QVBoxLayout(self)

        # wykresy
        self.fig_hist = MplFigure()
        self.fig_scatter = MplFigure()
        self.fig_top = MplFigure()

        layout.addWidget(QLabel("Histogram Anomaly Score"))
        layout.addWidget(self.fig_hist)

        layout.addWidget(QLabel("Scatter: Bytes vs Anomaly Score"))
        layout.addWidget(self.fig_scatter)

        layout.addWidget(QLabel("Top 10 src_ip by Anomaly Score"))
        layout.addWidget(self.fig_top)

        self.refresh()

    def refresh(self):
        if not os.path.exists(self.csv):
            return

        df = pd.read_csv(self.csv)
        if df.empty:
            return

        # ---------------- HISTOGRAM ----------------
        if "anomaly_score" in df.columns:
            self.fig_hist.ax.clear()
            counts, bins, _ = self.fig_hist.ax.hist(df["anomaly_score"], bins=40, color="#66ccff")

            # logarytmiczna skala Y
            self.fig_hist.ax.set_yscale("log")
            self.fig_hist.ax.set_title("Anomaly Score Distribution")
            self.fig_hist.finalize()

        # ---------------- SCATTER ----------------
        if "total_bytes" in df.columns and "anomaly_score" in df.columns:
            self.fig_scatter.ax.clear()
            self.fig_scatter.ax.scatter(
                df["total_bytes"], df["anomaly_score"], s=4, color="#ff8844"
            )
            self.fig_scatter.ax.set_title("Bytes vs Anomaly Score")

            # logarytmiczna skala X (naturalne ticki)
            self.fig_scatter.ax.set_xscale("log")

            self.fig_scatter.finalize()

        # ---------------- TOP N ----------------
        if "src_ip" in df.columns and "anomaly_score" in df.columns:
            self.fig_top.ax.clear()
            top = df.groupby("src_ip")["anomaly_score"].mean().nlargest(10)
            self.fig_top.ax.barh(top.index, top.values, color="#dd4444")
            self.fig_top.ax.set_title("Top 10 src_ip by Anomaly Score")
            self.fig_top.ax.invert_yaxis()
            self.fig_top.finalize()

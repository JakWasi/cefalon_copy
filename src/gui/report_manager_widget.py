# src/gui/report_manager_widget.py
import os
import glob
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QLabel, QDateEdit
)
from PyQt5.QtCore import QDate, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
import os
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--no-sandbox"
from reporting.report_generator import generate_report

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
REPORTS_DIR = os.path.join(PROJECT_ROOT, "data", "flows", "processed", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


class ReportManagerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout(self)

        self.label = QLabel("Zarządzanie raportami")
        main_layout.addWidget(self.label)

        # ------------------ wybór zakresu dat + przyciski ------------------
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Od:"))
        self.start_date = QDateEdit(calendarPopup=True)
        self.start_date.setDate(QDate.currentDate())
        date_layout.addWidget(self.start_date)

        date_layout.addWidget(QLabel("Do:"))
        self.end_date = QDateEdit(calendarPopup=True)
        self.end_date.setDate(QDate.currentDate())
        date_layout.addWidget(self.end_date)

        self.gen_button = QPushButton("Generuj raport")
        self.gen_button.clicked.connect(self.on_generate)
        date_layout.addWidget(self.gen_button)

        self.delete_button = QPushButton("Usuń raport")
        self.delete_button.clicked.connect(self.delete_report)
        date_layout.addWidget(self.delete_button)

        main_layout.addLayout(date_layout)

        # ------------------ lista raportów ------------------
        self.report_list = QListWidget()
        self.report_list.currentItemChanged.connect(self.display_report)
        main_layout.addWidget(self.report_list)

        # ------------------ podgląd raportu ------------------
        self.web_view = QWebEngineView()
        main_layout.addWidget(self.web_view, stretch=2)

        self.refresh_list()

    # ------------------ generowanie raportu ------------------
    def on_generate(self):
        start = self.start_date.date().toPyDate()
        end = self.end_date.date().toPyDate()
        try:
            generate_report(start_date=start, end_date=end, output_dir=REPORTS_DIR)
            self.refresh_list()
        except Exception as e:
            self.label.setText(f"Błąd: {e}")

    # ------------------ lista raportów ------------------
    def refresh_list(self):
        self.report_list.clear()
        files = sorted(glob.glob(os.path.join(REPORTS_DIR, "report_*.html")))
        for i, f in enumerate(files, start=1):
            fname = os.path.basename(f)
            mod_time = datetime.fromtimestamp(os.path.getmtime(f)).strftime("%Y-%m-%d %H:%M:%S")
            self.report_list.addItem(f"{i:03d} | {mod_time} | {fname}")

        if self.report_list.count() > 0:
            self.report_list.setCurrentRow(0)

    # ------------------ wyświetlanie raportu w webview ------------------
    def display_report(self, current, previous=None):
        if current is None:
            return
        text = current.text()
        if "|" not in text:
            return
        fname = text.split("|")[-1].strip()
        path = os.path.join(REPORTS_DIR, fname)
        if os.path.exists(path):
            url = QUrl.fromLocalFile(os.path.abspath(path))
            self.web_view.load(url)

    # ------------------ usuwanie raportu ------------------
    def delete_report(self):
        current = self.report_list.currentItem()
        if current is None:
            self.label.setText("Nie wybrano raportu")
            return
        fname = current.text().split("|")[-1].strip()
        path = os.path.join(REPORTS_DIR, fname)
        if os.path.exists(path):
            try:
                os.remove(path)
                self.refresh_list()
                self.label.setText("Raport usunięty")
            except Exception as e:
                self.label.setText(f"Błąd przy usuwaniu: {e}")

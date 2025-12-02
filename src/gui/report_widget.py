# src/gui/report_widget.py
import os
import webbrowser
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel

from reporting.report_generator import generate_report

class ReportWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)

        self.label = QLabel("Generowanie raportu z flowów")
        layout.addWidget(self.label)

        self.button = QPushButton("Generuj raport")
        self.button.clicked.connect(self.on_generate)
        layout.addWidget(self.button)

    def on_generate(self):
        try:
            generate_report()  # wywołanie modułu reportowania
            # otwieramy raport w domyślnej przeglądarce
            from reporting.report_generator import OUTPUT_FILE
            if os.path.exists(OUTPUT_FILE):
                webbrowser.open(f"file://{OUTPUT_FILE}")
        except Exception as e:
            self.label.setText(f"Błąd podczas generowania raportu: {e}")

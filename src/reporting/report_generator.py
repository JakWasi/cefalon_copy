# src/report/report_generator.py
import os
import csv
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
INPUT_FILE = os.path.join(PROJECT_ROOT, "data", "flows", "processed", "live_flows.csv")

def generate_report(start_date=None, end_date=None, output_dir=None):
    if not os.path.exists(INPUT_FILE):
        print(f"[report_generator] Brak pliku: {INPUT_FILE}")
        return

    if output_dir is None:
        output_dir = os.path.join(PROJECT_ROOT, "data", "flows", "processed", "reports")
    os.makedirs(output_dir, exist_ok=True)

    rows = []
    with open(INPUT_FILE, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ts_str = row.get("timestamp")
            if ts_str:
                ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                if start_date and ts.date() < start_date:
                    continue
                if end_date and ts.date() > end_date:
                    continue
            rows.append(row)

    if not rows:
        print("[report_generator] Brak danych w wybranym zakresie")
        return

    total_flows = len(rows)
    avg_score = sum(float(r.get("anomaly_score", 0)) for r in rows) / total_flows if total_flows else 0

    # ---------------- nazwa raportu z numerem ----------------
    existing = sorted(os.listdir(output_dir))
    indices = [int(f.split("_")[1].split(".")[0]) for f in existing if f.startswith("report_") and f.endswith(".html")]
    idx = max(indices, default=0) + 1
    output_file = os.path.join(output_dir, f"report_{idx:03d}.html")

    html_content = f"""
    <!DOCTYPE html>
    <html lang="pl">
    <head>
        <meta charset="UTF-8">
        <title>Raport Flow Analyzer</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ccc; padding: 8px; text-align: center; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <h1>Raport Flow Analyzer</h1>
        <p>Wygenerowano: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        <p>Liczba flowów: {total_flows} | Średni anomaly score: {avg_score:.2f}</p>
        <table>
            <thead>
                <tr>
                    {''.join(f"<th>{col}</th>" for col in reader.fieldnames)}
                </tr>
            </thead>
            <tbody>
                {''.join('<tr>' + ''.join(f"<td>{row[col]}</td>" for col in reader.fieldnames) + '</tr>' for row in rows)}
            </tbody>
        </table>
    </body>
    </html>
    """

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[report_generator] Raport wygenerowany: {output_file}")

import csv
import os
from datetime import datetime
from typing import Dict

LOG_DIR = "logs"
SKIPPED_FILE = os.path.join(LOG_DIR, "skipped_products.csv")
ERROR_FILE = os.path.join(LOG_DIR, "error_products.csv")

# Garante que a pasta de logs existe
os.makedirs(LOG_DIR, exist_ok=True)

def _write_to_csv(file_path: str, row: Dict):
    file_exists = os.path.isfile(file_path)
    with open(file_path, mode="a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

def log_skip(product: Dict):
    product["log_timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _write_to_csv(SKIPPED_FILE, product)

def log_error(product: Dict, error_msg: str):
    product["log_timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    product["error_message"] = error_msg
    _write_to_csv(ERROR_FILE, product)

# Wrappers opcionais para mensagens no terminal
def info(msg: str):
    print(f"ℹ️ {msg}")

def warning(msg: str):
    print(f"⚠️ {msg}")

def error(msg: str):
    print(f"❌ {msg}")

def critical(msg: str):
    print(f"🔥 {msg}")

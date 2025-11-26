# 🛠 XBZ to OMIE Product Sync

This integration project fetches products from the XBZ Brindes API and inserts them into OMIE ERP. It is built with Python and Docker, using environment variables for secrets and CSVs to track skipped products.

---

## 🚀 Features

- Syncs all products from XBZ in one API call (due to API limits)
- Inserts new products into OMIE via SOAP
- Skips products already present in OMIE
- Truncates `descricao` to 120 characters (OMIE limit)
- Cleans and validates NCM codes
- Logs skipped products into `skipped_products.csv`
- Stops execution on any OMIE error

---

## 📦 Tech Stack

- Python 3.11  
- Docker + Docker Compose  
- OMIE SOAP API  
- XBZ Brindes REST API  
- Pandas, Requests  
- .env for config management

---

## 🧩 Folder Structure


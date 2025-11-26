import json
import time
from app.clients.omie_client import OmieClient
from app.clients.xbz_client import XBZClient
from app.mappings.mapping import map_product
import csv
import os


def sync_products(token, cnpj, omie_app_key, omie_app_secret, dry_run=False, preview_count=None):
    xbz_client = XBZClient(token=token, cnpj=cnpj)
    omie_client = OmieClient(app_key=omie_app_key, app_secret=omie_app_secret)
    skipped_products = []

    print("📦 Buscando produtos da XBZ...")
    xbz_products = xbz_client.get_products()
    print(f"✅ {len(xbz_products)} produtos carregados da XBZ.")
    if xbz_products:
        salvar_produtos_xbz_csv(xbz_products, "produtos_xbz.csv")

    """print("📦 Buscando produtos da OMIE...")
    omie_products = omie_client.list_products()
    existing_codes = set(
        p.get("codigo_produto_integracao")
        for p in omie_products
        if p.get("codigo_produto_integracao")
    )
    print(f"✅ {len(existing_codes)} produtos carregados da OMIE.")

    if preview_count is not None:
        xbz_products = xbz_products[:preview_count]

    for product in xbz_products:
        codigo = product.get("CodigoComposto")

        if codigo in existing_codes:
            print(f"⏭️ Pulando {codigo} — já existe na OMIE.")
            continue

        omie_payload = map_product(product)
        print("🧾 OMIE Payload:\n", json.dumps(omie_payload, indent=2, ensure_ascii=False), "\n")

        if not dry_run:
            response = omie_client.insert_product(omie_payload)
            print("📬 OMIE Response:", response)

        time.sleep(1.1)  # Para evitar o rate limit"""

def salvar_produtos_xbz_csv(produtos, nome_arquivo="produtos_xbz.csv"):
    caminho_arquivo = os.path.join(os.getcwd(), nome_arquivo)
    with open(caminho_arquivo, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=produtos[0].keys())
        writer.writeheader()
        writer.writerows(produtos)

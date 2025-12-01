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
    failed_products = []
    inserted_count = 0
    skipped_count = 0
    failed_count = 0

    print("📦 Buscando produtos da XBZ...")
    xbz_products = xbz_client.get_products()
    print(f"✅ {len(xbz_products)} produtos carregados da XBZ.")
    if xbz_products:
        salvar_produtos_xbz_csv(xbz_products, "produtos_xbz.csv")

    print("\n📦 Buscando produtos da OMIE...")
    omie_products = omie_client.list_products()
    existing_codes = set(
        p.get("codigo_produto_integracao")
        for p in omie_products
        if p.get("codigo_produto_integracao")
    )
    print(f"✅ {len(existing_codes)} produtos carregados da OMIE.\n")

    if preview_count is not None:
        print(f"⚠️ Modo preview: processando apenas {preview_count} produtos.\n")
        xbz_products = xbz_products[:preview_count]

    for idx, product in enumerate(xbz_products, 1):
        codigo = product.get("CodigoComposto")
        print(f"\n[{idx}/{len(xbz_products)}] Processando produto: {codigo}")

        if codigo in existing_codes:
            print(f"⏭️ Pulando {codigo} — já existe na OMIE.")
            skipped_count += 1
            skipped_products.append({
                "codigo": codigo,
                "motivo": "já existe na OMIE (verificado localmente)"
            })
            continue

        omie_payload = map_product(product)
        print("🧾 OMIE Payload:", json.dumps(omie_payload, indent=2, ensure_ascii=False))

        if not dry_run:
            response = omie_client.insert_product(omie_payload)
            
            # Check response status
            if isinstance(response, dict):
                status = response.get("status")
                
                if status == "skipped":
                    print(f"⏭️ Produto {codigo} já existe na OMIE (confirmado pela API)")
                    skipped_count += 1
                    skipped_products.append({
                        "codigo": codigo,
                        "motivo": response.get("reason", "já existe")
                    })
                elif status == "error":
                    print(f"❌ Falha ao inserir produto {codigo}: {response.get('message')}")
                    failed_count += 1
                    failed_products.append({
                        "codigo": codigo,
                        "motivo": response.get("reason", "erro desconhecido"),
                        "mensagem": response.get("message", ""),
                        "fault_code": response.get("fault", "")
                    })
                else:
                    # Success
                    print(f"✅ Produto {codigo} inserido com sucesso!")
                    print(f"📬 OMIE Response: {response}")
                    inserted_count += 1
            else:
                # Success (old format response)
                print(f"✅ Produto {codigo} inserido com sucesso!")
                print(f"📬 OMIE Response: {response}")
                inserted_count += 1

        time.sleep(1.1)  # Para evitar o rate limit

    # Summary
    print("\n" + "="*60)
    print("📊 RESUMO DA SINCRONIZAÇÃO")
    print("="*60)
    print(f"📦 Total de produtos XBZ processados: {len(xbz_products)}")
    print(f"✅ Produtos inseridos: {inserted_count}")
    print(f"⏭️ Produtos pulados: {skipped_count}")
    print(f"❌ Produtos com erro: {failed_count}")
    print("="*60)
    
    # Save logs
    if skipped_products:
        save_skipped_products(skipped_products, "skipped_products.csv")
        print(f"📝 Log de produtos pulados salvo em 'skipped_products.csv'")
    
    if failed_products:
        save_failed_products(failed_products, "failed_products.csv")
        print(f"📝 Log de produtos com erro salvo em 'failed_products.csv'")
        print(f"💡 Você pode tentar sincronizar novamente esses produtos mais tarde.")

def salvar_produtos_xbz_csv(produtos, nome_arquivo="produtos_xbz.csv"):
    caminho_arquivo = os.path.join(os.getcwd(), nome_arquivo)
    with open(caminho_arquivo, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=produtos[0].keys())
        writer.writeheader()
        writer.writerows(produtos)

def save_skipped_products(skipped_products, nome_arquivo="skipped_products.csv"):
    caminho_arquivo = os.path.join(os.getcwd(), nome_arquivo)
    with open(caminho_arquivo, mode="w", newline="", encoding="utf-8") as file:
        fieldnames = ["codigo", "motivo"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(skipped_products)

def save_failed_products(failed_products, nome_arquivo="failed_products.csv"):
    caminho_arquivo = os.path.join(os.getcwd(), nome_arquivo)
    with open(caminho_arquivo, mode="w", newline="", encoding="utf-8") as file:
        fieldnames = ["codigo", "motivo", "mensagem", "fault_code"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(failed_products)

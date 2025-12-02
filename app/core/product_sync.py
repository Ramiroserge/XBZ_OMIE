import json
import time
from app.clients.omie_client import OmieClient
from app.clients.xbz_client import XBZClient
from app.mappings.mapping import map_product
import csv
import os

# Maximum number of products to INSERT per workflow run
# This prevents hitting OMIE's rate limits
# With 3-hour intervals and ~500 products per run, we can sync ~4000 new products/day
MAX_INSERTS_PER_RUN = 500


def sync_products(token, cnpj, omie_app_key, omie_app_secret, dry_run=False, preview_count=None, max_inserts=None):
    xbz_client = XBZClient(token=token, cnpj=cnpj)
    omie_client = OmieClient(app_key=omie_app_key, app_secret=omie_app_secret)
    skipped_products = []
    failed_products = []
    inserted_count = 0
    skipped_count = 0
    failed_count = 0
    rate_limited = False
    
    # Use provided max_inserts or default
    max_inserts_limit = max_inserts if max_inserts is not None else MAX_INSERTS_PER_RUN

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
    
    # Count how many products need to be inserted
    products_to_insert = [p for p in xbz_products if p.get("CodigoComposto") not in existing_codes]
    print(f"📊 Produtos novos para inserir: {len(products_to_insert)}")
    
    # If there are products to insert, check if API is available first
    if len(products_to_insert) > 0:
        print("🔍 Verificando disponibilidade da API OMIE...")
        api_status = omie_client.check_api_status()
        if not api_status.get("available"):
            print(f"⚠️ API OMIE bloqueada: {api_status.get('message', 'Rate limit ativo')}")
            print(f"💡 Aguarde o desbloqueio e tente novamente na próxima execução.")
            print("\n" + "="*60)
            print("📊 RESUMO DA SINCRONIZAÇÃO")
            print("="*60)
            print(f"📦 Total de produtos XBZ: {len(xbz_products)}")
            print(f"✅ Produtos já sincronizados: {len(existing_codes)}")
            print(f"⏳ Produtos aguardando sincronização: {len(products_to_insert)}")
            print(f"⚠️ Nenhuma inserção realizada - API bloqueada.")
            print("="*60)
            return
        print("✅ API OMIE disponível.\n")
    else:
        print("✅ Todos os produtos já estão sincronizados!\n")
        print("\n" + "="*60)
        print("📊 RESUMO DA SINCRONIZAÇÃO")
        print("="*60)
        print(f"📦 Total de produtos XBZ: {len(xbz_products)}")
        print(f"✅ Todos os {len(existing_codes)} produtos já estão na OMIE.")
        print("="*60)
        return
    
    print(f"📊 Limite de inserções por execução: {max_inserts_limit}")
    if len(products_to_insert) > max_inserts_limit:
        print(f"⚠️ Serão inseridos até {max_inserts_limit} produtos nesta execução.")
        print(f"💡 Os demais serão inseridos nas próximas execuções.\n")

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
        
        # Check if we've reached the insert limit
        if inserted_count >= max_inserts_limit:
            print(f"⏸️ Limite de {max_inserts_limit} inserções atingido. Continuará na próxima execução.")
            break

        omie_payload = map_product(product)
        print("🧾 OMIE Payload:", json.dumps(omie_payload, indent=2, ensure_ascii=False))

        if not dry_run:
            response = omie_client.insert_product(omie_payload)
            
            # Check if we got rate limited
            if response is None:
                # Rate limited - exit gracefully
                print("⏸️ API bloqueada. Salvando progresso e encerrando.")
                rate_limited = True
                break
            
            # Check response status
            if isinstance(response, dict):
                status = response.get("status")
                
                if status == "rate_limited":
                    print("⏸️ API bloqueada. Salvando progresso e encerrando.")
                    rate_limited = True
                    break
                elif status == "skipped":
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
    print(f"📦 Total de produtos XBZ: {len(xbz_products)}")
    print(f"✅ Produtos inseridos nesta execução: {inserted_count}")
    print(f"⏭️ Produtos pulados (já existem): {skipped_count}")
    print(f"❌ Produtos com erro: {failed_count}")
    remaining = len(products_to_insert) - inserted_count
    if remaining > 0:
        print(f"⏳ Produtos restantes para próximas execuções: {remaining}")
    if rate_limited:
        print(f"⚠️ Execução interrompida por rate limit. Continuará na próxima execução.")
    print("="*60)
    
    # Save logs
    if skipped_products:
        save_skipped_products(skipped_products, "skipped_products.csv")
        print(f"📝 Log de produtos pulados salvo em 'skipped_products.csv'")
    
    if failed_products:
        save_failed_products(failed_products, "failed_products.csv")
        print(f"📝 Log de produtos com erro salvo em 'failed_products.csv'")
        print(f"💡 Você pode tentar sincronizar novamente esses produtos mais tarde.")
    
    # Exit gracefully even if rate limited - we saved progress
    # The next run will pick up where we left off
    if rate_limited:
        print(f"\n✅ Progresso salvo. A sincronização continuará na próxima execução agendada.")

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

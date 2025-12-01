import requests
import time

class OmieClient:
    def __init__(self, app_key, app_secret):
        self.app_key = app_key
        self.app_secret = app_secret
        self.endpoint = "https://app.omie.com.br/api/v1/geral/produtos/"

    def list_products(self):
        all_products = []
        page = 1

        while True:
            payload = {
                "call": "ListarProdutos",
                "app_key": self.app_key,
                "app_secret": self.app_secret,
                "param": [
                    {
                        "pagina": page,
                        "registros_por_pagina": 500,
                        "apenas_importado_api": "N",
                        "filtrar_apenas_omiepdv": "N"
                    }
                ]
            }

            try:
                response = requests.post(self.endpoint, json=payload)
                response.raise_for_status()
                data = response.json()

                if "faultcode" in data:
                    print(f"❌ Erro ao listar produtos (página {page}): {data}")
                    break

                # Check for product_list_result structure
                produto_servico_cadastro = data.get("produto_servico_cadastro", [])
                if not produto_servico_cadastro:
                    break

                all_products.extend(produto_servico_cadastro)
                print(f"📄 Página {page}: {len(produto_servico_cadastro)} produtos carregados...")
                
                # Check if there are more pages
                total_paginas = data.get("total_de_paginas", 0)
                if page >= total_paginas:
                    break
                    
                page += 1
                time.sleep(0.5)  # Rate limit prevention

            except Exception as e:
                print(f"❌ Erro ao buscar produtos da página {page}: {e}")
                break

        return all_products

    def insert_product(self, product_data):
        payload = {
            "call": "IncluirProduto",
            "app_key": self.app_key,
            "app_secret": self.app_secret,
            "param": [product_data],
        }
        response = requests.post(self.endpoint, json=payload)
        data = response.json()

        if "faultcode" in data:
            fault = data.get("faultcode")
            message = data.get("faultstring", "Erro desconhecido")
            
            # Handle specific error types
            if fault == "MISUSE_API_PROCESS":
                print("📬 OMIE Response:", data)
                print("🚫 OMIE API bloqueada. Encerrando sincronização.")
                exit(1)
            elif fault == "SOAP-ENV:Client-102":
                # Product already exists - this is expected, not an error
                print(f"⏭️ Produto já existe na OMIE (será pulado)")
                return {"status": "skipped", "reason": "already_exists", "message": message}
            else:
                # Other errors - stop execution
                print(f"📬 OMIE Response: {data}")
                print(f"🚫 Erro crítico da OMIE ({fault}): {message}")
                print("⚠️ Encerrando sincronização por erro crítico.")
                exit(1)

        return data

    def atualizar_produtos_existentes(self, produtos: list):
        for produto in produtos:
            try:
                peso = round(float(produto.get("Peso") or 0) / 1000, 3)
                altura = float(produto.get("Altura") or 0)
                largura = float(produto.get("Largura") or 0)
                profundidade = float(produto.get("Profundidade") or 0)
                quantidade = int(produto.get("QuantidadeDisponivelEstoquePrincipal") or 0)
                if quantidade < 0:
                    quantidade = 0

                custo_str = str(produto.get("PrecoVendaFormatado") or "0").replace(",", ".")
                custo = float(custo_str)

                if quantidade >= 1000:
                    markup = 1.80
                elif 500 <= quantidade < 1000:
                    markup = 1.85
                elif 250 <= quantidade < 500:
                    markup = 1.90
                elif 150 <= quantidade < 250:
                    markup = 2.15
                elif 50 <= quantidade < 150:
                    markup = 2.22
                else:
                    markup = 2.32

                novo_valor = round(custo * markup, 2)

                # Construção condicional dos campos
                param_data = {
                    "codigo_produto_integracao": produto.get("CodigoComposto"),
                    "valor_unitario": novo_valor,
                    "peso_bruto": peso,
                    "quantidade_estoque": quantidade
                }
                if altura > 0:
                    param_data["altura"] = altura
                if largura > 0:
                    param_data["largura"] = largura
                if profundidade > 0:
                    param_data["profundidade"] = profundidade

                payload = {
                    "call": "AlterarProduto",
                    "app_key": self.app_key,
                    "app_secret": self.app_secret,
                    "param": [param_data]
                }

                response = requests.post(self.endpoint, json=payload)
                data = response.json()

                if "faultcode" in data:
                    print(f"⚠️ Falha ao atualizar {produto.get('CodigoComposto')}: {data}")
                else:
                    print(f"✅ Produto {produto.get('CodigoComposto')} atualizado com sucesso. Valor antigo: R$ {custo}. Valor novo: R$ {novo_valor}")
                    print(
                        f"📦 Altura: {altura}, Largura: {largura}, Profundidade: {profundidade}, Estoque: {quantidade}, Peso: {peso}")

                time.sleep(1.1)  # Para evitar rate limit

            except Exception as e:
                print(f"❌ Erro ao atualizar produto {produto.get('CodigoComposto')}: {e}")




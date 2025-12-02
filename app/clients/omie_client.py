import requests
import time

class OmieClient:
    def __init__(self, app_key, app_secret):
        self.app_key = app_key
        self.app_secret = app_secret
        self.endpoint = "https://app.omie.com.br/api/v1/geral/produtos/"
    
    def check_api_status(self):
        """Quick check if the API is available (not rate limited)."""
        payload = {
            "call": "ListarProdutos",
            "app_key": self.app_key,
            "app_secret": self.app_secret,
            "param": [{"pagina": 1, "registros_por_pagina": 1}]
        }
        try:
            response = requests.post(self.endpoint, json=payload, timeout=10)
            data = response.json()
            if data.get("faultcode") == "MISUSE_API_PROCESS":
                # Extract wait time from message if available
                message = data.get("faultstring", "")
                return {"available": False, "message": message}
            return {"available": True}
        except Exception as e:
            return {"available": False, "message": str(e)}

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

    def insert_product(self, product_data, max_retries=3):
        payload = {
            "call": "IncluirProduto",
            "app_key": self.app_key,
            "app_secret": self.app_secret,
            "param": [product_data],
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.post(self.endpoint, json=payload, timeout=30)
                data = response.json()

                if "faultcode" in data:
                    fault = data.get("faultcode")
                    message = data.get("faultstring", "Erro desconhecido")
                    
                    # Handle specific error types
                    if fault == "MISUSE_API_PROCESS":
                        print("📬 OMIE Response:", data)
                        print("⚠️ OMIE API bloqueada por rate limit.")
                        # Return a special status so the sync can save progress and exit gracefully
                        return {"status": "rate_limited", "reason": "api_blocked", "message": message}
                    elif fault == "SOAP-ENV:Client-102":
                        # Product already exists - this is expected, not an error
                        print(f"⏭️ Produto já existe na OMIE (será pulado)")
                        return {"status": "skipped", "reason": "already_exists", "message": message}
                    elif fault == "SOAP-ENV:Server":
                        # Server-side error - retry
                        if attempt < max_retries - 1:
                            wait_time = (attempt + 1) * 2  # 2s, 4s, 6s
                            print(f"⚠️ Erro temporário do servidor OMIE. Tentativa {attempt + 1}/{max_retries}. Aguardando {wait_time}s...")
                            time.sleep(wait_time)
                            continue
                        else:
                            # Max retries reached - skip this product
                            print(f"⚠️ Falha após {max_retries} tentativas. Pulando produto.")
                            return {"status": "error", "reason": "server_error", "message": message, "fault": fault}
                    else:
                        # Other client errors - skip and continue
                        print(f"⚠️ Erro da OMIE ({fault}): {message}")
                        return {"status": "error", "reason": "client_error", "message": message, "fault": fault}

                return data
                
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"⏱️ Timeout ao conectar com OMIE. Tentativa {attempt + 1}/{max_retries}. Aguardando {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"⚠️ Timeout após {max_retries} tentativas. Pulando produto.")
                    return {"status": "error", "reason": "timeout", "message": "Request timeout"}
                    
            except Exception as e:
                print(f"⚠️ Erro inesperado ao inserir produto: {e}")
                return {"status": "error", "reason": "exception", "message": str(e)}
        
        return {"status": "error", "reason": "max_retries_exceeded"}

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




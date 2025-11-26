import re

def aplicar_markup(custo: float, quantidade: int) -> float:
    if quantidade >= 1000:
        markup = 1.80
    elif quantidade >= 500:
        markup = 1.85
    elif quantidade >= 250:
        markup = 1.90
    elif quantidade >= 150:
        markup = 2.15
    elif quantidade >= 50:
        markup = 2.22
    else:
        markup = 2.32
    return round(custo * markup, 2)

def map_product(xbz_product: dict) -> dict:
    raw_ncm = xbz_product.get("Ncm", "")

    # Fix common typos (e.g. letter O → zero)
    ncm_fixed = str(raw_ncm).upper().replace("O", "0")  # Only 'O' → '0' for now

    # Remove everything except digits and truncate to 8 characters
    clean_ncm = re.sub(r"[^\d]", "", ncm_fixed)[:8]     #Eu fiz isso para corrigir alguns erros de digitação existentes no código cnm de alguns produtos

    descricao = f"{xbz_product['Nome']} - Cor: {xbz_product.get('CorWebPrincipal', '').strip()} - Codigo: {xbz_product.get('CodigoComposto')}"

    # Ensure descricao is at most 120 characters
    descricao = descricao[:120]
    custo = xbz_product.get("PrecoVenda") or 0
    quantidade = xbz_product.get("QuantidadeDisponivelEstoquePrincipal") or 0
    preco_final = aplicar_markup(custo, quantidade)

    return {
        "codigo": xbz_product["CodigoComposto"],
        "codigo_produto_integracao": xbz_product["CodigoComposto"],
        "descricao": descricao,
        "descr_detalhada": xbz_product["Descricao"],
        "altura": xbz_product.get("Altura") or 0,
        "largura": xbz_product.get("Largura") or 0,
        "profundidade": xbz_product.get("Profundidade") or 0,
        "peso_bruto": round((xbz_product.get("Peso") or 0) / 1000, 3),
        "valor_unitario": preco_final,
        "ncm": clean_ncm,
        "quantidade_estoque": xbz_product.get("quantidade"),
        "unidade": "UN",
        "bloqueado": "N",
        "importado_api": "S"
    }

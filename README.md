# 📦 Sincronização de Produtos XBZ → OMIE

Sistema automático que sincroniza os produtos do catálogo da **XBZ Brindes** para o seu **OMIE ERP**.

---

## 🎯 O que este sistema faz?

Este sistema **copia automaticamente** todos os produtos da XBZ para o OMIE, incluindo:

- ✅ Nome e descrição do produto
- ✅ Código do produto (SKU)
- ✅ Preço de venda (com markup automático baseado no estoque)
- ✅ Dimensões (altura, largura, profundidade)
- ✅ Peso
- ✅ Código NCM

---

## ⏰ Como funciona?

O sistema roda **automaticamente a cada 3 horas** através do GitHub Actions.

### Fluxo de execução:

```
1. 📥 Busca todos os produtos da XBZ
2. 📥 Busca todos os produtos já cadastrados no OMIE
3. 🔍 Compara as duas listas
4. ⏭️ Pula os produtos que já existem no OMIE
5. ➕ Cadastra os produtos novos no OMIE
6. 📊 Gera um relatório do que foi feito
```

---

## 🛡️ Proteção contra bloqueio da API

A API do OMIE tem limite de requisições. Para evitar bloqueios, o sistema:

| Proteção | Descrição |
|----------|-----------|
| **Limite por execução** | Cadastra no máximo **500 produtos novos** por vez |
| **Intervalo entre requisições** | Aguarda 1,1 segundo entre cada cadastro |
| **Verificação prévia** | Checa se a API está disponível antes de começar |
| **Retomada automática** | Se bloqueado, continua na próxima execução |

> 💡 **Na prática:** Com 8 execuções por dia, o sistema pode cadastrar até **4.000 produtos novos por dia**.

---

## 📊 Entendendo os relatórios

Após cada execução, o sistema gera um resumo como este:

```
============================================================
📊 RESUMO DA SINCRONIZAÇÃO
============================================================
📦 Total de produtos XBZ: 10.194
✅ Produtos inseridos nesta execução: 500
⏭️ Produtos pulados (já existem): 8.000
❌ Produtos com erro: 2
⏳ Produtos restantes para próximas execuções: 1.692
============================================================
```

### O que cada linha significa:

| Ícone | Significado |
|-------|-------------|
| 📦 | Total de produtos no catálogo da XBZ |
| ✅ | Quantos produtos NOVOS foram cadastrados nesta execução |
| ⏭️ | Quantos produtos JÁ EXISTIAM no OMIE (foram ignorados) |
| ❌ | Quantos produtos deram erro (salvos em arquivo para análise) |
| ⏳ | Quantos produtos ainda faltam cadastrar nas próximas execuções |

---

## 📁 Arquivos gerados

Após cada execução, são gerados arquivos CSV com detalhes:

| Arquivo | Conteúdo |
|---------|----------|
| `produtos_xbz.csv` | Lista completa dos produtos da XBZ |
| `skipped_products.csv` | Produtos que foram pulados (já existem) |
| `failed_products.csv` | Produtos que deram erro (com motivo) |

Estes arquivos ficam disponíveis para download nos **Artifacts** de cada execução no GitHub.

---

## 💰 Cálculo automático de preço

O sistema aplica um **markup automático** baseado na quantidade em estoque:

| Estoque | Markup | Exemplo (Custo R$ 10,00) |
|---------|--------|--------------------------|
| 1.000+ unidades | 1,80x | R$ 18,00 |
| 500 a 999 | 1,85x | R$ 18,50 |
| 250 a 499 | 1,90x | R$ 19,00 |
| 150 a 249 | 2,15x | R$ 21,50 |
| 50 a 149 | 2,22x | R$ 22,20 |
| Menos de 50 | 2,32x | R$ 23,20 |

---

## ▶️ Como executar manualmente?

Se precisar rodar a sincronização fora do horário automático:

1. Acesse o repositório no **GitHub**
2. Clique na aba **"Actions"**
3. Selecione **"Sync Products from XBZ to OMIE"**
4. Clique no botão **"Run workflow"**
5. (Opcional) Altere o limite de produtos se desejar
6. Clique em **"Run workflow"** verde

---

## ⚙️ Configurações necessárias

O sistema precisa das seguintes credenciais configuradas como **Secrets** no GitHub:

| Secret | Descrição |
|--------|-----------|
| `XBZ_TOKEN` | Token de autenticação da API XBZ |
| `XBZ_CNPJ` | CNPJ cadastrado na XBZ |
| `OMIE_APP_KEY` | Chave do aplicativo OMIE |
| `OMIE_APP_SECRET` | Segredo do aplicativo OMIE |

> ⚠️ **Importante:** Nunca compartilhe estas credenciais. Elas estão seguras nos Secrets do GitHub.

---

## ❓ Perguntas frequentes

### O sistema vai duplicar produtos?

**Não.** Antes de cadastrar, o sistema verifica se o produto já existe no OMIE pelo código. Se já existir, ele pula para o próximo.

### O que acontece se a API do OMIE bloquear?

O sistema **para automaticamente**, salva o progresso, e **continua de onde parou** na próxima execução (em 3 horas).

### Posso alterar o limite de 500 produtos por execução?

**Sim.** Ao executar manualmente, você pode alterar o campo "Maximum products to insert". Mas cuidado: valores muito altos podem causar bloqueio da API.

### Como sei se a sincronização está funcionando?

Acesse a aba **"Actions"** no GitHub. Você verá o histórico de todas as execuções com status de ✅ sucesso ou ❌ falha.

### Um produto deu erro. O que fazer?

Baixe o arquivo `failed_products.csv` nos Artifacts da execução. Ele contém o código do produto e o motivo do erro. Corrija o problema na XBZ e aguarde a próxima sincronização.

---

## 📞 Suporte

Em caso de dúvidas ou problemas, verifique:

1. Os logs da execução na aba **Actions** do GitHub
2. Os arquivos CSV nos **Artifacts**
3. Se as credenciais nos **Secrets** estão corretas

---

*Última atualização: Dezembro 2025*

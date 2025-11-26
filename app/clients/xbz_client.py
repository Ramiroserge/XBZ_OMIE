import requests
from typing import List, Dict

class XBZClient:

    def __init__(self, token: str, cnpj: str):
        self.token = token
        self.cnpj = cnpj
        self.base_url = "https://api.minhaxbz.com.br:5001/api/clientes"

    def get_products(self) -> List[Dict]:
        url = f"{self.base_url}/GetListaDeProdutos"
        params = {
            "token": self.token,
            "cnpj": self.cnpj
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

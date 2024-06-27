
import json
import requests


def consultar_status_pedido(pedido):
    url = 'https://apiconsulti.gestaoar.com.br/consultibrasil/api/GarAPIs/ConsultaPedidoProtocolo'
    headers = {"Content-Type": "application/json"}
    payload = { 
                "apiKey": "e5aaffae75484e138cd1685e2f486b54452edf0e867a4fda8e7bdd8f16b92502",
                "Pedido": pedido,
                "Protocolo": ""
    }
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    if response.status_code == 200:
        try:
            response_data = response.json()
            hash_venda = response_data
            return hash_venda, None
        except json.decoder.JSONDecodeError:
            return None, ["JSONDecodeError: A resposta não é um JSON válido"]
    else:
        return None, [f"Erro: A requisição retornou o status {response.status_code}"]
hash_venda, error = consultar_status_pedido('21438')


print(hash_venda["isProtocolo"] == '0')
print(error)
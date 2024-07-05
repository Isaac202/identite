
import json
import requests



def gerar_protocolo(pedido, cnpj, cpf, data_nascimento, is_possui_cnh):
    url = 'https://apiconsulti.gestaoar.com.br/consultibrasil/api/GarAPIs/'  # Substitua pela URL da API que gera os protocolos
    headers = {"Content-Type": "application/json"}
    payload = {
        "apiKey": "e5aaffae75484e138cd1685e2f486b54452edf0e867a4fda8e7bdd8f16b92502",
        "Pedido": pedido,
        "CNPJ": cnpj,
        "CPF": cpf,
        "DataNascimento": data_nascimento,
        "IsPossuiCNH": is_possui_cnh
    }

    response = requests.post(f'{url}EmitirProtocolo', data=json.dumps(payload), headers=headers)
    if response.status_code == 200:
        try:
            response_data = response.json()
            print(response_data)
            if 'ErrorCode' in response_data:
                erros = [erro['ErrorDescription'] for erro in response_data if 'ErrorDescription' in erro]
                return None, erros
            else:
                return response_data, None
        except json.decoder.JSONDecodeError:
            return None, ["JSONDecodeError: A resposta não é um JSON válido"]
    else:
        return None, [f"Erro: A requisição retornou o status {response.status_code}"]
    
def consultar_status_pedido(pedido):
    url = 'https://apiconsulti.gestaoar.com.br/Agilize/api/GarAPIs/ConsultaPedidoProtocolo'
    headers = {"Content-Type": "application/json"}
    payload = { 
                "apiKey": "cda7ee3929fd4e5d96c26fe4430a27bd7d7c575176cc497294d09b2a446cc3c1",
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
hash_venda, error = consultar_status_pedido('62536')

if hash_venda["StatusPedido"] != 'Protocolo Gerado':
    print("O protocolo ainda não foi gerado.")
print(hash_venda)
print(error)
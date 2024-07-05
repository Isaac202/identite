import requests
import json
from cryptography.fernet import Fernet
from django.conf import settings
import random
import string
from base.models import Pedidos

def encrypt_voucher(voucher_code):
    fernet = Fernet(settings.SECRET_KEY_CRYPTO.encode())
    encrypted_voucher = fernet.encrypt(voucher_code.encode()).decode()
    return encrypted_voucher

def decrypt_voucher(encrypted_voucher):
    fernet = Fernet(settings.SECRET_KEY_CRYPTO.encode())
    decrypted_voucher = fernet.decrypt(encrypted_voucher.encode()).decode()
    return decrypted_voucher

url = settings.URL_API
API_KEY = settings.API_KEY


def salvar_venda(cliente):
    endpoint = f'{url}/api/GarAPIs/'
    apiKey = API_KEY
    HashVendedor=  "01d6e9ff-3b53-4ba4-b9a7-f0ea9c9d4157"
    HashTabela = "b6952b6b-00ef-4f49-bc40-f139b0ac2e71"
    FormaPagamento = 11
    CodigoVoucher = cliente.voucher.code

    headers = {'Content-Type': 'application/json'}
    print(cliente.telefone[0:2],cliente.telefone[2:])
    payload = {
        "apiKey": apiKey,
        "HashVendedor": HashVendedor,
        "HashTabela": HashTabela,
        "FormaPagamento": FormaPagamento,
        "CodigoVoucher": CodigoVoucher,
        "Cliente":{
            "CNPJCPF": cliente.cpf if cliente.cnpj == None else cliente.cnpj,
            "NomeRazaoSocial": cliente.razao_social,
            "NomeFantasia": cliente.nome_fantasia,
            "Email": cliente.email,
            "CEP": cliente.cep,
            "Logradouro": cliente.logradouro,
            "Numero": cliente.numero,
            "Complemento":cliente.complemento,
            "Bairro": cliente.bairro,
            "Cidade": cliente.cidade,
            "UF": cliente.uf,
            "CodigoIBGE": cliente.cod_ibge,
            "DDD": cliente.telefone[0:2],
            "Telefone": cliente.telefone[2:]
        },
        "Produtos": [
            {
                "HashProduto": "e9eaa186-f11e-4a08-9f22-387c6c60e035"
            }
        ]
    }
    print(payload)
    response = requests.post(f"{endpoint}/Comprar", json.dumps(payload), headers=headers)
    if response.status_code == 200 and response.text.strip():
        try:
            response_data = response.json()
            if "Erros" in response_data:
                erros = response_data["Erros"]
                for erro in erros:
                    print(erro["Ocorrencia"])
                    return None ,erro["Ocorrencia"]
            else:
                pedido = Pedidos(pedido=response_data["Produtos"][0]["Pedido"], protocolo="")
                pedido.save()
                return pedido, None
        except json.decoder.JSONDecodeError:
            print("JSONDecodeError: A resposta não é um JSON válido")
    else:
        print(f"Erro: A requisição retornou o status {response.status_code}")
    return None



def gerar_protocolo(pedido, cnpj, cpf, data_nascimento, is_possui_cnh):
    endpoint = f'{url}/api/GarAPIs/'  # Substitua pela URL da API que gera os protocolos
    headers = {"Content-Type": "application/json"}
    payload = {
        "apiKey": API_KEY,
        "Pedido": pedido,
        "CNPJ": cnpj,
        "CPF": cpf,
        "DataNascimento": data_nascimento,
        "IsPossuiCNH": is_possui_cnh
    }

    response = requests.post(f'{endpoint}EmitirProtocolo', data=json.dumps(payload), headers=headers)
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
    



def obter_disponibilidade_agenda():
    endpoint = f'{url}/api/GarAPIs/ObterDisponibilidadeAgenda'
    headers = {"Content-Type": "application/json"}
    payload = {
       "apiKey": API_KEY,
        "DataInicial": "2024-06-27",
        "DataFinal": "2024-07-29",
        "hashLocal": "01d6e9ff-3b53-4ba4-b9a7-f0ea9c9d4157"
    }

    response = requests.post(endpoint, data=json.dumps(payload), headers=headers)
    if response.status_code == 200:
        try:
            response_data = response.json()
            return response_data, None
        except json.decoder.JSONDecodeError:
            return None, ["JSONDecodeError: A resposta não é um JSON válido"]
    else:
        return None, [f"Erro: A requisição retornou o status {response.status_code}"]
    


def agendar_pedido( hash_venda, data, hora_inicial, hora_final):
    endpoint = f'{url}/api/GarAPIs/Agendamento'
    headers = {"Content-Type": "application/json"}
    payload = { 
        "apiKey": API_KEY,
        "HashLocal": "01d6e9ff-3b53-4ba4-b9a7-f0ea9c9d4157",
        "DataInicial": f"{data} {hora_inicial}",
        "DataFinal": f"{data} {hora_final}",
        "HashVenda": hash_venda,
        "IsCliente":"1"
    }
    response = requests.post(endpoint, data=json.dumps(payload), headers=headers)
    if response.status_code == 200:
        try:
            response_data = response.json()
            return response_data, None
        except json.decoder.JSONDecodeError:
            return None, ["JSONDecodeError: A resposta não é um JSON válido"]
    else:
        return None, [f"Erro: A requisição retornou o status {response.status_code}"]
    


def consultar_status_pedido(pedido):
    endpont = f'{url}/api/GarAPIs/ConsultaPedidoProtocolo'
    headers = {"Content-Type": "application/json"}
    payload = { 
                "apiKey": API_KEY,
                "Pedido": pedido,
                "Protocolo": ""
    }
    response = requests.post(endpont, data=json.dumps(payload), headers=headers)
    if response.status_code == 200:
        try:
            response_data = response.json()
            hash_venda = response_data
            return hash_venda, None
        except json.decoder.JSONDecodeError:
            return None, ["JSONDecodeError: A resposta não é um JSON válido"]
    else:
        return None, [f"Erro: A requisição retornou o status {response.status_code}"]
    

def generate_random_code(length=12):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def adicionar_protocolo_e_hashvenda_no_pedido(pedido, protocolo,hash_venda):
    # Adicione o protocolo ao pedido aqui
    pedido.protocolo = protocolo
    pedido.hashVenda = hash_venda
    pedido.save()



def verifica_se_pode_videoconferecias(cliente):
    # Verifique se o pedido pode ser videoconferido
    endpoint = f'{url}/api/GarAPIs/ConsultaPedidoProtocolo'
    headers = {"Content-Type": "application/json"}
    payload = {
        "apiKey": API_KEY,
        "CPF": cliente.cpf
    }
    response = requests.post(endpoint, data=json.dumps(payload), headers=headers)
    data = response.json()
    if not data.get('IsOk', True) and not cliente.carteira_habilitacao:
        return False
    return True
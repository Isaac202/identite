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

def salvar_venda(cliente):
    endpoint = f'{url}/api/GarAPIs/'
    apiKey = "cda7ee3929fd4e5d96c26fe4430a27bd7d7c575176cc497294d09b2a446cc3c1"
    HashVendedor=  "01d6e9ff-3b53-4ba4-b9a7-f0ea9c9d4157"
    HashTabela = "86d7f05b-a75d-4e1f-b4a2-3558424e678a"
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
    url = f'{url}/api/GarAPIs/'  # Substitua pela URL da API que gera os protocolos
    headers = {"Content-Type": "application/json"}
    payload = {
        "apiKey": "cda7ee3929fd4e5d96c26fe4430a27bd7d7c575176cc497294d09b2a446cc3c1",
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
    



def obter_disponibilidade_agenda():
    url = f'{url}/api/GarAPIs/ObterDisponibilidadeAgenda'
    headers = {"Content-Type": "application/json"}
    payload = {
       "apiKey": "cda7ee3929fd4e5d96c26fe4430a27bd7d7c575176cc497294d09b2a446cc3c1",
        "DataInicial": "2024-06-27",
        "DataFinal": "2024-07-29",
        "hashLocal": "01d6e9ff-3b53-4ba4-b9a7-f0ea9c9d4157"
    }

    response = requests.post(url, data=json.dumps(payload), headers=headers)
    if response.status_code == 200:
        try:
            response_data = response.json()
            return response_data, None
        except json.decoder.JSONDecodeError:
            return None, ["JSONDecodeError: A resposta não é um JSON válido"]
    else:
        return None, [f"Erro: A requisição retornou o status {response.status_code}"]
    


def agendar_pedido( hash_venda, data, hora_inicial, hora_final):
    url = f'{url}/api/GarAPIs/AgendarPedido'
    headers = {"Content-Type": "application/json"}
    payload = { 
        "apiKey": "cda7ee3929fd4e5d96c26fe4430a27bd7d7c575176cc497294d09b2a446cc3c1",
        "HashLocal": "01d6e9ff-3b53-4ba4-b9a7-f0ea9c9d4157",
        "DataInicial": f"{data} {hora_inicial}",
        "DataFinal": f"{data} {hora_final}",
        "HashVenda": hash_venda,
        "IsCliente":"1"
    }
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    if response.status_code == 200:
        try:
            response_data = response.json()
            return response_data, None
        except json.decoder.JSONDecodeError:
            return None, ["JSONDecodeError: A resposta não é um JSON válido"]
    else:
        return None, [f"Erro: A requisição retornou o status {response.status_code}"]
    


def consultar_status_pedido(pedido):
    url = f'{url}/api/GarAPIs/ConsultaPedidoProtocolo'
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
    

def generate_random_code(length=12):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
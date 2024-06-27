import requests
import json
from cryptography.fernet import Fernet
from django.conf import settings

from base.models import Pedidos

def encrypt_voucher(voucher_code):
    fernet = Fernet(settings.SECRET_KEY_CRYPTO.encode())
    encrypted_voucher = fernet.encrypt(voucher_code.encode()).decode()
    return encrypted_voucher

def decrypt_voucher(encrypted_voucher):
    fernet = Fernet(settings.SECRET_KEY_CRYPTO.encode())
    decrypted_voucher = fernet.decrypt(encrypted_voucher.encode()).decode()
    return decrypted_voucher

'''


{
	"apiKey": "123ChaveDisponibilizadaPeloSistema456",
    "HashVendedor": "1d3ntific4d0r-V3ndend0r",
    "HashTabela": "1d3ntific4d0r-T4bela",
    "FormaPagamento": 8,
    "CodigoVoucher": "",
    "Cliente":{
    	"CNPJCPF": "19999999992",
    	"NomeRazaoSocial": "Paulo Henrique Fraga Mathias Netto",
    	"NomeFantasia": "",
    	"Email": "paulo***************.com.br",
    	"CEP": "90450120",
    	"Logradouro": "Rua Carlos Trein Filho",
    	"Numero": "627",
    	"Complemento": "",
    	"Bairro": "Mont Serrat",
    	"Cidade": "Porto Alegre",
    	"UF": "RS",
    	"CodigoIBGE": "4314902",
    	"DDD": 51,
    	"Telefone": 989999912
    },
    "Produtos": [
        {
            "HashProduto": "1d3ntific4d0r-Pr0duto"
        },
        {
            "HashProduto": "1d3ntific4d0r-0utro-Pr0duto"
        }
    ]
}
'''

import json

def salvar_venda(cliente):
    endpoint = 'https://apiconsulti.gestaoar.com.br/consultibrasil/'
    apiKey = "e5aaffae75484e138cd1685e2f486b54452edf0e867a4fda8e7bdd8f16b92502"
    HashVendedor=  "01d6e9ff-3b53-4ba4-b9a7-f0ea9c9d4157"
    HashTabela = "86d7f05b-a75d-4e1f-b4a2-3558424e678a"
    FormaPagamento = 8
    CodigoVoucher = cliente.voucher.code

    headers = {'Content-Type': 'application/json'}

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
            "Telefone": cliente.telefone
        },
        "Produtos": [
            {
                "HashProduto": "e9eaa186-f11e-4a08-9f22-387c6c60e035"
            }
        ]
    }

def salvar_venda(cliente):
    endpoint = 'https://apiconsulti.gestaoar.com.br/consultibrasil/api/GarAPIs/'
    apiKey = "e5aaffae75484e138cd1685e2f486b54452edf0e867a4fda8e7bdd8f16b92502"
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
    



def obter_disponibilidade_agenda():
    url = 'https://apiconsulti.gestaoar.com.br/consultibrasil/api/GarAPIs/ObterDisponibilidadeAgenda'
    headers = {"Content-Type": "application/json"}
    payload = {
       "apiKey": "e5aaffae75484e138cd1685e2f486b54452edf0e867a4fda8e7bdd8f16b92502",
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
    url = 'https://apiconsulti.gestaoar.com.br/consultibrasil/api/GarAPIs/AgendarPedido'
    headers = {"Content-Type": "application/json"}
    payload = { 
        "apiKey": "e5aaffae75484e138cd1685e2f486b54452edf0e867a4fda8e7bdd8f16b92502",
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
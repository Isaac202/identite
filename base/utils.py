import requests
import json
from cryptography.fernet import Fernet
from django.conf import settings

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
            "Complemento":cliente.complementp,
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
    response = requests.post(
            f"{endpoint}/Comprar", json.dumps(payload), headers=headers)

    if response.status_code == 200:
        payload = {
        "apiKey": apiKey,
        "Pedido": response["Produtos"][0]["Pedido"],
        "CNPJ": cliente.cnpj, 
        "CPF": cliente.cpf,
        "DataNascimento":cliente.data_nacimento ,#"1987-12-31",
        "IsPossuiCNH": True if cliente.carteira_identidade else False
        }
        response_emissao_protocolo = requests.post(
            f"{endpoint}/EmitirProtocolo", json.dumps(payload), headers=headers)
        if response_emissao_protocolo.status_code == 200:
            return response_emissao_protocolo.json()
        return response.json()
    return response.json()
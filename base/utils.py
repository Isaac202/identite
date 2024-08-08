from django.shortcuts import redirect
import requests
import json
from cryptography.fernet import Fernet
from django.conf import settings
import random
import string
from base.models import DadosCliente, Pedidos, Voucher

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
            "CEP": cliente.cep.replace("-", ""),
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
                pedido = response_data["Produtos"][0]["Pedido"]
        
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
        "DataFinal": "2024-08-29",
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
    
def create_client_and_order(cnpj, voucher):
    # Obter dados da empresa pelo CNPJ
    cnpj = cnpj.replace(".", "").replace("-", "").replace("/", "")
    empresa_data = fetch_empresa_data(cnpj)

    if not empresa_data:
       
        return None
    
    # Obter dados de endereço pelo CEP
    cep = empresa_data.get('cep')
    cep = cep.replace(".", "").replace("-", "").replace(" ", "")
    endereco_data = get_address_data(cep)
    if not endereco_data:
        return None, {'error': 'Dados de endereço não encontrados'}, 404

    # Criar um novo pedido
    novo_pedido = Pedidos(
        pedido=generate_random_code(),  # Você pode ajustar como deseja gerar o código do pedido
        status='13'  # Atribuído a Voucher
    )
    novo_pedido.save()

    # Preparar dados do cliente
    nome_completo = empresa_data.get('razao') or 'N/A'
    nome_fantasia = empresa_data.get('fantasia') or 'N/A'
    razao_social = empresa_data.get('razao') or 'N/A'
    logradouro = endereco_data.get('logradouro') or 'N/A'
    complemento = endereco_data.get('complemento', '')
    bairro = endereco_data.get('bairro') or 'N/A'
    cidade = endereco_data.get('localidade') or 'N/A'
    uf = endereco_data.get('uf') or 'N/A'
    cod_ibge = endereco_data.get('ibge') or 'N/A'
    numero = 'SN'
    voucher = Voucher.objects.get(code=voucher)
    # Criar um novo cliente
    novo_cliente = DadosCliente(
        nome_completo=nome_completo,
        nome_fantasia=nome_fantasia,
        razao_social=razao_social,
        cnpj=cnpj,
        cep=cep or '40110-100',  # Substitua por um valor padrão se necessário
        logradouro=logradouro,
        complemento=complemento,
        bairro=bairro,
        numero=numero,
        cidade=cidade,
        uf=uf,
        cod_ibge=cod_ibge,  # Adicionando o código do IBGE
        pedido=novo_pedido,  # Associar o pedido ao cliente
        voucher=voucher
    )
    novo_cliente.save()
    
    # Inativa o voucher
    voucher.is_valid = False
    voucher.save()

    return novo_cliente, None, None

def consultar_status_pedido(pedido):
    endpont = f'{url}/api/GarAPIs/ConsultaPedidoProtocolo'
    headers = {"Content-Type": "application/json"}
    payload = { 
                "apiKey": API_KEY,
                "Pedido": pedido,
                "Protocolo": ""
    }
    print(pedido)
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

def get_address_data(cep):
    response = requests.get(f'https://viacep.com.br/ws/{cep}/json/')
    if response.status_code == 200:
        return response.json()
    return None

def verifica_se_pode_videoconferecias(cliente):
    # Verifique se o pedido pode ser videoconferido
    endpoint = f'{url}/api/GarAPIs/PsBio'
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

def fetch_empresa_data(cnpj):
    CPFCNPJ_API_KEY = settings.CPFCNPJ
    if cnpj and len(cnpj) == 14:
        response = requests.get(f'https://api.cpfcnpj.com.br/{CPFCNPJ_API_KEY}/5/{cnpj}')
        if response.status_code == 200:
            data = response.json()
            if "erro" in data:
                return None
            return {
                'razao': data.get('razao'),
                'fantasia': data.get('fantasia'),
                'cep': data.get('matrizEndereco', {}).get('cep'),
                # Adicione aqui outros campos que você deseja retornar
            }
    return None
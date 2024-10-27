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
    HashVendedor = "01d6e9ff-3b53-4ba4-b9a7-f0ea9c9d4157"
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
        "Cliente": {
            "CNPJCPF": cliente.cpf if cliente.voucher.tipo == 'ECPF' else cliente.cnpj,
            "NomeRazaoSocial": cliente.nome_completo if cliente.voucher.tipo == 'ECPF' else cliente.razao_social,
            "NomeFantasia": cliente.nome_completo if cliente.voucher.tipo == 'ECPF' else cliente.nome_fantasia,
            "Email": cliente.email,
            "CEP": cliente.cep.replace("-", ""),
            "Logradouro": cliente.logradouro,
            "Numero": cliente.numero,
            "Complemento": cliente.complemento,
            "Bairro": cliente.bairro,
            "Cidade": cliente.cidade,
            "UF": cliente.uf,
            "CodigoIBGE": cliente.cod_ibge,
            "DDD": cliente.telefone[0:2],
            "Telefone": cliente.telefone[2:]
        },
        "Produtos": [
            {
                "HashProduto": "e9eaa186-f11e-4a08-9f22-387c6c60e035" if cliente.voucher.tipo == 'ECNPJ' else "HASH_DO_PRODUTO_ECPF"
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
                    return None, erro["Ocorrencia"]
            else:
                pedido = response_data["Produtos"][0]["Pedido"]
                return pedido, None
        except json.JSONDecodeError:
            return None, "Erro ao decodificar a resposta JSON"
    else:
        return None, f"Erro na requisição: status {response.status_code}"



def gerar_protocolo(pedido, cnpj_cpf, cpf, data_nascimento, is_possui_cnh):
    endpoint = f'{url}/api/GarAPIs/'
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    payload = {
        "apiKey": API_KEY,
        "Pedido": pedido,
        "CPF": cpf,
        "DataNascimento": data_nascimento,
        "IsPossuiCNH": is_possui_cnh
    }
    print(payload)
    # Adiciona CNPJ ou CPF dependendo do comprimento
    if len(cnpj_cpf) == 14:
        payload["CNPJ"] = cnpj_cpf
    else:
        payload["CPF"] = cnpj_cpf

    try:
        response = requests.post(
            f'{endpoint}EmitirProtocolo', 
            json=payload,  # Usar json em vez de data para serialização automática
            headers=headers,
            timeout=30  # Adicionar timeout para evitar esperas infinitas
        )
        
        response.raise_for_status()  # Levanta exceção para status codes de erro
        
        response_data = response.json()
        if 'ErrorCode' in response_data:
            erros = [erro['ErrorDescription'] for erro in response_data if 'ErrorDescription' in erro]
            return None, erros
        
        return response_data, None
        
    except requests.Timeout:
        return None, ["Tempo limite excedido ao tentar gerar o protocolo"]
    except requests.RequestException as e:
        return None, [f"Erro na requisição: {str(e)}"]
    except json.JSONDecodeError:
        return None, ["Erro ao processar resposta do servidor"]
    except Exception as e:
        return None, [f"Erro inesperado: {str(e)}"]
    



def obter_disponibilidade_agenda():
    endpoint = f'{url}/api/GarAPIs/ObterDisponibilidadeAgenda'
    headers = {"Content-Type": "application/json"}
    payload = {
       "apiKey": API_KEY,
        "DataInicial": "2024-06-27",
        "DataFinal": "2024-10-29",
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
    
def create_client_and_order(identificacao, voucher, cep=None):
    # Limpar a identificação (CPF ou CNPJ)
    identificacao = identificacao.replace(".", "").replace("-", "").replace("/", "")
    
    # Obter o objeto Voucher
    voucher = Voucher.objects.get(code=voucher)
    
    # Criar um novo pedido
    novo_pedido = Pedidos(
        pedido=generate_random_code(),
        status='13'  # Atribuído a Voucher
    )
    novo_pedido.save()

    # Inicializar novo_cliente com campos básicos
    novo_cliente = DadosCliente(
        pedido=novo_pedido,
        voucher=voucher
    )

    if voucher.tipo == 'ECNPJ':
        # Buscar dados da empresa
        dados = fetch_empresa_data(identificacao)
        if dados:
            novo_cliente.nome_completo = dados.get('razao') or 'N/A'
            novo_cliente.nome_fantasia = dados.get('fantasia') or 'N/A'
            novo_cliente.razao_social = dados.get('razao') or 'N/A'
            novo_cliente.cnpj = identificacao
            cep = cep or dados.get('cep')
        else:
            return None, {'error': 'Dados da empresa não encontrados'}, 404
    else:  # ECPF
        novo_cliente.cpf = identificacao
        # Usamos o CEP fornecido como parâmetro
        cep = cep

    # Se temos CEP, buscar dados de endereço
    if cep:
        cep = cep.replace(".", "").replace("-", "").replace(" ", "")
        endereco_data = get_address_data(cep)
        if endereco_data:
            novo_cliente.cep = cep
            novo_cliente.logradouro = endereco_data.get('logradouro') or 'N/A'
            novo_cliente.complemento = endereco_data.get('complemento', '')
            novo_cliente.bairro = endereco_data.get('bairro') or 'N/A'
            novo_cliente.numero = 'SN'
            novo_cliente.cidade = endereco_data.get('localidade') or 'N/A'
            novo_cliente.uf = endereco_data.get('uf') or 'N/A'
            novo_cliente.cod_ibge = endereco_data.get('ibge') or 'N/A'
    else:
        # Se não temos CEP, deixamos os campos de endereço vazios
        novo_cliente.cep = ''
        novo_cliente.logradouro = ''
        novo_cliente.bairro = ''
        novo_cliente.cidade = ''
        novo_cliente.uf = ''
        novo_cliente.cod_ibge = ''
    
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
    print("data", data)
    # Retorna True se data['IsOk'] for True ou se cliente.possui_cnh for True
    # Retorna False apenas se ambos forem False
    return data.get('IsOk', False) or cliente.possui_cnh

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
            }
    return None

# Remover ou comentar a função fetch_pessoa_data, já que não será utilizada
# def fetch_pessoa_data(cpf):
#     pass

def verificar_agendamento(hash_venda):
    endpoint = f'{url}/api/GarAPIs/VerificarAgendamento'
    headers = {"Content-Type": "application/json"}
    payload = {
        "apiKey": API_KEY,
        "HashVenda": hash_venda
    }

    response = requests.post(endpoint, json=payload, headers=headers)
    if response.status_code == 200:
        try:
            response_data = response.json()
            return response_data, None
        except json.decoder.JSONDecodeError:
            return None, ["JSONDecodeError: A resposta não é um JSON válido"]
    else:
        return None, [f"Erro: A requisição retornou o status {response.status_code}"]


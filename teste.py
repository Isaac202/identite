import os
import django
from datetime import datetime

# Defina a variável de ambiente
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')  # Altere 'seu_projeto' para o nome do seu projeto

# Configure o Django
django.setup()

from base.models import DadosCliente, Pedidos
from base.task import get_key_by_value
from base.utils import consultar_status_pedido
from django.db.models import Q
# Intervalo de datas
data_inicio = datetime(2024, 9, 1)
data_fim = datetime(2024, 10, 1)

def update_status_celery():
    # Filtra clientes com status 5 e que foram atualizados entre as datas especificadas
    status_validos = [choice[0] for choice in Pedidos.STATUS_CHOICES]
    clientes = DadosCliente.objects.filter(
         pedido__status=6
    )
    print(clientes.count())
    clientes_to_update = []
    
    # Mapeamento dos status da API para os status do modelo
    status_mapping = {
        'Não Confirmada': '1',
        'Solicitação de Estorno': '2',
        'Estornada': '3',
        'Emissão liberada': '4',
        'Protocolo Gerado': '5',
        'Emitida': '6',
        'Revogada': '7',
        'Em Verificação': '8',
        'Em Validação': '9',
        'Recusada': '10',
        'Cancelada': '11',
        'Atribuído a Voucher': '12'
    }
    
    for cliente in clientes:
        try:
            # Verifica se o cliente tem os atributos necessários
            if not hasattr(cliente, 'pedido'):
                print(f"Cliente {cliente.id} não tem pedido associado")
                continue
                
            cliente_documento = cliente.cnpj or cliente.cpf
            if not cliente_documento:
                print(f"Cliente {cliente.id} não tem documento (CPF/CNPJ)")
                continue

            response_data, error = consultar_status_pedido(cliente_documento)
            
            if error:
                print(f"Erro ao consultar cliente {cliente_documento}: {error}")
                continue
                
            if not response_data or not response_data.get("PossuiPedidosVinculados"):
                print(f"Sem pedidos vinculados para o cliente {cliente_documento}")
                continue

            pedidos = response_data.get("Pedidos", [])
            if not pedidos:
                print(f"Lista de pedidos vazia para o cliente {cliente_documento}")
                continue
                
            # Primeiro tenta encontrar um pedido emitido
            pedido_atualizar = next(
                (pedido for pedido in pedidos if pedido.get("StatusPedido") == "Emitida"),
                None
            )
            
            # Se não encontrar pedido emitido, pega o mais recente por data
            if not pedido_atualizar:
                try:
                    pedido_atualizar = max(
                        pedidos,
                        key=lambda x: datetime.strptime(x.get("DataVenda", "2000-01-01T00:00:00.000"), "%Y-%m-%dT%H:%M:%S.%f")
                    )
                except (ValueError, TypeError) as e:
                    print(f"Erro ao processar data do pedido para cliente {cliente_documento}: {e}")
                    continue

            # Verifica se o pedido tem todos os campos necessários
            required_fields = ["Pedido", "Protocolo", "HashVenda", "StatusPedido"]
            if not all(pedido_atualizar.get(field) for field in required_fields):
                print(f"Pedido incompleto para cliente {cliente_documento}")
                continue

          
                # Atualiza todos os campos do pedido com valores default caso necessário
            cliente.pedido.pedido = pedido_atualizar.get("Pedido", "")
            cliente.pedido.protocolo = pedido_atualizar.get("Protocolo", "")
            cliente.pedido.hashVenda = pedido_atualizar.get("HashVenda", "")
            cliente.pedido.status = status_mapping.get(
                pedido_atualizar.get("StatusPedido", "Não Confirmada"),
                '1'  # default status
            )
            clientes_to_update.append(cliente.pedido)

        except Exception as e:
            print(f"Erro inesperado ao processar cliente {getattr(cliente, 'id', 'unknown')}: {str(e)}")
            continue

    # Atualiza todos os pedidos modificados de uma vez
    try:
        if clientes_to_update:
            Pedidos.objects.bulk_update(clientes_to_update, ['pedido', 'protocolo', 'hashVenda', 'status'])
            print(f"Atualizados {len(clientes_to_update)} pedidos com sucesso")
    except Exception as e:
        print(f"Erro ao realizar bulk update: {str(e)}")

update_status_celery()
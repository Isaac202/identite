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

# Intervalo de datas
data_inicio = datetime(2024, 9, 1)
data_fim = datetime(2024, 9, 25)
status_dict = {
    '1': 'Não Confirmada',
    '2': 'Solicitação de Estorno',
    '3': 'Estornada',
    '4': 'Emissão liberada',
    '5': 'Protocolo Gerado',
    '6': 'Emitida',
    '7': 'Revogada',
    '8': 'Em Verificação',
    '9': 'Em Validação',
    '10': 'Recusada',
    '11': 'Cancelada',
    '12': 'Atribuído a Voucher'
}

def update_status_celery():
    # Filtra clientes com status 5 e que foram atualizados entre as datas especificadas
    clientes = DadosCliente.objects.filter(
       
        updated_at__gte=data_inicio,
        updated_at__lte=data_fim
    )
    print(clientes.count())
    clientes_to_update = []
    for cliente in clientes:
        status, error = consultar_status_pedido(cliente.pedido.pedido)
        status_dict = dict(Pedidos.STATUS_CHOICES)
    
        
        if "StatusPedido" in status:
            status_key = get_key_by_value(status_dict, status["StatusPedido"])
            cliente.pedido.status = status_key
            clientes_to_update.append(cliente.pedido)

    # Atualiza todos os pedidos modificados de uma vez
    Pedidos.objects.bulk_update(clientes_to_update, ['status'])
    
update_status_celery()
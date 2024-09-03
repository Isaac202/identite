import os
import django

# Defina a variável de ambiente
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')  # Altere 'seu_projeto' para o nome do seu projeto

# Configure o Django
django.setup()

from base.models import DadosCliente, Pedidos
from base.task import get_key_by_value
from base.utils import consultar_status_pedido
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
    clientes = DadosCliente.objects.filter(pedido__status='5')
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
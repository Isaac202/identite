import logging
import base64
from celery import shared_task
from django.core.files.base import ContentFile

from base.utils import consultar_status_pedido
from .models import DadosCliente, Pedidos


def get_key_by_value(dictionary, value):
    for key, val in dictionary.items():
        if val == value:
            return key
logger = logging.getLogger('celery')

@shared_task
def salvar_arquivos_cliente(id_cliente, rg_frente_b64=None, rg_verso_b64=None, cnh_b64=None):
    try:
        logger.info("Iniciando tarefa salvar_arquivos_cliente para o cliente %s", id_cliente)
        cliente = DadosCliente.objects.get(id=id_cliente)
        logger.debug("Dados do cliente recuperados: %s", cliente)
        
        # Decodificando os arquivos
        if rg_frente_b64:
            rg_frente = base64.b64decode(rg_frente_b64)
            cliente.rg_frente.save('rg_frente.jpg', ContentFile(rg_frente))
            logger.debug("RG frente salvo para o cliente %s", id_cliente)
        
        if rg_verso_b64:
            rg_verso = base64.b64decode(rg_verso_b64)
            cliente.rg_verso.save('rg_verso.jpg', ContentFile(rg_verso))
            logger.debug("RG verso salvo para o cliente %s", id_cliente)
        
        if cnh_b64:
            cnh = base64.b64decode(cnh_b64)
            cliente.carteira_habilitacao.save('cnh.jpg', ContentFile(cnh))
            logger.debug("CNH salvo para o cliente %s", id_cliente)
        
        cliente.save()
        logger.info("Cliente %s salvo com sucesso", id_cliente)
        
        return cliente.id  # Retornando um valor simples para logging
    except Exception as e:
        logger.error("Erro ao salvar arquivos para o cliente %s: %s", id_cliente, str(e))
        raise

    
@shared_task
def update_status_celery(cliente_ids):
    clientes = DadosCliente.objects.filter(id__in=cliente_ids, pedido__status='5')
    print(f"Atualizando {clientes.count()} clientes")
    clientes_to_update = []
    for cliente in clientes:
        status, error = consultar_status_pedido(cliente.pedido.pedido)
        status_dict = dict(Pedidos.STATUS_CHOICES)
        if "StatusPedido" in status:
            status_key = get_key_by_value(status_dict, status["StatusPedido"])
            if cliente.pedido.status != status_key:
                cliente.pedido.status = status_key
                clientes_to_update.append(cliente.pedido)

    # Atualiza todos os pedidos modificados de uma vez
    Pedidos.objects.bulk_update(clientes_to_update, ['status'])
    print(f"Atualizados {len(clientes_to_update)} clientes")
    return f"Atualizados {len(clientes_to_update)} de {clientes.count()} clientes"
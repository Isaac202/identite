import logging
import base64
from celery import shared_task
from django.core.files.base import ContentFile
from datetime import datetime

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
            cliente_documento = cliente.cnpj or cliente.cpf
            response_data, error = consultar_status_pedido(cliente_documento)
            
            if error or not response_data or not response_data.get("PossuiPedidosVinculados"):
                continue

            pedidos = response_data.get("Pedidos", [])
            if not pedidos:
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
                except (ValueError, TypeError):
                    continue

            # Verifica se o pedido tem todos os campos necessários
            required_fields = ["Pedido", "Protocolo", "HashVenda", "StatusPedido"]
            if not all(pedido_atualizar.get(field) for field in required_fields):
                continue

            # Atualiza todos os campos do pedido
            cliente.pedido.pedido = pedido_atualizar.get("Pedido", "")
            cliente.pedido.protocolo = pedido_atualizar.get("Protocolo", "")
            cliente.pedido.hashVenda = pedido_atualizar.get("HashVenda", "")
            cliente.pedido.status = status_mapping.get(
                pedido_atualizar.get("StatusPedido", "Não Confirmada"),
                '1'  # default status
            )
            clientes_to_update.append(cliente.pedido)

        except Exception as e:
            logger.error(f"Erro ao processar cliente {cliente.id}: {str(e)}")
            continue

    # Atualiza todos os pedidos modificados de uma vez
    if clientes_to_update:
        Pedidos.objects.bulk_update(clientes_to_update, ['pedido', 'protocolo', 'hashVenda', 'status'])
        print(f"Atualizados {len(clientes_to_update)} clientes")
    
    return f"Atualizados {len(clientes_to_update)} de {clientes.count()} clientes"
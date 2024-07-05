import logging
import base64
from celery import shared_task
from django.core.files.base import ContentFile
from .models import DadosCliente

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

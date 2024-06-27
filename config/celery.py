from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Define o módulo de configuração padrão do Django para o programa 'celery'.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

# Usa a string de configuração do Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Carrega automaticamente qualquer tarefa definida em seus aplicativos Django INSTALLED_APPS
app.autodiscover_tasks()
from django.urls import path
from .views import cadastrar_venda

urlpatterns = [
    path('cadastrar-venda/', cadastrar_venda, name='cadastrar_venda'),
    # outras urls...
]
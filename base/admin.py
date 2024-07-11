from django.contrib import admin
from .models import DadosCliente, Pedidos, Voucher

admin.site.register(Voucher)
admin.site.register(Pedidos)
class DadosClienteAdmin(admin.ModelAdmin):
    search_fields = ['nome_completo', 'cpf']

admin.site.register(DadosCliente, DadosClienteAdmin)
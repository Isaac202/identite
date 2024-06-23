from django.contrib import admin
from .models import DadosCliente, Pedidos, Voucher

admin.site.register(Voucher)
admin.site.register(Pedidos)
admin.site.register(DadosCliente)
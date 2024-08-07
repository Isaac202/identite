from django.contrib import admin
from .models import DadosCliente, Pedidos, Voucher
from django.db.models import Count

admin.site.register(Pedidos)

class VoucherAdmin(admin.ModelAdmin):
    search_fields= ['code']
    list_display = ['code','is_valid']

class DadosClienteAdmin(admin.ModelAdmin):
    list_display = ['nome_completo', 'get_pedido', 'get_protocolo', 'get_status','voucher','cpf', 'cnpj', 'created_at', 'updated_at']
    search_fields = ['nome_completo','pedido__pedido' ,'cpf', 'cnpj', 'voucher__code']
    list_filter = ['pedido__status', ('created_at', admin.DateFieldListFilter), ('updated_at', admin.DateFieldListFilter)]
    
    def get_pedido(self, obj):
        return obj.pedido.pedido
   
    
    def get_status(self, obj):
      return obj.pedido.get_status_display()
    def get_protocolo(self, obj):
        return obj.pedido.protocolo
    get_protocolo.short_description = 'Protocolo'
    get_pedido.short_description = 'Pedido'  # Define um título para a coluna
    get_status.short_description = 'Status'  # Define um título para a coluna
    def changelist_view(self, request, extra_context=None):
        # Obtenha a contagem total de clientes
        total_clientes = DadosCliente.objects.count()

        # Obtenha a contagem de clientes por status do pedido
        clientes_por_status = DadosCliente.objects.values('pedido__status').annotate(total=Count('id'))

        # Adicione as estatísticas ao contexto
        extra_context = extra_context or {}
        extra_context['total_clientes'] = total_clientes
        extra_context['clientes_por_status'] = clientes_por_status

        return super(DadosClienteAdmin, self).changelist_view(request, extra_context=extra_context)

admin.site.register(DadosCliente, DadosClienteAdmin)
admin.site.register(Voucher,VoucherAdmin)
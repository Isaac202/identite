from django.contrib import admin
from .models import DadosCliente, Pedidos, Voucher
from django.db.models import Count

admin.site.register(Voucher)
admin.site.register(Pedidos)



class DadosClienteAdmin(admin.ModelAdmin):
    list_display = ['nome_completo', 'get_pedido', 'get_status','cpf', 'cnpj', 'created_at', 'updated_at']
    search_fields = ['nome_completo', 'cpf', 'cnpj']
    list_filter = ['pedido__status', ('created_at', admin.DateFieldListFilter), ('updated_at', admin.DateFieldListFilter)]

    def get_pedido(self, obj):
        return obj.pedido.pedido
    def get_status(self, obj):
        return obj.pedido.status
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
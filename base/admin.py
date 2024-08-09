from django.contrib import admin
from .models import DadosCliente, Pedidos, Voucher
from django.db.models import Count
import openpyxl
from django.utils import timezone
from django.http import HttpResponse

admin.site.register(Pedidos)

class VoucherAdmin(admin.ModelAdmin):
    search_fields= ['code']
    list_display = ['code','is_valid']


class DadosClienteAdmin(admin.ModelAdmin):
    list_display = ['nome_completo', 'get_pedido', 'get_protocolo', 'get_status', 'voucher', 'cpf', 'cnpj', 'created_at', 'updated_at']
    search_fields = ['nome_completo', 'razao_social','pedido__pedido', 'cpf', 'cnpj', 'voucher__code']
    list_filter = ['pedido__status', ('created_at', admin.DateFieldListFilter), ('updated_at', admin.DateFieldListFilter)]
    actions = ['exportar_dados_para_excel']

    def get_pedido(self, obj):
        return obj.pedido.pedido

    def get_status(self, obj):
        return obj.pedido.get_status_display()

    def get_protocolo(self, obj):
        return obj.pedido.protocolo
    
    get_protocolo.short_description = 'Protocolo'
    get_pedido.short_description = 'Pedido'  # Define um título para a coluna
    get_status.short_description = 'Status'  # Define um título para a coluna

    def exportar_dados_para_excel(self, request, queryset):
        # Criar um workbook e uma planilha
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = 'Dados Clientes'

        # Cabeçalhos
        headers = ['Nome', 'CNPJ', 'razao_social','Voucher', 'Data de Atualização']
        sheet.append(headers)

        # Adicionar os dados dos clientes selecionados
        for cliente in queryset:
            # Remover o fuso horário de updated_at, se necessário
            updated_at = cliente.updated_at
            if updated_at.tzinfo is not None:
                updated_at = updated_at.replace(tzinfo=None)

            sheet.append([
                cliente.nome_completo,
                cliente.cnpj,
                cliente.razao_social,
                cliente.voucher.code if cliente.voucher else '',
                updated_at.strftime('%Y-%m-%d %H:%M:%S') if updated_at else ''
            ])

        # Criar um objeto HttpResponse com o conteúdo do arquivo Excel
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="dados_clientes.xlsx"'
        
        workbook.save(response)  # Salvar o workbook na resposta
        return response

    exportar_dados_para_excel.short_description = 'Exportar dados para Excel'

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

# Registrar o modelo e a classe do admin
admin.site.register(DadosCliente, DadosClienteAdmin)

admin.site.register(Voucher,VoucherAdmin)
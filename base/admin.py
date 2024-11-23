from django.contrib import admin
from .models import DadosCliente, Pedidos, Voucher
from django.db.models import Count
import openpyxl
from django.utils import timezone
from django.http import HttpResponse

class SoftDeleteAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        # Retorna apenas objetos ativos por padrão
        return self.model.objects.filter(is_active=True)

    actions = ['soft_delete_selected', 'restore_selected']

    def soft_delete_selected(self, request, queryset):
        for obj in queryset:
            obj.soft_delete()
        self.message_user(request, f"{queryset.count()} itens foram marcados como deletados.")
    soft_delete_selected.short_description = "Deletar itens selecionados (soft delete)"

    def restore_selected(self, request, queryset):
        for obj in queryset:
            obj.restore()
        self.message_user(request, f"{queryset.count()} itens foram restaurados.")
    restore_selected.short_description = "Restaurar itens selecionados"

@admin.register(Pedidos)
class PedidosAdmin(SoftDeleteAdmin):
    list_display = ('pedido', 'protocolo', 'status', 'created_at', 'is_active')
    list_filter = ('status', 'is_active')
    search_fields = ('pedido', 'protocolo')

@admin.register(Voucher)
class VoucherAdmin(SoftDeleteAdmin):
    list_display = ('code', 'tipo', 'is_valid', 'lote', 'created_at', 'is_active')
    list_filter = ('tipo', 'is_valid', 'created_at', 'is_active')
    search_fields = ('code',)
    ordering = ('-created_at',)

class DadosClienteAdmin(SoftDeleteAdmin):
    list_display = ['nome_completo', 'get_pedido', 'get_protocolo', 'get_status', 
                   'voucher', 'cpf', 'cnpj', 'created_at', 'updated_at', 'is_active']
    search_fields = ['nome_completo', 'razao_social', 'pedido__pedido', 'cpf', 'cnpj', 'voucher__code']
    list_filter = ['pedido__status', ('created_at', admin.DateFieldListFilter), 
                  ('updated_at', admin.DateFieldListFilter), 'is_active']
    actions = ['exportar_dados_para_excel', 'soft_delete_selected', 'restore_selected']

    def get_pedido(self, obj):
        return obj.pedido.pedido if obj.pedido else None

    def get_status(self, obj):
        return obj.pedido.get_status_display() if obj.pedido else None

    def get_protocolo(self, obj):
        return obj.pedido.protocolo if obj.pedido else None
    
    get_protocolo.short_description = 'Protocolo'
    get_pedido.short_description = 'Pedido'
    get_status.short_description = 'Status'

    def exportar_dados_para_excel(self, request, queryset):
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = 'Dados Clientes'
        
        headers = ['Nome', 'CNPJ', 'razao_social', 'Voucher', 'Data de Atualização', 'Status']
        sheet.append(headers)

        for cliente in queryset:
            updated_at = cliente.updated_at
            if updated_at and updated_at.tzinfo is not None:
                updated_at = updated_at.replace(tzinfo=None)

            sheet.append([
                cliente.nome_completo,
                cliente.cnpj,
                cliente.razao_social,
                cliente.voucher.code if cliente.voucher else '',
                updated_at.strftime('%Y-%m-%d %H:%M:%S') if updated_at else '',
                self.get_status(cliente) or ''
            ])

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="dados_clientes.xlsx"'
        workbook.save(response)
        return response

    exportar_dados_para_excel.short_description = 'Exportar dados para Excel'

admin.site.register(DadosCliente, DadosClienteAdmin)


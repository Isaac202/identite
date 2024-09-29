from django_filters import rest_framework as filters
from base.models import Lote, Voucher, Pedidos, DadosCliente, Agendamento, Slots

class LoteFilter(filters.FilterSet):
    class Meta:
        model = Lote
        fields = ['numero', 'created_at']

class VoucherFilter(filters.FilterSet):
    created_at = filters.DateFromToRangeFilter()
    is_valid = filters.BooleanFilter()
    lote_numero = filters.NumberFilter(field_name='lote__numero')

    class Meta:
        model = Voucher
        fields = ['is_valid', 'lote_numero', 'created_at']

class PedidosFilter(filters.FilterSet):
    class Meta:
        model = Pedidos
        fields = ['status', 'created_at']

class DadosClienteFilter(filters.FilterSet):
    pedido__status = filters.ChoiceFilter(choices=Pedidos.STATUS_CHOICES)
    voucher__is_valid = filters.BooleanFilter()

    class Meta:
        model = DadosCliente
        fields = ['pedido__status', 'voucher__is_valid', 'created_at']

class AgendamentoFilter(filters.FilterSet):
    class Meta:
        model = Agendamento
        fields = ['pedido__status', 'data', 'hora', 'created_at']

class SlotsFilter(filters.FilterSet):
    class Meta:
        model = Slots
        fields = ['hashSlot', 'created_at']
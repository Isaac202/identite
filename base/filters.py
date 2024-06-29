import django_filters
from .models import DadosCliente
from .models import Voucher

class VoucherFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(field_name="created_at", lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name="created_at", lookup_expr='lte')

    class Meta:
        model = Voucher
        fields = ['start_date', 'end_date']


class DadosClienteFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(field_name="created_at", lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name="created_at", lookup_expr='lte')
    #cnpj = django_filters.CharFilter(field_name="cnpj", lookup_expr='icontains')

    class Meta:
        model = DadosCliente
        fields = ['start_date', 'end_date']
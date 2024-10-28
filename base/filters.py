import django_filters
from django import forms
from .models import DadosCliente, Pedidos
from .models import Voucher

class VoucherFilter(django_filters.FilterSet):
    tipo = django_filters.ChoiceFilter(
        choices=Voucher.TIPO_CHOICES,
        empty_label="Todos",
        method='filter_tipo'
    )

    def filter_tipo(self, queryset, name, value):
        if value:
            return queryset.filter(tipo=value)
        return queryset

    class Meta:
        model = Voucher
        fields = ['tipo']

class DadosClienteFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(field_name='created_at', lookup_expr='gte', widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = django_filters.DateFilter(field_name='created_at', lookup_expr='lte', widget=forms.DateInput(attrs={'type': 'date'}))
    status = django_filters.ChoiceFilter(field_name='pedido__status', choices=Pedidos.STATUS_CHOICES)
    nome_completo = django_filters.CharFilter(lookup_expr='icontains')
    cnpj = django_filters.CharFilter(lookup_expr='icontains')
    voucher_code = django_filters.CharFilter(field_name='voucher__code', lookup_expr='icontains')

    class Meta:
        model = DadosCliente
        fields = ['start_date', 'end_date', 'status', 'nome_completo', 'cnpj', 'voucher_code']

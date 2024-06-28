# serializers.py
from rest_framework import serializers
from .models import Voucher, DadosCliente

class VoucherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voucher
        fields = '__all__'

class DadosClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = DadosCliente
        fields = '__all__'

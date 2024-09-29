# serializers.py
from rest_framework import serializers
from base.models import Lote, Voucher, Pedidos, DadosCliente, Agendamento, Slots

class LoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lote
        fields = ['id', 'numero', 'created_at']  # Adicione outros campos relevantes do Lote

class VoucherSerializer(serializers.ModelSerializer):
    lote = LoteSerializer(read_only=True)
    lote_id = serializers.PrimaryKeyRelatedField(
        queryset=Lote.objects.all(), source='lote', write_only=True
    )

    class Meta:
        model = Voucher
        fields = ['id', 'code', 'is_valid', 'created_at', 'lote', 'lote_id']  # Adicione 'lote_id' aqui
        read_only_fields = ['created_at', 'updated_at']

    def create(self, validated_data):
        lote = validated_data.pop('lote', None)
        voucher = Voucher.objects.create(lote=lote, **validated_data)
        return voucher

    def update(self, instance, validated_data):
        lote = validated_data.pop('lote', None)
        if lote is not None:
            instance.lote = lote
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class PedidosSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Pedidos
        fields = ['id', 'pedido', 'protocolo', 'hashVenda', 'status', 'status_display', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class DadosClienteSerializer(serializers.ModelSerializer):
    pedido = PedidosSerializer(read_only=True)
    pedido_id = serializers.PrimaryKeyRelatedField(
        queryset=Pedidos.objects.all(), source='pedido', write_only=True
    )
    voucher = VoucherSerializer(read_only=True)
    voucher_id = serializers.PrimaryKeyRelatedField(
        queryset=Voucher.objects.all(), source='voucher', write_only=True
    )

    class Meta:
        model = DadosCliente
        fields = [
            'id', 'nome_completo', 'nome_fantasia', 'razao_social', 'cpf', 'cnpj',
            'email', 'cep', 'logradouro', 'numero', 'complemento', 'bairro',
            'cidade', 'uf', 'cod_ibge', 'telefone', 'data_nacimento',
            'rg_frente', 'rg_verso', 'carteira_habilitacao',
            'pedido', 'pedido_id', 'voucher', 'voucher_id',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class AgendamentoSerializer(serializers.ModelSerializer):
    pedido = PedidosSerializer(read_only=True)
    pedido_id = serializers.PrimaryKeyRelatedField(
        queryset=Pedidos.objects.all(), source='pedido', write_only=True
    )

    class Meta:
        model = Agendamento
        fields = ['id', 'pedido', 'pedido_id', 'data', 'hora', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class SlotsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slots
        fields = ['id', 'hashSlot', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

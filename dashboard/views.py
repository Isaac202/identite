# views.py
import logging
from requests import Response
from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from base.models import Voucher, Lote, Pedidos, DadosCliente, Agendamento, Slots
from .filters import VoucherFilter, LoteFilter, PedidosFilter, DadosClienteFilter, AgendamentoFilter, SlotsFilter
from .serializers import (
    VoucherSerializer,
    LoteSerializer,
    PedidosSerializer,
    DadosClienteSerializer,
    AgendamentoSerializer,
    SlotsSerializer
)
from django.db.models import F
from rest_framework.permissions import AllowAny

logger = logging.getLogger(__name__)

class VoucherViewSet(viewsets.ModelViewSet):
    queryset = Voucher.objects.all().order_by(F('id').desc(nulls_last=True))
    serializer_class = VoucherSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = VoucherFilter
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        logger.info(f"Iniciando listagem de vouchers. Query params: {request.query_params}")
        queryset = self.filter_queryset(self.get_queryset())
        logger.info(f"Número de vouchers após filtragem: {queryset.count()}")

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            logger.info("Paginação aplicada e serialização concluída")
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        logger.info("Serialização concluída sem paginação")
        return Response(serializer.data)

class LoteViewSet(viewsets.ModelViewSet):
    queryset = Lote.objects.all()
    serializer_class = LoteSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = LoteFilter
    # Removida a linha de permission_classes

class PedidosViewSet(viewsets.ModelViewSet):
    queryset = Pedidos.objects.all()
    serializer_class = PedidosSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = PedidosFilter
    # Removida a linha de permission_classes

class DadosClienteViewSet(viewsets.ModelViewSet):
    queryset = DadosCliente.objects.all()
    serializer_class = DadosClienteSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = DadosClienteFilter
    # Removida a linha de permission_classes

class AgendamentoViewSet(viewsets.ModelViewSet):
    queryset = Agendamento.objects.all()
    serializer_class = AgendamentoSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = AgendamentoFilter
    # Removida a linha de permission_classes

class SlotsViewSet(viewsets.ModelViewSet):
    queryset = Slots.objects.all()
    serializer_class = SlotsSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = SlotsFilter
    # Removida a linha de permission_classes


# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LoteViewSet,
    VoucherViewSet,
    PedidosViewSet,
    DadosClienteViewSet,
    AgendamentoViewSet,
    SlotsViewSet
)

router = DefaultRouter()
router.register(r'lotes', LoteViewSet)
router.register(r'vouchers', VoucherViewSet)
router.register(r'pedidos', PedidosViewSet)
router.register(r'dadosclientes', DadosClienteViewSet)
router.register(r'agendamentos', AgendamentoViewSet)
router.register(r'slots', SlotsViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]

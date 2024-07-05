from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VoucherViewSet, DadosClienteViewSet,agendar_videoconferencia,check_voucher, create_voucher, delete_voucher, edit_voucher, form,agradecimento_orientacao, generate_vouchers,gerar_protocolo_view, list_vouchers, voucher_statistics
from django.contrib.auth import views as auth_views

router = DefaultRouter()
router.register(r'vouchers', VoucherViewSet)
router.register(r'dadosclientes', DadosClienteViewSet)

urlpatterns = [
    path('', check_voucher, name='check_voucher'),
    path("painel/", voucher_statistics, name="painel"),
    path('form/<slug:slug>/', form, name='form'),
    path('api/', include(router.urls)),
    path('vouchers/', list_vouchers, name='vouchers'),
    path('generate_vouchers/', generate_vouchers, name='generate_vouchers'),
    path('agradecimento_orientacao/', agradecimento_orientacao, name='agradecimento_orientacao'),
    path('agendar_videoconferencia/<int:pedido>/', agendar_videoconferencia, name='agendar_videoconferencia'),
    path('gerar_protocolo/<str:pedido>/', gerar_protocolo_view, name='gerar_protocolo'),
    path('create_voucher/', create_voucher, name='create_voucher'),
    path('edit_voucher/<int:id>/', edit_voucher, name='edit_voucher'),
    path('delete_voucher/<int:id>/', delete_voucher, name='delete_voucher'),
     path('login/', auth_views.LoginView.as_view(template_name='home/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]
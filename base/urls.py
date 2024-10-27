from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (VoucherViewSet, DadosClienteViewSet, agendar_videoconferencia, 
                    atualizar_empresa, atualizar_status_individual_view, check_voucher, 
                    consultar_status_view, create_client_and_assign_voucher, create_voucher, 
                    delete_voucher, edit_voucher, empresa_form_view, form, agradecimento_orientacao, 
                    generate_vouchers, gerar_protocolo_view, get_empresa_data, list_vouchers, 
                    update_status, voucher_statistics)
from django.contrib.auth import views as auth_views

router = DefaultRouter()
router.register(r'vouchers', VoucherViewSet)
router.register(r'dadosclientes', DadosClienteViewSet)

urlpatterns = [
    path('', check_voucher, name='check_voucher'),
    path("painel/", voucher_statistics, name="painel"),
    path('form/<slug:slug>/', form, name='form'),
    path('empresa-form/', empresa_form_view, name='empresa_form_view'),
    path('create-client-voucher/', create_client_and_assign_voucher, name='create_client_voucher'),
    path('api/', include(router.urls)),
    path('vouchers/', list_vouchers, name='vouchers'),
    path('get_empresa_data/', get_empresa_data, name='get_empresa_data'),
    path('generate_vouchers/', generate_vouchers, name='generate_vouchers'),
    path('agradecimento_orientacao/', agradecimento_orientacao, name='agradecimento_orientacao'),
    path('agendar_videoconferencia/<int:pedido>/', agendar_videoconferencia, name='agendar_videoconferencia'),
    path('gerar_protocolo/<str:pedido>/', gerar_protocolo_view, name='gerar_protocolo'),
    path('create_voucher/', create_voucher, name='create_voucher'),
    path('edit_voucher/<int:id>/', edit_voucher, name='edit_voucher'),
    path('update_status/<int:pedido_id>/', update_status, name='update_status'),
    path('delete_voucher/<int:id>/', delete_voucher, name='delete_voucher'),
    path('consultar_status/<int:cliente_id>/', consultar_status_view, name='consultar_status'),
    path('atualizar_status_individual/<int:cliente_id>/', atualizar_status_individual_view, name='atualizar_status_individual'),
    path('atualizar/empresa/<str:voucher>/', atualizar_empresa, name='atualizar_empresa'),
    path('login/', auth_views.LoginView.as_view(template_name='home/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]

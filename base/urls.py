from django.urls import path
from .views import agendar_videoconferencia,check_voucher, form,agradecimento_orientacao

urlpatterns = [
    path('', check_voucher, name='check_voucher'),
    path('form/<slug:slug>/', form, name='form'),
    path('agradecimento_orientacao/', agradecimento_orientacao, name='agradecimento_orientacao'),
    path('agendar_videoconferencia/<int:pedido>/', agendar_videoconferencia, name='agendar_videoconferencia'),
    # outras urls...
]
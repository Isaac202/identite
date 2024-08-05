from django import forms
from .models import Voucher

class VoucherForm(forms.ModelForm):
    class Meta:
        model = Voucher
        fields = '__all__'  # ou uma lista dos campos que você deseja incluir




class EmpresaForm(forms.Form):
    cnpj = forms.CharField(label='CNPJ', max_length=18, required=True)
    voucher = forms.CharField(label='Voucher', max_length=20, required=True)
    nome_completo = forms.CharField(label='Nome Completo', max_length=255, required=False)
    nome_fantasia = forms.CharField(label='Nome Fantasia', max_length=255, required=False)
    razao_social = forms.CharField(label='Razão Social', max_length=255, required=False)
    cep = forms.CharField(label='CEP', max_length=9, required=False)
    logradouro = forms.CharField(label='Logradouro', max_length=255, required=False)
    complemento = forms.CharField(label='Complemento', max_length=255, required=False)
    bairro = forms.CharField(label='Bairro', max_length=255, required=False)
    numero = forms.CharField(label='Número', max_length=10, required=False)
    cidade = forms.CharField(label='Cidade', max_length=255, required=False)
    uf = forms.CharField(label='UF', max_length=2, required=False)
    cod_ibge = forms.CharField(label='Código IBGE', max_length=10, required=False)

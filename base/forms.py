from django import forms
from .models import Voucher

class VoucherForm(forms.ModelForm):
    class Meta:
        model = Voucher
        fields = '__all__'  # ou uma lista dos campos que você deseja incluir
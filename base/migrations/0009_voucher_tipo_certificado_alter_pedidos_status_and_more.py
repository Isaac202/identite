# Generated by Django 5.0.6 on 2024-10-03 15:15

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0008_alter_dadoscliente_cpf_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='voucher',
            name='tipo_certificado',
            field=models.CharField(blank=True, choices=[('e-CPF', 'e-CPF'), ('e-CNPJ', 'e-CNPJ')], default='e-CNPJ', max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='pedidos',
            name='status',
            field=models.CharField(blank=True, choices=[('1', 'Não Confirmada'), ('2', 'Solicitação de Estorno'), ('3', 'Estornada'), ('4', 'Emissão liberada'), ('5', 'Protocolo Gerado'), ('6', 'Emitida'), ('7', 'Revogada'), ('8', 'Em Verificação'), ('9', 'Em Validação'), ('10', 'Recusada'), ('11', 'Cancelada'), ('12', 'Atribuído a Voucher')], default='1', max_length=2, null=True),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='code',
            field=models.CharField(max_length=20, unique=True),
        ),
        migrations.AlterField(
            model_name='voucher',
            name='lote',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='base.lote'),
        ),
    ]

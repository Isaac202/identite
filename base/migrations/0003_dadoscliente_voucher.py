# Generated by Django 5.0.6 on 2024-06-22 23:10

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0002_pedidos_alter_voucher_code_dadoscliente'),
    ]

    operations = [
        migrations.AddField(
            model_name='dadoscliente',
            name='voucher',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, to='base.voucher'),
            preserve_default=False,
        ),
    ]
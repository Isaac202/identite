# Generated by Django 5.0.6 on 2024-07-09 19:38

import base.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0002_lote_voucher_lote'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dadoscliente',
            name='carteira_habilitacao',
            field=models.FileField(blank=True, null=True, upload_to=base.models.upload_image_book),
        ),
        migrations.AlterField(
            model_name='dadoscliente',
            name='rg_frente',
            field=models.FileField(blank=True, null=True, upload_to=base.models.upload_image_book),
        ),
        migrations.AlterField(
            model_name='dadoscliente',
            name='rg_verso',
            field=models.FileField(blank=True, null=True, upload_to=base.models.upload_image_book),
        ),
    ]

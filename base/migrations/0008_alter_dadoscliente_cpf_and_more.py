# Generated by Django 5.0.6 on 2024-07-22 00:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0007_alter_pedidos_hashvenda_alter_pedidos_pedido_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dadoscliente',
            name='cpf',
            field=models.CharField(blank=True, max_length=14, null=True),
        ),
        migrations.AlterField(
            model_name='dadoscliente',
            name='data_nacimento',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='dadoscliente',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AlterField(
            model_name='dadoscliente',
            name='telefone',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]

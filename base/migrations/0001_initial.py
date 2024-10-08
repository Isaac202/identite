# Generated by Django 5.0.6 on 2024-06-28 20:20

import base.models
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Pedidos',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('pedido', models.CharField(max_length=255)),
                ('protocolo', models.CharField(max_length=255)),
                ('hashVenda', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Slots',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('hashSlot', models.CharField(max_length=255, unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Voucher',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('code', models.CharField(max_length=255, unique=True)),
                ('is_valid', models.BooleanField(default=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Agendamento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('data', models.CharField(max_length=255)),
                ('hora', models.CharField(max_length=255)),
                ('pedido', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.pedidos')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DadosCliente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('nome_completo', models.CharField(max_length=255)),
                ('nome_fantasia', models.CharField(max_length=255)),
                ('razao_social', models.CharField(max_length=255)),
                ('cpf', models.CharField(max_length=14)),
                ('cnpj', models.CharField(max_length=14)),
                ('email', models.EmailField(max_length=254)),
                ('cep', models.CharField(max_length=14)),
                ('logradouro', models.CharField(max_length=255)),
                ('numero', models.CharField(max_length=10)),
                ('complemento', models.CharField(max_length=255)),
                ('bairro', models.CharField(max_length=255)),
                ('cidade', models.CharField(max_length=255)),
                ('uf', models.CharField(max_length=10)),
                ('cod_ibge', models.CharField(max_length=10)),
                ('telefone', models.CharField(max_length=20)),
                ('data_nacimento', models.CharField(max_length=100)),
                ('rg_frente', models.ImageField(blank=True, null=True, upload_to=base.models.upload_image_book)),
                ('rg_verso', models.ImageField(blank=True, null=True, upload_to=base.models.upload_image_book)),
                ('carteira_habilitacao', models.ImageField(blank=True, null=True, upload_to=base.models.upload_image_book)),
                ('pedido', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.pedidos')),
                ('voucher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.voucher')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]

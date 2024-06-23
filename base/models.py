from django.db import models
from .utils import encrypt_voucher, decrypt_voucher

def upload_image_book(instance, filename):
    return f"documentos_identite/{instance.nome_completo}-{filename}"

class Voucher(models.Model):
    code = models.CharField(max_length=255, unique=True)  # Aumente o tamanho para armazenar o voucher encriptado
    is_valid = models.BooleanField(default=True)

    #def save(self, *args, **kwargs):
     #   if not self.pk:  # Se o objeto ainda não foi salvo no banco de dados
      #      self.code = encrypt_voucher(self.code)
       # super().save(*args, **kwargs)

    #def get_decrypted_code(self):
     #   return decrypt_voucher(self.code)

    def __str__(self):
        return self.code

class Pedidos(models.Model):
    pedido = models.CharField(max_length=255)
    protocolo = models.CharField(max_length=255)

    def __str__(self):
        return f'Numero do Pedido:{self.pedido}'
class DadosCliente(models.Model):
    nome_completo = models.CharField(max_length=255)
    nome_fantasia = models.CharField(max_length=255)
    razao_social = models.CharField(max_length=255)
    cpf = models.CharField(max_length=14)
    cnpj = models.CharField(max_length=14)
    email = models.EmailField()
    cep = models.CharField(max_length=14)
    logradouro = models.CharField(max_length=255)
    numero = models.CharField(max_length=10)
    complemento = models.CharField(max_length=255)
    bairro = models.CharField(max_length=255)
    cidade = models.CharField(max_length=255)
    uf = models.CharField(max_length=10)
    cod_ibge = models.CharField(max_length=10)
    telefone = models.CharField(max_length=20)
    data_nacimento = models.CharField(max_length=100)
    rg_frente = models.ImageField(
        upload_to=upload_image_book, blank=True, null=True)
    rg_verso = models.ImageField(
        upload_to=upload_image_book, blank=True, null=True)
    carteira_identidade = models.ImageField(
        upload_to=upload_image_book, blank=True, null=True)
    pedido = models.ForeignKey(Pedidos, on_delete=models.CASCADE)
    voucher = models.ForeignKey(Voucher, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.nome_completo}'

class Agendamento(models.Model):
    pedido = models.ForeignKey(Pedidos, on_delete=models.CASCADE)
    data = models.CharField(max_length=255)
    hora = models.CharField(max_length=255)

    def __str__(self):
        return f'Agendamento para o pedido {self.pedido.id} em {self.data} às {self.hora}'
    


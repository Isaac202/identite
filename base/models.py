from django.db import models
from django.db.models import Max

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True,null=True, blank=True)

    class Meta:
        abstract = True

def upload_image_book(instance, filename):
    return f'uploads/consulti/{instance.pk}/{filename}'


class Lote(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    
    numero = models.IntegerField(default=1, unique=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            max_numero = Lote.objects.all().aggregate(Max('numero'))['numero__max']
            if max_numero is not None:
                self.numero = max_numero + 1
        super().save(*args, **kwargs)

class Voucher(BaseModel):
    code = models.CharField(max_length=255, unique=True)  # Aumente o tamanho para armazenar o voucher encriptado
    lote = models.ForeignKey(Lote, on_delete=models.CASCADE)
    is_valid = models.BooleanField(default=True)

    def __str__(self):
        return self.code



class Pedidos(BaseModel):
    STATUS_CHOICES = [
        ('1', 'Não Confirmada'),
        ('2', 'Solicitação de Estorno'),
        ('3', 'Estornada'),
        ('4', 'Emissão liberada'),
        ('5', 'Protocolo Gerado'),
        ('6', 'Emitida'),
        ('7', 'Revogada'),
        ('8', 'Em Verificação'),
        ('9', 'Em Validação'),
        ('10', 'Recusada'),
        ('11', 'Cancelada'),
        ('12', 'Atribuído a Voucher')  # Novo status adicionado aqui
    ]

    pedido = models.CharField(max_length=255, blank=True, null=True)
    protocolo = models.CharField(max_length=255, blank=True, null=True)
    hashVenda = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default='1', null=True, blank=True)

    def __str__(self):
        return f'Numero do Pedido:{self.pedido}'

    def get_status_display(self):
        status_dict = dict(self.STATUS_CHOICES)
        return status_dict.get(self.status, "Status desconhecido")



class DadosCliente(BaseModel):
    nome_completo = models.CharField(max_length=255)
    nome_fantasia = models.CharField(max_length=255)
    razao_social = models.CharField(max_length=255)
    cpf = models.CharField(max_length=14,blank=True, null=True)
    cnpj = models.CharField(max_length=14)
    email = models.EmailField(blank=True, null=True)
    cep = models.CharField(max_length=14)
    logradouro = models.CharField(max_length=255)
    numero = models.CharField(max_length=10)
    complemento = models.CharField(max_length=255)
    bairro = models.CharField(max_length=255)
    cidade = models.CharField(max_length=255)
    uf = models.CharField(max_length=10)
    cod_ibge = models.CharField(max_length=10)
    telefone = models.CharField(max_length=20,blank=True, null=True)
    data_nacimento = models.CharField(max_length=100,blank=True, null=True)
    possui_cnh = models.BooleanField(default=False)
    pedido = models.ForeignKey(Pedidos, on_delete=models.CASCADE)
    voucher = models.ForeignKey(Voucher, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.nome_completo} - {self.telefone}'

class Agendamento(BaseModel):
    pedido = models.ForeignKey(Pedidos, on_delete=models.CASCADE)
    data = models.CharField(max_length=255)
    hora = models.CharField(max_length=255)

    def __str__(self):
        return f'Agendamento para o pedido {self.pedido.id} em {self.data} às {self.hora}'
    



class Slots(BaseModel):
    hashSlot = models.CharField(max_length=255, unique=True)

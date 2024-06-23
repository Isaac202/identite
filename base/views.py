from django.shortcuts import render, redirect
from django.http import Http404
from .models import Agendamento, DadosCliente, Pedidos, Voucher
from .utils import encrypt_voucher, decrypt_voucher


def check_voucher(request):
    if request.method == 'POST':
        code = request.POST.get('voucher_code')
  
        try:
            voucher = Voucher.objects.get(code=code, is_valid=True)
            print(voucher)
            return redirect('form', slug=code)
        except Voucher.DoesNotExist:
            return render(request, 'invalid.html')
    return render(request, 'check_voucher.html')


def form(request,slug=None):
    if slug is None:
        raise Http404("Página não encontrada.")
    else:
        try:
            voucher = Voucher.objects.get(code=slug, is_valid=True)
        except Voucher.DoesNotExist:
            return render(request, 'invalid.html', {'code': slug})
    if request.method == 'POST':
        pedidos = Pedidos.objects.get(id=1)
        novo_cliente = DadosCliente()
        if request.POST["nomeCompleto"].strip():
            novo_cliente.nome_completo = request.POST["nomeCompleto"]
        if request.POST["nomeFantasia"].strip():
            novo_cliente.nome_fantasia = request.POST["nomeFantasia"]
        if request.POST["nomeRazaoSocial"].strip():
            novo_cliente.razao_social = request.POST["nomeRazaoSocial"]
        if request.POST["cpf"].strip():
            novo_cliente.cpf = request.POST["cpf"]
        if request.POST["cnpj"].strip():
            novo_cliente.cnpj = request.POST["cpf"]
        if request.POST["email"].strip():
            novo_cliente.email = request.POST["email"]
        if request.POST["data_nacimento"].strip():
            novo_cliente.data_nacimento = request.POST["data_nacimento"]
        if request.POST["cep"].strip():
            novo_cliente.cep = request.POST["cep"]
        if request.POST["logradouro"].strip():
            novo_cliente.logradouro = request.POST["logradouro"]
        if request.POST["numero"].strip():
            novo_cliente.numero = request.POST["numero"]
        if request.POST["complemento"].strip():
            novo_cliente.complemento = request.POST["complemento"]
        if request.POST["bairro"].strip():
            novo_cliente.bairro = request.POST["bairro"]
        if request.POST["cidade"].strip():
            novo_cliente.cidade = request.POST["cidade"]
        if request.POST["uf"].strip():
            novo_cliente.uf = request.POST["uf"]
        if request.POST["codigoIBGE"].strip():
            novo_cliente.cod_ibge = request.POST["codigoIBGE"]
        if request.POST["telefone"].strip():
            novo_cliente.telefone = request.POST["telefone"]
        if "rg-frente" in request.FILES:
            novo_cliente.rg_frente = request.FILES["rg-frente"]
        if "rg-verso" in request.FILES:
            novo_cliente.rg_verso = request.FILES["rg-verso"]
        if "cnh" in request.FILES:
            novo_cliente.carteira_identidade = request.FILES["cnh"]
        novo_cliente.voucher_id = voucher.id
        novo_cliente.pedido_id = 1
        novo_cliente.save()
        return redirect('agendar_videoconferencia', pedido=pedidos.pedido) # redireciona para a view de agendamento
    return render(request, 'form.html',{'slug': slug})



def agendar_videoconferencia(request, pedido=None):
    if request.method == 'POST':
        # Aqui você pode processar os dados do POST. Por exemplo, você pode salvar a data e a hora escolhidas pelo usuário.
        data = request.POST['data']
        hora = request.POST['hora']
        get_pedido = Pedidos.objects.get(pedido=pedido)
        # Supondo que você tenha um modelo Agendamento que guarda a data e a hora da videoconferência.
        agendamento = Agendamento(pedido=get_pedido, data=data, hora=hora)
        agendamento.save()

        # Redireciona para a página de agradecimento e orientação.
        return redirect('agradecimento_orientacao')

    # Se o método não for POST, renderiza a página de agendamento.
    return render(request, 'agendar_videoconferencia.html', {'pedido': pedido})

def agradecimento_orientacao(request):
    return render(request, 'agradecimento.html')
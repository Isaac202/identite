from django.shortcuts import render, redirect
from django.http import Http404
from .models import Agendamento, DadosCliente, Pedidos, Voucher
from .utils import agendar_pedido, consultar_status_pedido, gerar_protocolo, obter_disponibilidade_agenda, salvar_venda
from datetime import datetime



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
            cpf = request.POST["cpf"].replace(".", "").replace("-", "")          
            novo_cliente.cpf = cpf
        if request.POST["cnpj"].strip():
            cnpj = request.POST["cnpj"].replace(".", "").replace("-", "").replace("/", "")
            novo_cliente.cnpj = cnpj
        if request.POST["email"].strip():
            novo_cliente.email = request.POST["email"]
        if request.POST["data_nacimento"].strip():
            data_nascimento = datetime.strptime(request.POST.get('data_nacimento'), '%d/%m/%Y').strftime('%Y-%m-%d')  # Altera o formato da data
            novo_cliente.data_nacimento = data_nascimento
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
            telefone = request.POST["telefone"].replace("(", "").replace(")", "").replace(" ", "").replace("-", "")
            novo_cliente.telefone = telefone
        if "rg-frente" in request.FILES:
            novo_cliente.rg_frente = request.FILES["rg-frente"]
        if "rg-verso" in request.FILES:
            novo_cliente.rg_verso = request.FILES["rg-verso"]
        if "cnh" in request.FILES:
            novo_cliente.carteira_identidade = request.FILES["cnh"]
        novo_cliente.voucher_id = voucher.id
        pedido, erro = salvar_venda(novo_cliente)
        if pedido is not None:
            novo_cliente.pedido_id = pedido.id
            novo_cliente.save()
            return redirect('gerar_protocolo', pedido=pedido.pedido) # redireciona para a view de agendamento
        else:
            return render(request, 'form.html', {'erro': erro,'slug': slug})
    return render(request, 'form.html',{'slug': slug})



def agendar_videoconferencia(request, pedido=None):
    if request.method == 'POST':
        # Aqui você pode processar os dados do POST. Por exemplo, você pode salvar a data e a hora escolhidas pelo usuário.
        print(request.POST)
        slot = request.POST['slot']
        data, hora_inicial, hora_final = slot.split(';')
        print(data, hora_inicial, hora_final)   
        # Converta a data e a hora para o formato correto
        data = datetime.strptime(data, "%Y-%m-%dT%H:%M:%S").date()
    
        print("Depois de converter")
        print(data, hora_inicial, hora_final)
        get_pedido = Pedidos.objects.get(pedido=pedido)
        hash_venda, error = consultar_status_pedido(pedido)
        if hash_venda["isProtocolo"] == '0':
            error = "O protocolo ainda não foi gerado."
            return render(request, 'protocolo.html', {'pedido': pedido, 'erro_protocolo': error})
        # Agende o pedido
        response_data, errors = agendar_pedido(hash_venda["HashVenda"], data, hora_inicial, hora_final)
        if errors:
            # Trate os erros aqui
            pass

        # Supondo que você tenha um modelo Agendamento que guarda a data e a hora da videoconferência.
        agendamento = Agendamento(pedido=get_pedido, data=data, hora=hora_inicial)
        agendamento.save()

        # Redireciona para a página de agradecimento e orientação.
        return redirect('agradecimento_orientacao')

    # Se o método não for POST, chama a função obter_slots_agenda e passa os dados retornados para o template.
      # Substitua pelo hashSlot apropriado.
    slots_agenda, erro = obter_disponibilidade_agenda()
    print(slots_agenda)
    if erro:
        return render(request, 'gerar_protocolo_view.html', {'erro': erro})

    return render(request, 'agendar_videoconferencia.html', {'pedido': pedido, 'slots_agenda': slots_agenda})

def agradecimento_orientacao(request):
    return render(request, 'agradecimento.html')




def gerar_protocolo_view(request, pedido=None):
    dados_cliente = DadosCliente.objects.get(pedido__pedido=pedido)
    if request.method == 'POST':
        cnpj = request.POST.get('cnpj').replace(".", "").replace("/", "").replace("-", "")  # Remove a máscara do CNPJ
        cpf = request.POST.get('cpf').replace(".", "").replace("-", "")  # Remove a máscara do CPF
        data_nascimento = datetime.strptime(request.POST.get('data_nascimento'), '%d/%m/%Y').strftime('%Y-%m-%d')  # Altera o formato da data

        # Pega os outros dados do objeto dados_cliente
        pedido = dados_cliente.pedido.pedido
        is_possui_cnh = True if dados_cliente.carteira_identidade else False   

        erros, protocolo = gerar_protocolo(pedido, cnpj, cpf, data_nascimento, is_possui_cnh)
        if protocolo is not None:
            return render(request, 'agendar_videoconferencia.html', {'pedido': pedido})
        else:
            return render(request, 'protocolo.html', {'pedido': pedido,'erros': erros})
    return render(request, 'protocolo.html', {'pedido': pedido, 'dados_cliente': dados_cliente})
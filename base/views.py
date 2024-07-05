from django.shortcuts import get_object_or_404, render, redirect
from django.http import Http404
import base64
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.forms.models import model_to_dict
from base.filters import DadosClienteFilter, VoucherFilter
from base.task import salvar_arquivos_cliente
from .models import Agendamento, DadosCliente, Pedidos, Voucher
from .utils import adicionar_protocolo_e_hashvenda_no_pedido, agendar_pedido, consultar_status_pedido, generate_random_code, gerar_protocolo, obter_disponibilidade_agenda, salvar_venda, verifica_se_pode_videoconferecias
from datetime import datetime
from .forms import VoucherForm
from django.utils.dateparse import parse_date
from rest_framework import viewsets
from rest_framework import viewsets, permissions
from django.views.decorators.http import require_POST
from .models import Voucher, DadosCliente
from .serializers import VoucherSerializer, DadosClienteSerializer
from django.http import JsonResponse
from .models import Voucher, Lote

API_KEY = 'e9f1c3b7d2f44a3294d3b1e3429f6a75'

@csrf_exempt
@require_POST
def generate_vouchers(request):
    api_key = request.headers.get('APIKEY')
    
    if api_key != API_KEY:
        return JsonResponse({'error': 'Invalid API Key'}, status=403)

    lote = Lote.objects.create()
    vouchers = []
    for _ in range(1000):
        code = generate_random_code()
        voucher = Voucher.objects.create(code=code, lote=lote)
        vouchers.append(voucher)

    return JsonResponse({'lote': lote.id, 'vouchers': [model_to_dict(v) for v in vouchers]}, status=201)
class VoucherViewSet(viewsets.ModelViewSet):
    queryset = Voucher.objects.all()
    serializer_class = VoucherSerializer
    permission_classes = [permissions.AllowAny]  # Adicione esta linha

class DadosClienteViewSet(viewsets.ModelViewSet):
    queryset = DadosCliente.objects.all()
    serializer_class = DadosClienteSerializer
    permission_classes = [permissions.AllowAny]  # Adicione esta linha



    
def check_voucher(request):
    if request.method == 'POST':
        code = request.POST.get('voucher_code')
  
        try:
            voucher = Voucher.objects.get(code=code, is_valid=True)
            
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
   
        novo_cliente.voucher_id = voucher.id
        pedido, erro = salvar_venda(novo_cliente)
        if pedido is not None:
            novo_cliente.pedido_id = pedido.id
            novo_cliente.save()
            rg_frente = rg_verso = cnh = None

            if "rg-frente" in request.FILES:
                rg_frente = base64.b64encode(request.FILES["rg-frente"].read()).decode('utf-8')

            if "rg-verso" in request.FILES:
                rg_verso = base64.b64encode(request.FILES["rg-verso"].read()).decode('utf-8')

            if "cnh" in request.FILES:
                cnh = base64.b64encode(request.FILES["cnh"].read()).decode('utf-8')
            salvar_arquivos_cliente.delay(novo_cliente.id, rg_frente, rg_verso, cnh)
            return redirect('gerar_protocolo', pedido=pedido.pedido) # redireciona para a view de agendamento
        else:
            return render(request, 'form.html', {'erro': erro,'slug': slug})
    return render(request, 'form.html',{'slug': slug})



def agendar_videoconferencia(request, pedido=None):
    cliente = DadosCliente.objects.get(pedido__pedido=pedido)
    esta_ok = verifica_se_pode_videoconferecias(cliente)
    if not esta_ok:
        return render(request, 'entre_contato.html')
    if request.method == 'POST':
        # Aqui você pode processar os dados do POST. Por exemplo, você pode salvar a data e a hora escolhidas pelo usuário.
       
        slot = request.POST['slot']
        data, hora_inicial, hora_final = slot.split(';')
        # Converta a data e a hora para o formato correto
        data = datetime.strptime(data, "%Y-%m-%dT%H:%M:%S%z").date()
        get_pedido = Pedidos.objects.get(pedido=pedido)
        hash_venda, error = consultar_status_pedido(pedido)
        if hash_venda["StatusPedido"] != 'Protocolo Gerado':
            error = "O protocolo ainda não foi gerado."
            return render(request, 'protocolo.html', {'pedido': pedido, 'erro_protocolo': error})
        adicionar_protocolo_e_hashvenda_no_pedido(get_pedido, hash_venda['Protocolo'], hash_venda['HashVenda'])
        # Agende o pedido
        response_data, errors = agendar_pedido(hash_venda["HashVenda"], data, hora_inicial, hora_final)
        if errors:
            # Trate os erros aqui
            pass

        # Supondo que você tenha um modelo Agendamento que guarda a data e a hora da videoconferência.
        agendamento = Agendamento(pedido=get_pedido, data=data, hora=hora_inicial)
        agendamento.save()

        # Instancie o voucher e atualize para inválido
        dados_cliente = DadosCliente.objects.get(pedido=get_pedido)
        voucher = dados_cliente.voucher
        voucher.is_valid = False
        voucher.save()

        # Redireciona para a página de agradecimento e orientação.
        return redirect('agradecimento_orientacao')

    # Se o método não for POST, chama a função obter_slots_agenda e passa os dados retornados para o template.
      # Substitua pelo hashSlot apropriado.
    slots_agenda, erro = obter_disponibilidade_agenda()

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
        is_possui_cnh = True if dados_cliente.carteira_habilitacao else False   

        erros, protocolo = gerar_protocolo(pedido, cnpj, cpf, data_nascimento, is_possui_cnh)

        
        status_pedido = consultar_status_pedido(pedido)
        if any('Protocolo emitido com sucesso' in erro['ErrorDescription'] for erro in erros):
            print("Linha 208")
            print(erros)
            return redirect('agendar_videoconferencia', pedido=pedido)
        print("Linha 210", erros)
        if erros:
            print("Linha 212")
            return render(request, 'protocolo.html', {'pedido': pedido, 'erros': erros})
        if protocolo is not None:
            print("Linha 215")
            return render(request, 'agendar_videoconferencia.html', {'pedido': pedido})
        else:
            print("Linha 219")
            return render(request, 'protocolo.html', {'pedido': pedido,'erros': erros})
    return render(request, 'protocolo.html', {'pedido': pedido, 'dados_cliente': dados_cliente})



@login_required
def list_vouchers(request):
    voucher_list = Voucher.objects.all()
    voucher_filter = VoucherFilter(request.GET, queryset=voucher_list)
    return render(request, 'home/listar_voucher.html', {'filter': voucher_filter})


@login_required
def create_voucher(request):
    if request.method == "POST":
        form = VoucherForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('list_vouchers')
    else:
        form = VoucherForm()
    return render(request, 'home/create_voucher.html', {'form': form})

@login_required
def voucher_statistics(request):
    dados_cliente_filter = DadosClienteFilter(request.GET, queryset=DadosCliente.objects.filter(voucher__isnull=False).select_related('voucher'))
    clients_with_vouchers = dados_cliente_filter.qs
    all_voucher = Voucher.objects.all()
    total_clients = clients_with_vouchers.distinct().count()
    active_vouchers = all_voucher.filter(is_valid=True).count()
    inactive_vouchers = all_voucher.filter(is_valid=False).count()

    context = {
        'filter': dados_cliente_filter,
        'total_clients': total_clients,
        'active_vouchers': active_vouchers,
        'inactive_vouchers': inactive_vouchers,
        'clients_with_vouchers': clients_with_vouchers,
    }

    return render(request, 'home/index.html', context)


@login_required
@csrf_exempt
def create_voucher(request):
    if request.method == "POST":
        quantity = int(request.POST.get('quantity', 1))
        vouchers = []
        for _ in range(quantity):
            code = generate_random_code()
            voucher = Voucher.objects.create(code=code)
            vouchers.append(voucher)
        return JsonResponse({'vouchers': [model_to_dict(v) for v in vouchers]}, status=201)
    return JsonResponse({'error': 'Invalid method'}, status=400)

@login_required
@csrf_exempt
def edit_voucher(request, id):
    voucher = get_object_or_404(Voucher, id=id)
    if request.method == "POST":
        
        if voucher.is_valid == True:
            voucher.is_valid = False
            voucher.save()
            return JsonResponse({'voucher': model_to_dict(voucher)}, status=200)
        else:
            voucher.is_valid = True
            voucher.save()
            return JsonResponse({'voucher': model_to_dict(voucher)}, status=200)
    else:
        form = VoucherForm(instance=voucher)
    return JsonResponse({'form': form.as_p()}, status=400)

@login_required
@csrf_exempt
def delete_voucher(request, id):
    voucher = get_object_or_404(Voucher, id=id)
    if request.method == "POST":
        voucher.delete()
        return JsonResponse({'result': 'OK'}, status=200)
    return JsonResponse({'error': 'Invalid method'}, status=400)
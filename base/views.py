import json
from django.shortcuts import get_object_or_404, render, redirect
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.forms.models import model_to_dict
from base.filters import DadosClienteFilter, VoucherFilter
from base.task import update_status_celery,salvar_arquivos_cliente
from .models import Agendamento, DadosCliente, Pedidos, Voucher
from .utils import create_client_and_order, get_address_data,adicionar_protocolo_e_hashvenda_no_pedido, agendar_pedido, consultar_status_pedido, generate_random_code, gerar_protocolo, obter_disponibilidade_agenda, salvar_venda, verifica_se_pode_videoconferecias
from datetime import datetime
from .forms import VoucherForm
import base64
from .forms import EmpresaForm
from .utils import fetch_empresa_data, get_address_data
from django.core.files.base import ContentFile
from django.http import HttpResponseRedirect
from django.urls import reverse
from rest_framework import viewsets
from rest_framework import viewsets, permissions
from django.views.decorators.http import require_POST
from .models import Voucher, DadosCliente
from .serializers import VoucherSerializer, DadosClienteSerializer
from django.http import JsonResponse
from .models import Voucher, Lote
import requests
from rest_framework import status
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q
from django.db import transaction



API_KEY = 'e9f1c3b7d2f44a3294d3b1e3429f6a75'


def get_empresa_data(request):
    cnpj = request.GET.get('cnpj', None)
    CPFCNPJ_API_KEY = settings.CPFCNPJ
    if cnpj and len(cnpj) == 14:
        response = requests.get(f'https://api.cpfcnpj.com.br/{CPFCNPJ_API_KEY}/5/{cnpj}')
        if response.status_code == 200:
            data = response.json()
            return JsonResponse({
                'razao': data.get('razao'),
                'fantasia': data.get('fantasia'),
                'cep': data.get('matrizEndereco', {}).get('cep'),
                # Adicione aqui outros campos que você deseja retornar
            })
    return JsonResponse({'error': 'CNPJ inválido'}, status=400)


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


def empresa_form_view(request):
    if request.method == 'POST':
        form = EmpresaForm(request.POST)
        if form.is_valid():
            # Processa os dados do formulário
            cnpj = form.cleaned_data['cnpj']
            voucher = form.cleaned_data['voucher']
            empresa_data = fetch_empresa_data(cnpj)
            if not empresa_data:
                form.add_error('cnpj', 'Dados da empresa não encontrados.')
            else:
                cep = empresa_data.get('cep')
                endereco_data = get_address_data(cep)
                if not endereco_data:
                    form.add_error('cep', 'Dados de endereço não encontrados.')
                else:
                    # Preencher o formulário com os dados da empresa e do endereço
                    form = EmpresaForm(initial={
                        'cnpj': cnpj,
                        'voucher': voucher,
                        'nome_completo': empresa_data.get('razao'),
                        'nome_fantasia': empresa_data.get('fantasia'),
                        'razao_social': empresa_data.get('razao'),
                        'cep': cep,
                        'logradouro': endereco_data.get('logradouro'),
                        'complemento': endereco_data.get('complemento'),
                        'bairro': endereco_data.get('bairro'),
                        'numero': 'SN',
                        'cidade': endereco_data.get('localidade'),
                        'uf': endereco_data.get('uf'),
                        'cod_ibge': endereco_data.get('ibge'),
                    })
    else:
        form = EmpresaForm()
    
    return render(request, 'empresa_form.html', {'form': form})

    
def check_voucher(request):
    if request.method == 'POST':
        code = request.POST.get('voucher_code')
        cnpj = request.POST["cnpj"]
  
        try:
            cliente = DadosCliente.objects.get(voucher__code=code)
            if cliente.pedido.protocolo:
                return render(request, 'invalid.html')
            else:
                return redirect('form', slug=code)
        except DadosCliente.DoesNotExist:
            print("Linha 31")
            
            cliente_get =create_client_and_order(cnpj, code)
            if not cliente_get:
                return redirect('atualizar_empresa', voucher=code)
            return redirect('form', slug=code)  # Redireciona para o formulário com o código do voucher
        except DadosCliente.MultipleObjectsReturned:
            return render(request, 'invalid.html')
    return render(request, 'check_voucher.html')

def form(request, slug=None):
    if slug is None:
        raise Http404("Página não encontrada.")
    else:
        try:
            voucher = Voucher.objects.get(code=slug)
            cliente = DadosCliente.objects.filter(voucher__code=slug).first()
            if cliente:
                cliente_existente = True
                nome_completo = cliente.nome_fantasia if cliente.nome_fantasia != "N/A" else cliente.razao_social.split(" ")[0] 
            else:
                nome_completo = None
                cliente_existente = False
        except Voucher.DoesNotExist:
            return render(request, 'invalid.html', {'code': slug})

    if request.method == 'POST':
        if "cnpj" in request.POST and request.POST["cnpj"].strip():
            cnpj = request.POST["cnpj"]
            cliente_get =create_client_and_order(cnpj, slug)
            if not cliente_get:
                return redirect('atualizar_empresa', voucher=slug)
            return redirect(request.path)
        
        cliente = DadosCliente.objects.filter(voucher__code=slug).first()

        if request.POST["nomeCompleto"].strip():
            cliente.nome_completo = request.POST["nomeCompleto"]
        if request.POST["email"].strip():
            cliente.email = request.POST["email"]
        if request.POST["telefone"].strip():
            telefone = request.POST["telefone"].replace("(", "").replace(")", "").replace(" ", "").replace("-", "")
            cliente.telefone = telefone
    
        pedido, erro = salvar_venda(cliente)
        if pedido is not None:
            cliente.pedido.pedido = pedido
            cliente.pedido.save()
            cliente.save()
            def encode_file_to_base64(file):
                return base64.b64encode(file.read()).decode('utf-8')

            rg_frente_b64 = None
            rg_verso_b64 = None
            cnh_b64 = None

            if "rg-frente" in request.FILES:
                rg_frente_b64 = encode_file_to_base64(request.FILES["rg-frente"])
                
            if "rg-verso" in request.FILES:
                rg_verso_b64 = encode_file_to_base64(request.FILES["rg-verso"])
        
            if "cnh" in request.FILES:
                cnh_b64 = encode_file_to_base64(request.FILES["cnh"])

            # Chama a tarefa Celery para salvar os arquivos
            salvar_arquivos_cliente.delay(cliente.id, rg_frente_b64, rg_verso_b64, cnh_b64)
    
            Voucher.objects.filter(code=slug).update(is_valid=False)
            return redirect('gerar_protocolo', pedido=pedido)
        else:
            return render(request, 'form.html', {'erro': erro, 'slug': slug, 'cliente': cliente, 'cliente_existente': cliente_existente})
    return render(request, 'form.html', {'slug': slug, 'cliente': cliente,'nome_completo': nome_completo, 'cliente_existente': cliente_existente})


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



def get_key_by_value(dictionary, value):
    for key, val in dictionary.items():
        if val == value:
            return key
        
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
        dados_cliente = DadosCliente.objects.get(pedido__pedido=pedido)
        dados_cliente.cnpj = cnpj
        dados_cliente.cpf = cpf
        dados_cliente.data_nacimento = data_nascimento
        dados_cliente.save()
        
        status_pedido = consultar_status_pedido(pedido)
        if any('Protocolo emitido com sucesso' in erro['ErrorDescription'] for erro in erros):
            status, error = consultar_status_pedido(dados_cliente.pedido.pedido)
            status_dict = dict(Pedidos.STATUS_CHOICES)
            status_key = get_key_by_value(status_dict, status["StatusPedido"])
            dados_cliente.pedido.status = status_key
            dados_cliente.pedido.save()
            return redirect('agendar_videoconferencia', pedido=pedido)
        
        if erros:
            return render(request, 'protocolo.html', {'pedido': pedido, 'erros': erros})
        if protocolo is not None:
            return render(request, 'agendar_videoconferencia.html', {'pedido': pedido})
        else:
            return render(request, 'protocolo.html', {'pedido': pedido,'erros': erros})
    return render(request, 'protocolo.html', {'pedido': pedido, 'dados_cliente': dados_cliente})



@login_required
def list_vouchers(request):
    voucher_list = Voucher.objects.filter(is_valid=True)
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

def update_status_view(request):
    filter_params = request.GET.dict()
    queryset = DadosCliente.objects.all()

    if 'start_date' in filter_params and filter_params['start_date']:
        queryset = queryset.filter(created_at__gte=filter_params['start_date'])
    if 'end_date' in filter_params and filter_params['end_date']:
        queryset = queryset.filter(created_at__lte=filter_params['end_date'])
    if 'status' in filter_params and filter_params['status']:
        queryset = queryset.filter(pedido__status=filter_params['status'])
    if 'nome_completo' in filter_params and filter_params['nome_completo']:
        queryset = queryset.filter(nome_completo__icontains=filter_params['nome_completo'])
    if 'cnpj' in filter_params and filter_params['cnpj']:
        queryset = queryset.filter(cnpj__icontains=filter_params['cnpj'])
    if 'voucher_code' in filter_params and filter_params['voucher_code']:
        queryset = queryset.filter(voucher__code__icontains=filter_params['voucher_code'])

    # Filtra apenas clientes com status '5' (assumindo que '5' é o status que precisa ser atualizado)
    queryset = queryset.filter(pedido__status='5')

    clientes = queryset[:100]  # Limita a 100 clientes
    cliente_ids = list(clientes.values_list('id', flat=True))

    update_status_celery.delay(cliente_ids)

    return JsonResponse({'success': True, 'message': f'Atualizando {len(cliente_ids)} clientes.'})


@login_required
def voucher_statistics(request):
    # Aplicar filtros
    dados_cliente_filter = DadosClienteFilter(request.GET, queryset=DadosCliente.objects.filter(voucher__isnull=False).select_related('voucher', 'pedido').order_by('-created_at'))
    clients_with_vouchers = dados_cliente_filter.qs

    # Calcular estatísticas com base nos filtros aplicados
    total_clients = clients_with_vouchers.distinct().count()
    
    # Obter vouchers únicos dos clientes filtrados
    filtered_vouchers = Voucher.objects.filter(dadoscliente__in=clients_with_vouchers).distinct()
    
    active_vouchers = filtered_vouchers.filter(is_valid=True).count()
    inactive_vouchers = filtered_vouchers.filter(is_valid=False).count()

    # Adicionar paginação
    paginator = Paginator(clients_with_vouchers, 10)  # 10 itens por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'filter': dados_cliente_filter,
        'total_clients': total_clients,
        'active_vouchers': active_vouchers,
        'inactive_vouchers': inactive_vouchers,
        'clients_with_vouchers': page_obj,
        'page_obj': page_obj,
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



@csrf_exempt
def update_status(request, pedido_id):
    if request.method == 'POST':
        try:
            pedido = Pedidos.objects.get(pedido=pedido_id)
        except ObjectDoesNotExist:
            return JsonResponse({'error': 'Pedido não encontrado'}, status=404)
        status, error = consultar_status_pedido(pedido.pedido)
        status_dict = dict(Pedidos.STATUS_CHOICES)
        status_key = get_key_by_value(status_dict, status["StatusPedido"])

        if error:
            return JsonResponse({'error': error}, status=400)
    
        pedido.status = status_key
        pedido.save()
        return JsonResponse({'success': 'Status atualizado com sucesso'}, status=200)
   
    else:
        return JsonResponse({'error': 'Método inválido'}, status=405)


@csrf_exempt
def create_client_and_assign_voucher(request):  
    data = json.loads(request.body)
    if data['APIKEY'] != API_KEY:
        return JsonResponse({'error': 'Invalid API Key'}, status=403)
    cnpj = data['cnpj'].replace(".", "").replace("-", "").replace("/", "")
    voucher = Voucher.objects.filter(is_valid=True).first()
    if not voucher:
        return JsonResponse({'error': 'Nenhum voucher disponível'}, status=404)
    voucher.is_valid = False
    voucher.save()
    print(voucher.is_valid)
    return JsonResponse({
        'id': voucher.id,
        'code': voucher.code,
        'is_valid': voucher.is_valid,
    }, status=200)


def atualizar_empresa(request, voucher):
    voucher = str(voucher)
    if request.method == 'POST':
        # Captura os dados do formulário diretamente do request.POST
        print("POST",voucher)
        nome_fantasia = request.POST.get('nomeFantasia')
        razao_social = request.POST.get('razaoSocial')
        cnpj = request.POST.get('cnpj')
        cep = request.POST.get('cep')
        cep = cep.replace(".", "").replace("-", "").replace(" ", "")
        cnpj = cnpj.replace(".", "").replace("-", "").replace(" ", "").replace("/","")
        endereco_data = get_address_data(cep)
        
        # Validação básica dos dados
        errors = []
        if not cnpj or not cep:
            errors.append('Campos obrigatórios não preenchidos.')
        if len(cnpj) != 14:
            errors.append('CNPJ inválido.')
        if len(cep) != 8 or not cep.isdigit():
            errors.append('CEP inválido.')
        
        if errors:
            print(errors)
            return render(request, 'empresa.html', {'errors': errors, "voucher": voucher})
        
        # Obtém o objeto voucher
        try:
            voucher = Voucher.objects.get(code=voucher)
        except Voucher.DoesNotExist:
            errors.append('Voucher não encontrado.')
            return render(request, 'empresa.html', {'errors': errors, "voucher": voucher})

        # Cria um novo pedido
        novo_pedido = Pedidos(
            pedido=generate_random_code(),  # Gere um código aleatório para o pedido
            status='13'  # Status atribuído ao Voucher
        )
        novo_pedido.save()

        # Cria ou atualiza o objeto DadosCliente associado ao voucher
        dados_cliente, created = DadosCliente.objects.update_or_create(
            voucher=voucher,  # Filtra pelo voucher
            defaults={  # Define os dados que devem ser atualizados ou criados
                'nome_fantasia': nome_fantasia,
                'razao_social': razao_social,
                'cnpj': cnpj,
                'cep': cep,
                'logradouro': endereco_data.get('logradouro') or 'N/A',
                'complemento': endereco_data.get('complemento', ''),
                'bairro': endereco_data.get('bairro') or 'N/A',
                'cidade': endereco_data.get('localidade') or 'N/A',
                'uf': endereco_data.get('uf') or 'N/A',
                'cod_ibge': endereco_data.get('ibge') or 'N/A',
                'numero': 'SN',
                'pedido': novo_pedido,  # Associa o novo pedido
            }
        )

        # Redireciona para a página de sucesso
        return redirect('form', slug=voucher.code)

    if request.method == 'GET':
        return render(request, 'empresa.html', {"voucher": voucher})


def handler404(request, exception, *args, **argv):
    return render(request, '404.html', status=404)

def handler500(request, *args, **argv):
    return render(request, '500.html', status=500)

def consultar_status_view(request, cliente_id):
    try:
        with transaction.atomic():
            cliente = DadosCliente.objects.select_for_update().get(id=cliente_id)
            status_data, error = consultar_status_pedido(cliente.pedido.pedido)
            if error:
                return JsonResponse({'success': False, 'error': error})
            
            status_dict = dict(Pedidos.STATUS_CHOICES)
            status_key = get_key_by_value(status_dict, status_data["StatusPedido"])
            
            # Atualiza o status do pedido
            if cliente.pedido.status != status_key:
                cliente.pedido.status = status_key
                cliente.pedido.save()
            
            # Atualiza o protocolo se disponível
            if status_data.get("Protocolo") and cliente.pedido.protocolo != status_data["Protocolo"]:
                cliente.pedido.protocolo = status_data["Protocolo"]
                cliente.pedido.save()
            
            # Atualiza o hashVenda se disponível
            if status_data.get("HashVenda") and cliente.pedido.hashVenda != status_data["HashVenda"]:
                cliente.pedido.hashVenda = status_data["HashVenda"]
                cliente.pedido.save()

            # Atualiza ou cria o agendamento
            if status_data.get("DataHoraAgenda"):
                data_hora = datetime.strptime(status_data["DataHoraAgenda"], "%d/%m/%Y %H:%M:%S")
                agendamento, created = Agendamento.objects.update_or_create(
                    pedido=cliente.pedido,
                    defaults={
                        'data': data_hora.strftime("%Y-%m-%d"),
                        'hora': data_hora.strftime("%H:%M:%S")
                    }
                )

        return JsonResponse({
            'success': True,
            'status': status_dict.get(status_key, "Desconhecido"),
            'status_description': status_data.get("StatusPedido", "Descrição não disponível"),
            'protocolo': status_data.get("Protocolo", "Não disponível"),
            'hashVenda': status_data.get("HashVenda", "Não disponível"),
            'data_status': status_data.get("DataStatusPedido", "Não disponível"),
            'local_agendamento': status_data.get("LocalAgendamento", "Não disponível"),
            'data_hora_agenda': status_data.get("DataHoraAgenda", "Não disponível")
        })
    except DadosCliente.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Cliente não encontrado'})

@require_POST
def atualizar_status_individual_view(request, cliente_id):
    try:
        cliente = DadosCliente.objects.get(id=cliente_id)
        status, error = consultar_status_pedido(cliente.pedido.pedido)
        if error:
            return JsonResponse({'success': False, 'error': error})
        print(status)
        status_dict = dict(Pedidos.STATUS_CHOICES)
        status_key = get_key_by_value(status_dict, status["StatusPedido"])
        
        if cliente.pedido.status != status_key:
            cliente.pedido.status = status_key
            cliente.pedido.save()
        
        return JsonResponse({
            'success': True,
            'status': status_dict.get(status_key, "Desconhecido"),
            'status_description': status.get("StatusPedido", "Descrição não disponível")
        })
    except DadosCliente.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Cliente não encontrado'})
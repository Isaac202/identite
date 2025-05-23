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
from django.db.utils import IntegrityError



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
        
        try:
            voucher = Voucher.objects.get(code=code)
            
            if not voucher.is_valid:
                return render(request, 'invalid.html', {'message': 'Este voucher já foi utilizado.'})
            
            # Redirecionar para o formulário genérico
            return redirect('form', slug=code)
        
        except Voucher.DoesNotExist:
            return render(request, 'invalid.html', {'message': 'Voucher inválido.'})
    
    return render(request, 'check_voucher.html')

def form(request, slug):
    if slug is None:
        raise Http404("Página não encontrada.")
    
    voucher = get_object_or_404(Voucher, code=slug)
    cliente = DadosCliente.objects.filter(voucher=voucher).first()
    
    if request.method == 'POST':
        # Se for e-CNPJ e tiver identificação, usar create_client_and_order
        if voucher.tipo == 'ECNPJ' and request.POST.get("identificacao"):
            identificacao = request.POST.get("identificacao")
            cliente, error, _ = create_client_and_order(identificacao, slug)
            if error:
                return render(request, 'form.html', {'erro': error, 'slug': slug, 'voucher': voucher})
            return redirect('form', slug=slug)

        # Para e-CPF ou atualização de dados existentes
        if not cliente:
            # Criar um novo pedido primeiro
            novo_pedido = Pedidos.objects.create(
                pedido=generate_random_code(),
                status='13'  # Atribuído a Voucher
            )
            
            # Criar o cliente com o pedido
            cliente = DadosCliente(
                voucher=voucher,
                pedido=novo_pedido
            )
        
        # Atualizar dados do cliente
        if voucher.tipo == 'ECNPJ':
            cliente.nome_fantasia = request.POST.get("nomeFantasia")
            cliente.razao_social = request.POST.get("razaoSocial")
            cliente.cnpj = request.POST.get("cnpj", "").replace(".", "").replace("-", "").replace("/", "")
        else:  # ECPF
            cliente.nome_completo = request.POST.get("nomeCompleto")
            cliente.cpf = request.POST.get("cpf", "").replace(".", "").replace("-", "")
            # Campos específicos para e-CPF
            cliente.cep = request.POST.get("cep", "").replace("-", "")
            cliente.logradouro = request.POST.get("logradouro")
            cliente.numero = request.POST.get("numero")
            cliente.complemento = request.POST.get("complemento")
            cliente.bairro = request.POST.get("bairro")
            cliente.cidade = request.POST.get("cidade")
            cliente.uf = request.POST.get("uf")
            cliente.cod_ibge = request.POST.get("cod_ibge")
        
        # Dados comuns para ambos os tipos
        cliente.email = request.POST.get("email")
        telefone = request.POST.get("telefone")
        if telefone:
            cliente.telefone = telefone.replace("(", "").replace(")", "").replace(" ", "").replace("-", "")
        cliente.possui_cnh = request.POST.get("possui_cnh") == "sim"
        
        try:
            cliente.save()
        except IntegrityError as e:
            return render(request, 'form.html', {'erro': str(e), 'slug': slug, 'cliente': cliente, 'voucher': voucher})
        
        pedido, erro = salvar_venda(cliente)
        if pedido is not None:
            cliente.pedido.pedido = pedido
            cliente.pedido.save()
            voucher.is_valid = False
            voucher.save()
            return redirect('gerar_protocolo', pedido=pedido)
        else:
            return render(request, 'form.html', {'erro': erro, 'slug': slug, 'cliente': cliente, 'voucher': voucher})
    
    return render(request, 'form.html', {'slug': slug, 'cliente': cliente, 'voucher': voucher})


def agendar_videoconferencia(request, pedido=None):
    cliente = DadosCliente.objects.get(pedido__pedido=pedido)
    esta_ok = verifica_se_pode_videoconferecias(cliente)
    if not esta_ok:
        return render(request, 'entre_contato.html')
    if request.method == 'POST':
        # Aqui você pode processar os dados do POST. Por exemplo, você pode salvar a data e a hora escolhidas pelo usuário.
       
        slot = request.POST['slot']
        data, hora_inicial, hora_final = slot.split(';')
        # Add timezone info to the datetime string
        data = datetime.strptime(data + "+0000", "%Y-%m-%dT%H:%M:%S%z").date()
        get_pedido = Pedidos.objects.get(pedido=pedido)
        documento_cliente = cliente.cnpj or cliente.cpf
        hash_venda, error = consultar_status_pedido(documento_cliente)
      
        if hash_venda.get("Pedidos"):
            # Ordena os pedidos pela data mais recente
            pedido_atual = sorted(
                hash_venda["Pedidos"],
                key=lambda x: datetime.strptime(x.get("DataVenda", "2000-01-01T00:00:00"), "%Y-%m-%dT%H:%M:%S.%f"),
                reverse=True
            )[0]
            
            if pedido_atual["StatusPedido"] != 'Protocolo Gerado':
                error = "O protocolo ainda não foi gerado."
                return render(request, 'protocolo.html', {'pedido': pedido, 'erro_protocolo': error})
                
            adicionar_protocolo_e_hashvenda_no_pedido(get_pedido, pedido_atual['Protocolo'], pedido_atual['HashVenda'])
            # Agende o pedido
            response_data, errors = agendar_pedido(pedido_atual["HashVenda"], data, hora_inicial, hora_final)
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
    # Verificar se o protocolo já foi gerado
    status, error = consultar_status_pedido(pedido)
    # Adicionar ambas as possíveis strings de status
    status_success = ['Protocolo Gerado', 'Protocolo emitido com sucesso']
    if not error and status and status.get("StatusPedido") in status_success:
        return redirect('agendar_videoconferencia', pedido=pedido)
    try:
        dados_cliente = DadosCliente.objects.select_related('voucher', 'pedido').get(pedido__pedido=pedido)
            
    except DadosCliente.DoesNotExist:
        return render(request, 'protocolo.html', {'pedido': pedido, 'erro': 'Cliente no encontrado'})

    if request.method == 'POST':
        try:
            # Limpar e preparar os dados uma única vez
            cnpj_cpf = (dados_cliente.cnpj if dados_cliente.voucher.tipo == 'ECNPJ' else dados_cliente.cpf).replace(".", "").replace("-", "").replace("/", "")
            cpf = request.POST.get('cpf', '').replace(".", "").replace("-", "")
            dados_cliente.cpf = cpf
            dados_cliente.save()
            try:
                data_nascimento = datetime.strptime(request.POST.get('data_nascimento', ''), '%d/%m/%Y').strftime('%Y-%m-%d')
            except ValueError:
                return render(request, 'protocolo.html', {
                    'pedido': pedido, 
                    'dados_cliente': dados_cliente,
                    'erro': 'Data de nascimento inválida'
                })

            # Validações básicas antes de fazer a requisição
            if not cpf or not data_nascimento:
                return render(request, 'protocolo.html', {
                    'pedido': pedido, 
                    'dados_cliente': dados_cliente,
                    'erro': 'Todos os campos são obrigatórios'
                })

            # Fazer a requisição para gerar o protocolo
            erros, protocolo = gerar_protocolo(pedido, cnpj_cpf, cpf, data_nascimento, dados_cliente.possui_cnh)
            
            if erros:
                # Verificar se o erro indica que o protocolo já foi gerado
                for erro in erros:
                    if isinstance(erro, dict):
                        erro_desc = erro.get('ErrorDescription', '').lower()
                    else:
                        erro_desc = str(erro).lower()
                        
                    # Adicionar ambas as possíveis strings de erro
                    if any(status in erro_desc for status in ["protocolo já foi gerado", "protocolo emitido com sucesso"]):
                        return redirect('agendar_videoconferencia', pedido=pedido)
                
                return render(request, 'protocolo.html', {
                    'pedido': pedido, 
                    'erros': erros, 
                    'dados_cliente': dados_cliente
                })
            
            if protocolo:
                # Atualizar status do pedido
                status, error = consultar_status_pedido(dados_cliente.pedido.pedido)
                if not error and status:
                    status_dict = dict(Pedidos.STATUS_CHOICES)
                    status_key = get_key_by_value(status_dict, status["StatusPedido"])
                    dados_cliente.pedido.status = status_key
                    dados_cliente.pedido.save()
                
                return redirect('agendar_videoconferencia', pedido=pedido)
            
            return render(request, 'protocolo.html', {
                'pedido': pedido, 
                'erro': 'Erro ao gerar protocolo', 
                'dados_cliente': dados_cliente
            })

        except Exception as e:
            return render(request, 'protocolo.html', {
                'pedido': pedido, 
                'erro': f'Erro inesperado: {str(e)}', 
                'dados_cliente': dados_cliente
            })
    
    return render(request, 'protocolo.html', {'pedido': pedido, 'dados_cliente': dados_cliente})



@login_required
def list_vouchers(request):
    voucher_list = Voucher.objects.filter(is_valid=True)
    voucher_filter = VoucherFilter(request.GET, queryset=voucher_list)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Se for uma requisição AJAX, retornar apenas a parte da tabela
        return render(request, 'home/voucher_table_rows.html', {'filter': voucher_filter})
    
    return render(request, 'home/listar_voucher.html', {'filter': voucher_filter})


@login_required
@csrf_exempt
def create_voucher(request):
    if request.method == "POST":
        quantity = int(request.POST.get('quantity', 1))
        tipo = request.POST.get('tipo', 'ECNPJ')  # Default para e-CNPJ se não especificado
        
        # Criar um novo lote
        lote = Lote.objects.create()
        vouchers = []
        
        for _ in range(quantity):
            code = generate_random_code()
            voucher = Voucher.objects.create(
                code=code,
                lote=lote,
                tipo=tipo
            )
            vouchers.append(voucher)
            
        return JsonResponse({
            'vouchers': [{
                'id': v.id,
                'code': v.code,
                'tipo': v.get_tipo_display(),
                'is_valid': v.is_valid
            } for v in vouchers]
        }, status=201)
    
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
    print("request:",request.body)
    data = json.loads(request.body)
    print("data:",data)
    if data['APIKEY'] != API_KEY:
        return JsonResponse({'error': 'Invalid API Key'}, status=403)
    
    # Verificar se temos CPF ou CNPJ no payload
    cnpj = data.get('cnpj', '').strip()
    cpf = data.get('cpf', '').strip()
    razao_social = data.get('razao_social')
    nome_fantasia = data.get('nome_fantasia')
    cep = data.get('cep')  # Adicionado CEP
    print("data:",data)
    # Determinar o tipo baseado em qual campo está preenchido
    if cpf:
        identificacao = cpf

        tipo_voucher = 'ECPF'
        print("CPF")
    else:
        identificacao = cnpj
        tipo_voucher = 'ECNPJ'
    
    # Limpar a identificação de qualquer formatação
    identificacao = identificacao.replace(".", "").replace("-", "").replace("/", "")
    
    # Validar o comprimento da identificação
    if len(identificacao) not in [11, 14]:
        return JsonResponse({'error': 'Número de documento inválido'}, status=400)
    
    # Buscar voucher disponível do tipo correto e não entregue
    voucher = Voucher.objects.filter(
        is_valid=True, 
        tipo=tipo_voucher,
        entregue=False
    ).first()
    
    # Se não houver voucher disponível, gerar novos
    if not voucher:
        # Criar um novo lote
        lote = Lote.objects.create()
        
        # Gerar 25 vouchers de cada tipo
        # Gerar 1000 novos vouchers do tipo necessário
        for _ in range(1000):
            code = generate_random_code()
            Voucher.objects.create(
                code=code,
                lote=lote,
                tipo=tipo_voucher
            )
        
        # Tentar obter um voucher novamente
        voucher = Voucher.objects.filter(
            is_valid=True, 
            tipo=tipo_voucher,
            entregue=False
        ).first()
        
        if not voucher:
            return JsonResponse({
                'error': f'Erro ao gerar novos vouchers do tipo {tipo_voucher}',
                'tipo_solicitado': tipo_voucher
            }, status=500)
    
    # Marcar voucher como entregue e inválido
    voucher.entregue = True
    voucher.save()
    
    # Se for ECNPJ e tiver razão social e nome fantasia, criar o cliente
    if tipo_voucher == 'ECNPJ' and razao_social and nome_fantasia:
        cliente, error, _ = create_client_and_order(
            identificacao=identificacao,
            voucher=voucher.code,
            razao_social=razao_social,
            nome_fantasia=nome_fantasia,
            cep=cep  # Passando o CEP
        )
        if error:
            return JsonResponse({'error': error}, status=400)
    
    return JsonResponse({
        'id': voucher.id,
        'code': voucher.code,
        'tipo': voucher.get_tipo_display(),
        'is_valid': voucher.is_valid,
        'entregue': voucher.entregue
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
            errors.append('Campos obrigatrios não preenchidos.')
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
                "nome_completo": razao_social,
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
            cliente_documento = cliente.cnpj or cliente.cpf  # Usar o número do pedido ao invés do documento
            response_data, error = consultar_status_pedido(cliente_documento)
            if error:
                return JsonResponse({'success': False, 'error': error})
            
            # Mapeamento dos status da API para os status do modelo
            status_mapping = {
                'Não Confirmada': '1',
                'Solicitação de Estorno': '2',
                'Estornada': '3',
                'Emissão liberada': '4',
                'Protocolo Gerado': '5',
                'Emitida': '6',
                'Revogada': '7',
                'Em Verificação': '8',
                'Em Validação': '9',
                'Recusada': '10',
                'Cancelada': '11',
                'Atribuído a Voucher': '12'
            }
            
        if error:
            print(f"Erro ao consultar cliente {cliente_documento}: {error}")
            
            
        if not response_data or not response_data.get("PossuiPedidosVinculados"):
            print(f"Sem pedidos vinculados para o cliente {cliente_documento}")
           

        pedidos = response_data.get("Pedidos", [])
        if not pedidos:
            print(f"Lista de pedidos vazia para o cliente {cliente_documento}")
            
        # Primeiro tenta encontrar um pedido emitido
        pedido_atualizar = response_data.get("Pedidos", [])
        
        # Se não encontrar pedido emitido, pega o mais recente por data
        if not pedido_atualizar:
            try:
                pedido_atualizar = max(
                    pedidos,
                    key=lambda x: datetime.strptime(x.get("DataVenda", "2000-01-01T00:00:00.000"), "%Y-%m-%dT%H:%M:%S.%f")
                )
            except (ValueError, TypeError) as e:
                print(f"Erro ao processar data do pedido para cliente {cliente_documento}: {e}")
                
       
        # Verifica se o pedido tem todos os campos necessário
        pedido_atualizar = pedidos[0] 
        print("StatusPedido:",pedido_atualizar.get("StatusPedido", "Não Confirmada"))
        cliente.pedido.pedido = pedido_atualizar.get("Pedido", "")
        cliente.pedido.protocolo = pedido_atualizar.get("Protocolo", "")
        cliente.pedido.hashVenda = pedido_atualizar.get("HashVenda", "")
        cliente.pedido.status = status_mapping.get(
            pedido_atualizar.get("StatusPedido", "Não Confirmada"),
            '1'  # default status
        )
        cliente.pedido.save()
        return JsonResponse({
            'success': True,
            'status': pedido_atualizar.get("Pedido", "Desconhecido"),
            'status_description': pedido_atualizar.get("StatusPedido", "Descrição não disponível"),
            'protocolo': pedido_atualizar.get("Protocolo", "Não disponível"),
            'hashVenda': pedido_atualizar.get("HashVenda", "Não disponível"),
            'data_status': pedido_atualizar.get("DataStatusPedido", "Não disponível"),
            'local_agendamento': pedido_atualizar.get("LocalAgendamento", "Não disponível"),
            'data_hora_agenda': pedido_atualizar.get("DataAgenda", "Não disponível")
        })
    except DadosCliente.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Cliente não encontrado'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Erro inesperado: {str(e)}'})

@require_POST
def atualizar_status_individual_view(request, cliente_id):
    try:
        cliente = DadosCliente.objects.get(id=cliente_id)
        # Usa o documento do cliente (CPF ou CNPJ) para consulta
        cliente_documento = cliente.cnpj or cliente.cpf
        if not cliente_documento:
            return JsonResponse({'success': False, 'error': 'Cliente sem documento (CPF/CNPJ)'})

        response_data, error = consultar_status_pedido(cliente_documento)
        
        if error:
            return JsonResponse({'success': False, 'error': error})

        if not response_data or not response_data.get("PossuiPedidosVinculados"):
            return JsonResponse({'success': False, 'error': 'Nenhum pedido vinculado encontrado'})

        # Mapeamento dos status da API para os status do modelo
        status_mapping = {
            'Não Confirmada': '1',
            'Solicitação de Estorno': '2',
            'Estornada': '3',
            'Emissão liberada': '4',
            'Protocolo Gerado': '5',
            'Emitida': '6',
            'Revogada': '7',
            'Em Verificação': '8',
            'Em Validação': '9',
            'Recusada': '10',
            'Cancelada': '11',
            'Atribuído a Voucher': '12'
        }

        pedidos = response_data.get("Pedidos", [])
        if not pedidos:
            return JsonResponse({'success': False, 'error': 'Nenhum pedido encontrado'})

        # Primeiro tenta encontrar um pedido emitido
        pedido_atualizar = next(
            (pedido for pedido in pedidos if pedido.get("StatusPedido") == "Emitida"),
            None
        )

        # Se não encontrar pedido emitido, pega o mais recente por data
        if not pedido_atualizar:
            try:
                pedido_atualizar = max(
                    pedidos,
                    key=lambda x: datetime.strptime(x.get("DataVenda", "2000-01-01T00:00:00.000"), "%Y-%m-%dT%H:%M:%S.%f")
                )
            except (ValueError, TypeError) as e:
                return JsonResponse({'success': False, 'error': f'Erro ao processar data do pedido: {str(e)}'})

        # Verifica se o pedido tem todos os campos necessários
        required_fields = ["Pedido", "Protocolo", "HashVenda", "StatusPedido"]
        if not all(pedido_atualizar.get(field) for field in required_fields):
            return JsonResponse({'success': False, 'error': 'Pedido com dados incompletos'})

        # Atualiza todos os campos do pedido
        cliente.pedido.pedido = pedido_atualizar.get("Pedido", "")
        cliente.pedido.protocolo = pedido_atualizar.get("Protocolo", "")
        cliente.pedido.hashVenda = pedido_atualizar.get("HashVenda", "")
        cliente.pedido.status = status_mapping.get(
            pedido_atualizar.get("StatusPedido", "Não Confirmada"),
            '1'  # default status
        )
        cliente.pedido.save()

        status_dict = dict(Pedidos.STATUS_CHOICES)
        status_key = get_key_by_value(status_dict, status["StatusPedido"])
        
        print("status")
        cliente.pedido.save()
        return JsonResponse({
            'success': True,
            'status': status_dict.get(cliente.pedido.status, "Desconhecido"),
            'status_description': pedido_atualizar.get("StatusPedido", "Descrição não disponível"),
            # 'protocolo': cliente.pedido.protocolo,
            # 'hashVenda': cliente.pedido.hashVenda
        })

    except DadosCliente.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Cliente não encontrado'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Erro inesperado: {str(e)}'})

@login_required
def voucher_statistics(request):
    # Aplicar filtros
    dados_cliente_filter = DadosClienteFilter(request.GET, queryset=DadosCliente.objects.filter(voucher__isnull=False).select_related('voucher', 'pedido').order_by('-created_at'))
    clients_with_vouchers = dados_cliente_filter.qs

    # Calcular estatísticas com base nos filtros aplicados
    total_clients = clients_with_vouchers.distinct().count()
    
    # Obter vouchers únicos dos clientes filtrados
    filtered_vouchers = Voucher.objects.filter(dadoscliente__in=clients_with_vouchers).distinct()
    
    # Contar vouchers por tipo
    active_vouchers_ecnpj = filtered_vouchers.filter(is_valid=True, tipo='ECNPJ').count()
    active_vouchers_ecpf = filtered_vouchers.filter(is_valid=True, tipo='ECPF').count()
    inactive_vouchers_ecnpj = filtered_vouchers.filter(is_valid=False, tipo='ECNPJ').count()
    inactive_vouchers_ecpf = filtered_vouchers.filter(is_valid=False, tipo='ECPF').count()

    # Adicionar paginação
    paginator = Paginator(clients_with_vouchers, 10)  # 10 itens por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'filter': dados_cliente_filter,
        'total_clients': total_clients,
        'active_vouchers_ecnpj': active_vouchers_ecnpj,
        'active_vouchers_ecpf': active_vouchers_ecpf,
        'inactive_vouchers_ecnpj': inactive_vouchers_ecnpj,
        'inactive_vouchers_ecpf': inactive_vouchers_ecpf,
        'clients_with_vouchers': page_obj,
        'page_obj': page_obj,
    }

    return render(request, 'home/index.html', context)
































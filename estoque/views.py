"""
Views para sistema de estoque com autenticação e CRUD para colaboradores e equipamentos.
Organizado seguindo boas práticas Pythonicas com imports agrupados e comentários descritivos.
"""

# Standard Library
import json
import re

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.db.models import Q, Sum, Max
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.core.paginator import Paginator
from django.forms import modelform_factory
from django.utils.timezone import now
from django.urls import reverse
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import ProtectedError

# Local Apps
from .forms import ColaboradorForm, EquipamentoForm, CertificacaoForm, CertificacaoFormSet, AgendamentoForm
from .models import Certificacao, Colaborador, Equipamento, Agendamento, PecaAgendada


class CustomLoginView(LoginView):
    """View personalizada para login que redireciona usuários autenticados"""
    
    template_name = 'estoque/home.html'
    
    def dispatch(self, request, *args, **kwargs):
        """Redireciona usuários já autenticados para o dashboard"""
        if request.user.is_authenticated:
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)


@login_required
def dashboard(request):
    """Página inicial após login"""
    return render(request, 'estoque/dashboard.html')


# ==============================================
# VIEWS PARA GESTÃO DE COLABORADORES
# ==============================================

@login_required
def cadastrar_colaborador(request):
    """
    Cadastra novo colaborador e cria usuário associado.
    Requer permissões de superusuário ou 'estoque.add_colaborador'.
    """
    # Verificação de permissões
    if not request.user.is_superuser and not request.user.has_perm('estoque.add_colaborador'):
        messages.error(request, 'Você não tem permissão para acessar esta página.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = ColaboradorForm(request.POST)
        if form.is_valid():
            try:
                colaborador = form.save(commit=False)
                nomes = colaborador.nome.strip().split()
                
                # Gera senha a partir dos 6 primeiros dígitos do CPF
                cpf_numeros = re.sub(r'[^0-9]', '', colaborador.cpf)
                senha = cpf_numeros[:6]
                
                # Cria usuário Django associado
                user = User.objects.create_user(
                    username=colaborador.matricula,
                    email=colaborador.email,
                    first_name=nomes[0],
                    last_name=' '.join(nomes[1:]) if len(nomes) > 1 else '',
                    password=senha
                )
                
                # Completa e salva o colaborador
                colaborador.user = user
                colaborador.data_criacao = timezone.now()
                colaborador.save()
                
                messages.success(request, 'Colaborador cadastrado com sucesso!')
                return redirect('cadastrar_colaborador')
                
            except Exception as e:
                messages.error(request, f'Erro ao cadastrar colaborador: {str(e)}')
    else:
        form = ColaboradorForm()

    return render(request, 'estoque/cadastro_colaborador.html', {
        'colaborador_form': form
    })
    
@login_required
def excluir_equipamento(request, pk):
    equipamento = get_object_or_404(Equipamento, pk=pk)
    
    if request.method == 'POST':
        try:
            equipamento.delete()
            messages.success(request, 'Equipamento excluído com sucesso.')
            return redirect('listar_equipamentos')
        except ProtectedError:
            messages.error(request, 'Não foi possível excluir o equipamento pois ele está vinculado a agendamentos.')
            return redirect('detalhe_equipamento', pk=pk)
    
    # Se não for POST, redireciona para a lista
    return redirect('listar_equipamentos')


@login_required
def listar_colaboradores(request):
    """Lista todos os colaboradores cadastrados"""
    colaboradores = Colaborador.objects.all()
    return render(request, 'estoque/colaboradores.html', {
        'colaboradores': colaboradores
    })


@login_required
def editar_colaborador(request, pk):
    """Edita informações de um colaborador existente"""
    colaborador = get_object_or_404(Colaborador, pk=pk)

    if request.method == 'POST':
        form = ColaboradorForm(request.POST, instance=colaborador)
        if form.is_valid():
            colaborador = form.save()
            # Atualiza dados do usuário associado
            colaborador.user.email = colaborador.email
            colaborador.user.first_name = colaborador.nome.split()[0]
            colaborador.user.last_name = ' '.join(colaborador.nome.split()[1:])
            colaborador.user.save()
            
            messages.success(request, 'Colaborador atualizado com sucesso!')
            return redirect('listar_colaboradores')
    else:
        form = ColaboradorForm(instance=colaborador)

    return render(request, 'estoque/editar_colaborador.html', {
        'form': form,
        'colaborador': colaborador
    })


@login_required
def excluir_colaborador(request, pk):
    """Remove colaborador e usuário associado"""
    colaborador = get_object_or_404(Colaborador, pk=pk)

    if request.method == 'POST':
        if colaborador.user:
            colaborador.user.delete()  # Remove usuário vinculado
        colaborador.delete()
        messages.success(request, 'Colaborador excluído com sucesso!')
        return redirect('listar_colaboradores')

    return render(request, 'estoque/excluir_colaborador.html', {
        'colaborador': colaborador
    })


# ==============================================
# VIEWS PARA GESTÃO DE EQUIPAMENTOS
# ==============================================

@login_required
def cadastrar_equipamento(request):
    """Cadastra novo equipamento com certificados associados"""
    if request.method == 'POST':
        form = EquipamentoForm(request.POST, request.FILES)
        
        if form.is_valid():
            equipamento = form.save()
            certificados_data = json.loads(request.POST.get('certificados_json', '[]'))
            
            # Processa cada certificado enviado
            for idx, cert_data in enumerate(certificados_data):
                anexo_file = request.FILES.get(f'anexo_{idx}')
                
                Certificacao.objects.create(
                    equipamento=equipamento,
                    nome_certificado=cert_data.get('nome'),
                    empresa_certificadora=cert_data.get('empresa'),
                    data_certificacao=cert_data.get('data') or None,
                    data_vencimento=cert_data.get('vencimento') or None,
                    codigo_certificado=cert_data.get('codigo'),
                    detalhes=cert_data.get('detalhes'),
                    anexo=anexo_file  # Pode ser None se não houver arquivo
                )

            messages.success(request, 'Equipamento cadastrado com sucesso!')
            return render(request, 'estoque/equipamento_cadastro.html', {
                'form': EquipamentoForm(),
                'qr_code': equipamento.qrcode.url,
                'exibir_modal': True
            })
        else:
            return render(request, 'estoque/equipamento_cadastro.html', {'form': form})
    else:
        form = EquipamentoForm()

    return render(request, 'estoque/equipamento_cadastro.html', {'form': form})

@login_required
def editar_equipamento(request, pk):
    equipamento = get_object_or_404(Equipamento, pk=pk)

    EquipamentoForm = modelform_factory(Equipamento, exclude=['qrcode'])
    
    if request.method == 'POST':
        form = EquipamentoForm(request.POST, request.FILES, instance=equipamento)
        formset = CertificacaoFormSet(request.POST, request.FILES, instance=equipamento)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('detalhe_equipamento', pk=equipamento.pk)
    else:
        form = EquipamentoForm(instance=equipamento)
        formset = CertificacaoFormSet(instance=equipamento)

    return render(request, 'estoque/equipamento_editar.html', {
        'form': form,
        'formset': formset,
        'equipamento': equipamento
    })


@login_required
def listar_equipamentos(request):
    """Lista equipamentos com possibilidade de busca"""
    busca = request.GET.get('q', '')
    equipamentos = Equipamento.objects.all()

    if busca:
        equipamentos = equipamentos.filter(
            Q(equipamento__icontains=busca) |
            Q(identificador__icontains=busca) |
            Q(registro__icontains=busca)
        )

    return render(request, 'estoque/equipamento_lista.html', {
        'equipamentos': equipamentos,
        'busca': busca
    })
    

@login_required
def detalhe_equipamento(request, pk):
    
    equipamento = get_object_or_404(Equipamento, pk=pk)
    today = timezone.now().date()
    return render(request, 'estoque/equipamento_detalhe.html', {
        'equipamento': equipamento,
        'today': today
    })


@login_required
def ler_qrcode(request):
    """Página para leitura de QRCode"""
    return render(request, 'estoque/qrcode_leitura.html')



@login_required
def estoque_resumido(request):
    search = request.GET.get('search', '')

    agrupados = (
        Equipamento.objects
        .filter(equipamento__icontains=search)
        .values('equipamento')
        .annotate(
            total_quantidade=Sum('quantidade'),
            ultimo_registro=Max('registro')
        )
        .order_by('equipamento')
    )

    equipamentos = []
    hoje = timezone.now().date()

    for item in agrupados:
        registros = Equipamento.objects.filter(equipamento=item['equipamento'])
        if not registros.exists():
            continue

        total_certificados = 0
        total_validos = 0
        total_sem_certificado = 0
        foto = None
        primeiro_registro = None

        for reg in registros:
            certificacoes = reg.certificacoes.all()
            qtd_certificados = certificacoes.count()
            total_certificados += qtd_certificados
            total_validos += sum(1 for c in certificacoes if c.data_vencimento and c.data_vencimento >= hoje)
            if qtd_certificados == 0:
                total_sem_certificado += 1
            if not foto and reg.foto:
                foto = reg.foto.url
            if not primeiro_registro:
                primeiro_registro = reg

        equipamentos.append({
            'equipamento': item['equipamento'],
            'total_quantidade': item['total_quantidade'],
            'foto': foto,
            'total_certificado': total_certificados,
            'total_valido': total_validos,
            'total_vencido': total_certificados - total_validos,
            'total_sem_certificado': total_sem_certificado,
            'registro': primeiro_registro.registro if primeiro_registro else None
        })

    # Paginação
    paginator = Paginator(equipamentos, 10)  # 10 por página
    page = request.GET.get('page')
    equipamentos_page = paginator.get_page(page)

    return render(request, 'estoque/estoque_resumido.html', {
        'equipamentos': equipamentos_page,
        'search': search,
        'paginator': paginator
    })


@login_required
def estoque_detalhado(request, nome_equipamento):
    equipamentos = Equipamento.objects.filter(equipamento=nome_equipamento)
    return render(request, 'estoque/estoque_detalhado.html', {
        'nome_equipamento': nome_equipamento,
        'equipamentos': equipamentos,
        'today': timezone.now().date()
    })
    

def autocomplete_equipamento(request):
    """Endpoint AJAX para autocompletar nomes de equipamentos"""
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        term = request.GET.get('term', '').upper()
        equipamentos = Equipamento.objects.filter(
            equipamento__icontains=term
        ).values_list('equipamento', flat=True).distinct()
        return JsonResponse(list(equipamentos), safe=False)
    
    
    

@login_required
def agendar_view(request):
    if request.method == 'POST':
        form = AgendamentoForm(request.POST)
        if form.is_valid():
            agendamento = form.save(commit=False)
            agendamento.save()

            pecas_ids = request.POST.get('pecas_ids', '')
            for pid in pecas_ids.split(','):
                if pid:
                    PecaAgendada.objects.create(agendamento=agendamento, equipamento_id=int(pid))

            # Verifica se é AJAX pelo cabeçalho ou pelo formato da resposta
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.accepts('application/json'):
                return JsonResponse({
                    'status': 'success',
                    'numero_agendamento': agendamento.numero_agendamento,
                    'redirect_url': reverse('sucesso_agendamento', kwargs={'numero': agendamento.numero_agendamento})
                })

            return redirect('sucesso_agendamento', numero=agendamento.numero_agendamento)

        # Tratamento de erros
        errors = {field: error.get_json_data() for field, error in form.errors.items()}
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.accepts('application/json'):
            return JsonResponse({'status': 'error', 'errors': errors}, status=400)
        
        return render(request, 'estoque/agendamento_form.html', {'form': form})
    
    form = AgendamentoForm()
    return render(request, 'estoque/agendamento_form.html', {'form': form})




def buscar_pecas_com_certificado(request):
    q = request.GET.get('q', '').strip()

    # IDs dos equipamentos já agendados
    pecas_agendadas_ids = list(PecaAgendada.objects.values_list('equipamento_id', flat=True))

    # Buscar equipamentos com certificado válido e que NÃO estão agendados
    equipamentos_disponiveis = Equipamento.objects.filter(
        Q(equipamento__icontains=q) | Q(identificador__icontains=q),
        certificacoes__data_vencimento__gte=now()
    ).exclude(pk__in=pecas_agendadas_ids).distinct()

    dados = []
    for p in equipamentos_disponiveis:
        cert = p.certificacoes.order_by('-data_vencimento').first()
        dados.append({
            'id': p.pk,
            'nome': p.equipamento,
            'identificador': p.identificador,
            'validade': cert.data_vencimento.strftime('%d/%m/%Y') if cert else '',
            'foto_url': p.foto.url if p.foto else '',
        })

    return JsonResponse({'resultados': dados})



def sucesso_agendamento(request, numero):
    return render(request, 'estoque/agendamento_sucesso.html', {'numero_agendamento': numero})


@login_required
def verificar_agendamentos_equipamento(request, pk):
    equipamento = get_object_or_404(Equipamento, pk=pk)
    pecas_agendadas = PecaAgendada.objects.filter(equipamento=equipamento).select_related('agendamento')
    
    agendamentos = []
    for peca in pecas_agendadas:
        agendamentos.append({
            'id': peca.agendamento.id,
            'numero': peca.agendamento.numero_agendamento,
            'solicitante': peca.agendamento.nome_solicitante,
            'data': peca.agendamento.data_hora_agendamento.strftime('%d/%m/%Y %H:%M')
        })
    
    return JsonResponse({
        'has_agendamentos': len(agendamentos) > 0,
        'agendamentos': agendamentos
    }, encoder=DjangoJSONEncoder)
    
    
@login_required
def lista_agendamento_view(request):
    return render(request, 'estoque/lista_agendamento.html')
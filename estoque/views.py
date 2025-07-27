"""
Views para sistema de estoque com autenticação e CRUD para colaboradores e equipamentos.
Organizado seguindo boas práticas Pythonicas com imports agrupados e comentários descritivos.
"""

# Standard Library
import json
import re

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
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
from django.db import transaction
from django.db import IntegrityError
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from datetime import datetime
import os
from django.conf import settings

# Local Apps
from .forms import ColaboradorForm, EquipamentoForm, CertificacaoForm, CertificacaoFormSet, AgendamentoForm, ChecklistSaidaForm, TermoRetiradaForm, DevolucaoMaterialForm, InventarioForm
from .models import Certificacao, Colaborador, Equipamento, Agendamento, PecaAgendada, SaidaMaterial, VerificacaoPeca, ChecklistSaida, TermoRetirada, DevolucaoMaterial, InventarioEquipamento


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
    Permite acesso a superusuários ou usuários nos grupos 'gestor' ou 'assistente-adm'
    """
    # Verificação de permissões
    if not (request.user.is_superuser or 
            request.user.groups.filter(name__in=['gestor', 'assistente-adm']).exists()):
        messages.error(request, 'Você não tem permissão para acessar esta página.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = ColaboradorForm(request.POST, user=request.user)
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
                
                # Adiciona os grupos selecionados ao usuário (se o campo existir)
                if 'grupos' in form.cleaned_data:
                    grupos = form.cleaned_data['grupos']
                    user.groups.set(grupos)
                
                # Completa e salva o colaborador
                colaborador.user = user
                colaborador.data_criacao = timezone.now()
                colaborador.save()
                
                messages.success(request, 'Colaborador cadastrado com sucesso!')
                return redirect('cadastrar_colaborador')
                
            except Exception as e:
                messages.error(request, f'Erro ao cadastrar colaborador: {str(e)}')
    else:
        form = ColaboradorForm(user=request.user)

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
    """
    View que exibe a lista de equipamentos detalhados e os modais de inventário.
    """
    equipamentos = Equipamento.objects.filter(equipamento=nome_equipamento).order_by('registro')
    
    # Criamos uma instância vazia do formulário para passar ao template,
    # embora não seja estritamente necessário, pois o modal tem seus próprios campos.
    form = InventarioForm()

    context = {
        'nome_equipamento': nome_equipamento,
        'equipamentos': equipamentos,
        'today': timezone.now().date(),
        'inventario_form': form, # Passando o form para o contexto
    }
    return render(request, 'estoque/estoque_detalhado.html', context)


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
            try:
                agendamento = form.save(commit=False)
                agendamento.status = 'AG'  # Definindo status como 'Agendado'
                agendamento.save()

                pecas_ids = request.POST.get('pecas_ids', '')
                if pecas_ids:
                    for pid in pecas_ids.split(','):
                        if pid:
                            PecaAgendada.objects.create(
                                agendamento=agendamento, 
                                equipamento_id=int(pid)
                            )

                # Resposta para requisições AJAX
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'numero_agendamento': agendamento.numero_agendamento,
                        'redirect_url': reverse('lista_agendamento')  # Alterado aqui
                    })

                # Redirecionamento tradicional
                return redirect('lista_agendamento')  # Alterado aqui

            except Exception as e:
                # Tratamento de erros para AJAX
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': str(e)
                    }, status=400)
                raise e

        # Formulário inválido
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            errors = {field: [str(error) for error in error_list] for field, error_list in form.errors.items()}
            return JsonResponse({
                'success': False,
                'errors': errors
            }, status=400)
        
        # Caso não seja AJAX e formulário inválido
        return render(request, 'estoque/agendamento_form.html', {'form': form})
    
    # GET request
    form = AgendamentoForm()
    return render(request, 'estoque/agendamento_form.html', {'form': form})


def buscar_pecas_com_certificado(request):
    q = request.GET.get('q', '').strip()
    data_atual = now()

    # Equipamentos em agendamentos ativos
    agendamentos_ativos = Agendamento.objects.filter(status__in=['AGENDADO'])
    pecas_em_uso_ids = PecaAgendada.objects.filter(
        agendamento__in=agendamentos_ativos
    ).values_list('equipamento_id', flat=True)

    # Equipamentos com certificação válida, ativos e não agendados
    equipamentos_disponiveis = Equipamento.objects.filter(
        Q(equipamento__icontains=q) | Q(identificador__icontains=q),
        certificacoes__data_vencimento__gte=data_atual,
        status='ATIVO'  # ← filtro importante aqui
    ).exclude(pk__in=pecas_em_uso_ids).distinct()

    # Montar resposta
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
    agendamentos = Agendamento.objects.all().order_by('-data_hora_agendamento')
    
    # Filtro por busca
    busca = request.GET.get('busca', '')
    if busca:
        agendamentos = agendamentos.filter(
            Q(numero_agendamento__icontains=busca) |
            Q(nome_solicitante__icontains=busca) |
            Q(matricula__icontains=busca) |
            Q(setor_solicitante__icontains=busca)
        )
    
    # Filtro por status
    status_filtro = request.GET.getlist('status')
    if status_filtro:
        agendamentos = agendamentos.filter(status__in=status_filtro)
    
    # Paginação
    paginator = Paginator(agendamentos, 10)  # 10 itens por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'estoque/lista_agendamento.html', {
        'page_obj': page_obj,
        'busca': busca,
        'status_filtro': status_filtro,
        'STATUS_CHOICES': Agendamento.STATUS_CHOICES
    })

@login_required
def agendamento_detalhe(request, pk):
    agendamento = get_object_or_404(Agendamento, pk=pk)
    pecas = PecaAgendada.objects.filter(agendamento=agendamento).select_related('equipamento')
    return render(request, 'estoque/agendamento_detalhe.html', {'agendamento': agendamento, 'pecas': pecas})

@login_required
def editar_agendamento(request, pk):
    agendamento = get_object_or_404(Agendamento, pk=pk)

    if request.method == 'POST':
        form = AgendamentoForm(request.POST, instance=agendamento)
        if form.is_valid():
            form.save()

            # Atualiza as peças agendadas (remove as antigas e adiciona as novas)
            pecas_ids = request.POST.get('pecas_ids', '')
            novas_pecas_ids = [int(pid) for pid in pecas_ids.split(',') if pid]

            # Remove peças que não estão mais
            PecaAgendada.objects.filter(agendamento=agendamento).exclude(equipamento_id__in=novas_pecas_ids).delete()

            # Adiciona novas peças (evita duplicatas)
            pecas_existentes = PecaAgendada.objects.filter(agendamento=agendamento).values_list('equipamento_id', flat=True)
            for pid in novas_pecas_ids:
                if pid not in pecas_existentes:
                    PecaAgendada.objects.create(agendamento=agendamento, equipamento_id=pid)

            return redirect('agendamento_detalhe', pk=agendamento.pk)
    else:
        form = AgendamentoForm(instance=agendamento)

    # Pegar as peças já agendadas
    pecas_agendadas = PecaAgendada.objects.filter(agendamento=agendamento).select_related('equipamento')

    # Buscar a certificação mais recente de cada peça
    for peca in pecas_agendadas:
        cert = peca.equipamento.certificacoes.order_by('-data_vencimento').first()
        peca.certificado_mais_recente = cert

    return render(
        request,
        'estoque/agendamento_editar.html',
        {
            'form': form,
            'agendamento': agendamento,
            'pecas_agendadas': pecas_agendadas,
        }
    )


@login_required
def excluir_agendamento(request, pk):
    agendamento = get_object_or_404(Agendamento, pk=pk)
    if request.method == 'POST':
        agendamento.delete()
        return redirect('lista_agendamento')
    return render(request, 'estoque/agendamento_excluir.html', {'agendamento': agendamento})


@login_required
def saida_material(request):
    agendamento = None
    
    if request.method == 'POST':
        # Buscar agendamento
        if 'buscar_agendamento' in request.POST:
            numero_agendamento = request.POST.get('numero_agendamento')
            try:
                agendamento = Agendamento.objects.get(numero_agendamento=numero_agendamento)
            except Agendamento.DoesNotExist:
                messages.error(request, 'Agendamento não encontrado!')
        
        # Registrar saída
        elif 'registrar_saida' in request.POST:
            agendamento_id = request.POST.get('agendamento_id')
            agendamento = get_object_or_404(Agendamento, pk=agendamento_id)
            
            if SaidaMaterial.objects.filter(agendamento=agendamento).exists():
                messages.error(request, 'Já existe uma saída registrada para este agendamento!')
            else:
                # Criar registro de saída usando dados do agendamento
                saida = SaidaMaterial.objects.create(
                    agendamento=agendamento,
                    observacoes=request.POST.get('observacoes', '')
                )

                # Criar checklist
                ChecklistSaida.objects.create(
                    saida=saida,
                    alguma_avaria='alguma_avaria' in request.POST,
                    validade_ok='validade_ok' in request.POST,
                    certificacao_ok='certificacao_ok' in request.POST,
                )

                # Criar termo de retirada
                TermoRetirada.objects.create(
                    saida=saida,
                    lido=True,
                    assinatura_base64=request.POST.get('assinatura_base64', '')
                )

                # Atualizar status do agendamento
                agendamento.status = 'RT'
                agendamento.save()
                
                # Atualizar estoque
                for peca in agendamento.pecas_agendadas.all():
                    peca.equipamento.quantidade -= 1
                    peca.equipamento.save()
                
                messages.success(request, 'Saída registrada com sucesso!')
                return redirect('lista_saidas')  # Removido o parâmetro agendamento_id

    return render(request, 'estoque/saida_material.html', {
        'agendamento': agendamento
    })
    
    
def lista_saidas(request):
    saidas = SaidaMaterial.objects.select_related(
        'agendamento', 'devolucao'
    ).all().order_by('-data_registro')
    
    return render(request, 'estoque/lista_saidas.html', {
        'saidas': saidas,
        'STATUS_CHOICES': Agendamento.STATUS_CHOICES
    })


def detalhe_saida(request, pk):
    saida = get_object_or_404(SaidaMaterial.objects.select_related('agendamento'), pk=pk)
    pecas = saida.agendamento.pecas_agendadas.select_related('equipamento').all()
    return render(request, 'estoque/detalhe_saida.html', {
        'saida': saida,
        'pecas': pecas
    })

def editar_saida(request, pk):
    saida = get_object_or_404(SaidaMaterial, pk=pk)
    if request.method == 'POST':
        # Lógica para edição aqui
        messages.success(request, 'Saída atualizada com sucesso!')
        return redirect('detalhe_saida', pk=saida.pk)
    return render(request, 'estoque/editar_saida.html', {'saida': saida})

def excluir_saida(request, pk):
    saida = get_object_or_404(SaidaMaterial, pk=pk)
    if request.method == 'POST':
        saida.delete()
        messages.success(request, 'Saída excluída com sucesso!')
        return redirect('lista_saidas')
    return render(request, 'estoque/confirmar_exclusao.html', {'saida': saida})



def devolucao_material(request):
    agendamento = None
    saida = None
    pecas = None
    checklist = None
    
    if request.method == 'POST':
        # Buscar agendamento
        if 'buscar_agendamento' in request.POST:
            numero_agendamento = request.POST.get('numero_agendamento')
            try:
                agendamento = Agendamento.objects.get(
                    Q(numero_agendamento=numero_agendamento) & 
                    Q(status='RT')  # Só permite devolver agendamentos com status Retirado
                )
                saida = agendamento.saida_material
                pecas = agendamento.pecas_agendadas.select_related('equipamento').all()
                checklist = saida.checklist
            except Agendamento.DoesNotExist:
                messages.error(request, 'Agendamento não encontrado ou já devolvido!')
        
        # Registrar devolução
        elif 'registrar_devolucao' in request.POST:
            form = DevolucaoMaterialForm(request.POST)
            if form.is_valid():
                saida_id = request.POST.get('saida_id')
                saida = get_object_or_404(SaidaMaterial, pk=saida_id)
                
                if hasattr(saida, 'devolucao'):
                    messages.error(request, 'Esta saída já foi devolvida!')
                else:
                    devolucao = form.save(commit=False)
                    devolucao.saida = saida
                    devolucao.save()
                    
                    messages.success(request, 'Devolução registrada com sucesso!')
                    return redirect('lista_saidas')
            else:
                messages.error(request, 'Por favor, corrija os erros abaixo.')
    
    return render(request, 'estoque/devolucao_material.html', {
        'agendamento': agendamento,
        'saida': saida,
        'pecas': pecas,
        'checklist': checklist,
        'form': DevolucaoMaterialForm()
    })
    
@login_required
def registrar_inventario(request, pk):
    equipamento = get_object_or_404(Equipamento, pk=pk)
    
    # Verifica se o equipamento está descartado
    if equipamento.status == 'DESCARTADO':
        messages.error(request, 'Este equipamento já está descartado e não pode ser inventariado!')
        return redirect('detalhe_equipamento', pk=pk)
        
    colaborador = Colaborador.objects.get(user=request.user)

    if request.method == 'POST':
        form = InventarioForm(request.POST)
        if form.is_valid():
            inventario = form.save(commit=False)
            inventario.equipamento = equipamento
            inventario.colaborador = colaborador
            
            # ✅ Salva sempre o inventário, com ou sem problema
            inventario.save()

            # ✅ Exibe mensagem conforme status do inventário
            if inventario.avaria or inventario.perda or inventario.nao_devolvido:
                messages.warning(request, 'Inventário registrado com problemas! O gestor será notificado.')
            else:
                messages.success(request, 'Inventário registrado sem problemas.')

            return redirect('detalhe_equipamento', pk=equipamento.pk)
        else:
            messages.error(request, 'Por favor, corrija os erros no formulário!')
    else:
        form = InventarioForm()

    return render(request, 'inventario/modal_form.html', {
        'equipamento': equipamento,
        'form': form
    })
    
    
@login_required
def inventario_problemas(request):
    """
    Exibe apenas os registros de inventário que possuem problemas 
    (avaria=True OU perda=True OU nao_devolvido=True)
    """
    inventarios_com_problemas = InventarioEquipamento.objects.filter(
        Q(avaria=True) | Q(perda=True) | Q(nao_devolvido=True)
    ).select_related('equipamento', 'colaborador').order_by('-data_inventario')

    context = {
        'inventarios': inventarios_com_problemas,
    }
    return render(request, 'estoque/inventario_problemas.html', context)


@login_required
def inventario_detalhe(request, pk):
    """
    Exibe os detalhes de um registro de inventário.
    """
    inventario = get_object_or_404(InventarioEquipamento, pk=pk)
    return render(request, 'estoque/inventario_detalhe.html', {'inventario': inventario})




def is_gestor(user):
    return user.groups.filter(name='gestor').exists() or user.is_superuser
@login_required
@user_passes_test(is_gestor, login_url='dashboard')
def remover_peca_estoque(request, pk):
    inventario = get_object_or_404(InventarioEquipamento, pk=pk)
    
    if request.method == 'POST':
        try:
            # Marcar o equipamento como descartado
            equipamento = inventario.equipamento
            equipamento.status = 'DESCARTADO'
            equipamento.data_descarte = timezone.now()
            
            # Usar apenas a observação do inventário como motivo
            equipamento.motivo_descarte = (
                f"Motivo do inventário: {inventario.observacao}\n"
                f"Descarte realizado por: {request.user.username} em {timezone.now().strftime('%d/%m/%Y %H:%M')}"
            )
            equipamento.save()

            # Marcar o inventário como descartado
            inventario.descarte = True
            inventario.save()

            messages.success(request, 'Peça marcada como descartada com sucesso!')
            return redirect('inventario_problemas')
        
        except Exception as e:
            messages.error(request, f'Erro ao marcar como descartado: {str(e)}')
            return redirect('inventario_detalhe', pk=pk)

    return redirect('inventario_detalhe', pk=pk)


def relatorio_inventario_pdf(request):
    INVENTARIO_CHOICES = {
        'GERAL': 'Inventário Geral',
        'PARCIAL': 'Inventário Parcial',
        'PERIODICO': 'Inventário Periódico',
        'ROTATIVO': 'Inventário Rotativo'
    }
    
    if request.method == 'POST':
        tipo_inventario = request.POST.get('tipo_inventario')
        data_inicio = request.POST.get('data_inicio')
        data_fim = request.POST.get('data_fim')
        
        try:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d') if data_inicio else None
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d') if data_fim else None
        except ValueError:
            return HttpResponse("Formato de data inválido. Use YYYY-MM-DD.")
        
        # Filtra apenas itens que foram inventariados (exclui os que nunca foram inventariados)
        inventarios = InventarioEquipamento.objects.all()
        
        if data_inicio and data_fim:
            inventarios = inventarios.filter(data_inventario__range=[data_inicio, data_fim])
        
        if tipo_inventario == 'PARCIAL':
            inventarios = inventarios.filter(avaria=True) | inventarios.filter(perda=True) | inventarios.filter(nao_devolvido=True)
        
        # Separar peças com e sem problemas
        inventarios_com_problemas = inventarios.filter(
            Q(avaria=True) | Q(perda=True) | Q(nao_devolvido=True)
        ).distinct()
        
        inventarios_sem_problemas = inventarios.exclude(
            Q(avaria=True) | Q(perda=True) | Q(nao_devolvido=True)
        ).distinct()
        
        total_inventariado = inventarios.count()
        total_descartes = inventarios.filter(equipamento__status='DESCARTADO').count()
        total_pendentes = total_inventariado - total_descartes
        
        context = {
            'inventarios_com_problemas': inventarios_com_problemas,
            'inventarios_sem_problemas': inventarios_sem_problemas,
            'tipo_inventario': INVENTARIO_CHOICES.get(tipo_inventario, ''),
            'data_inicio': data_inicio.strftime('%d/%m/%Y') if data_inicio else '',
            'data_fim': data_fim.strftime('%d/%m/%Y') if data_fim else '',
            'total_inventariado': total_inventariado,
            'total_descartes': total_descartes,
            'total_pendentes': total_pendentes,
        }
        
        template = get_template('estoque/relatorio_inventario_pdf.html')
        html = template.render(context)
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="relatorio_inventario_{timezone.now().date()}.pdf"'
        
        pisa_status = pisa.CreatePDF(
            html, 
            dest=response,
            encoding='UTF-8',
            link_callback=lambda uri, rel: os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, '')))
        
        if pisa_status.err:
            return HttpResponse('Erro ao gerar PDF')
        return response
    
    context = {
        'opcoes_inventario': INVENTARIO_CHOICES
    }
    return render(request, 'estoque/selecionar_relatorio.html', context)
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from .forms import ColaboradorForm, EquipamentoForm
from django.contrib.auth.models import User
from django.contrib import messages
import re
from .models import Colaborador, Equipamento
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from django.db.models import Sum, Max
from django.http import JsonResponse



class CustomLoginView(LoginView):
    template_name = 'estoque/home.html'
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

@login_required
def dashboard(request):
    return render(request, 'estoque/dashboard.html')


def cadastrar_colaborador(request):
    if not request.user.is_superuser and not request.user.has_perm('estoque.add_colaborador'):
        messages.error(request, 'Você não tem permissão para acessar esta página.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = ColaboradorForm(request.POST)
        if form.is_valid():
            try:
                colaborador = form.save(commit=False)
                nomes = colaborador.nome.strip().split()
                
                # Extrai os 6 primeiros dígitos do CPF para senha
                cpf_numeros = re.sub(r'[^0-9]', '', colaborador.cpf)
                senha = cpf_numeros[:6]
                
                # Criar usuário associado
                user = User.objects.create_user(
                    username=colaborador.matricula,
                    email=colaborador.email,
                    first_name=nomes[0],
                    last_name=' '.join(nomes[1:]) if len(nomes) > 1 else '',
                    password=senha
                )
                
                colaborador.user = user
                colaborador.data_criacao = timezone.now()  # Garante a data correta
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
def listar_colaboradores(request):
    colaboradores = Colaborador.objects.all()
    return render(request, 'estoque/colaboradores.html', {
        'colaboradores': colaboradores
    })
    
    
    
@login_required
def editar_colaborador(request, pk):
    colaborador = get_object_or_404(Colaborador, pk=pk)

    if request.method == 'POST':
        form = ColaboradorForm(request.POST, instance=colaborador)
        if form.is_valid():
            colaborador = form.save()
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
    colaborador = get_object_or_404(Colaborador, pk=pk)

    if request.method == 'POST':
        if colaborador.user:
            colaborador.user.delete()  # Apaga o User vinculado
        colaborador.delete()
        messages.success(request, 'Colaborador excluído com sucesso!')
        return redirect('listar_colaboradores')

    return render(request, 'estoque/excluir_colaborador.html', {
        'colaborador': colaborador
    })
    
@login_required
def cadastrar_equipamento(request):
    if request.method == 'POST':
        form = EquipamentoForm(request.POST, request.FILES)
        if form.is_valid():
            equipamento = form.save()
            messages.success(request, 'Equipamento cadastrado com sucesso!')
            return render(request, 'estoque/equipamento_cadastro.html', {
                'form': EquipamentoForm(),
                'qr_code': equipamento.qrcode.url,
                'exibir_modal': True
            })
    else:
        form = EquipamentoForm()

    return render(request, 'estoque/equipamento_cadastro.html', {'form': form})


@login_required
def listar_equipamentos(request):
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
    return render(request, 'estoque/equipamento_detalhe.html', {
        'equipamento': equipamento
    })
    
    
    
@login_required
def ler_qrcode(request):
    return render(request, 'estoque/qrcode_leitura.html')



@login_required
def estoque_resumido(request):
    agrupados = (
        Equipamento.objects
        .values('equipamento')
        .annotate(
            total_quantidade=Sum('quantidade'),
            ultimo_registro=Max('registro')  # CORRETO
        )
        .order_by('equipamento')
    )

    equipamentos = []
    for item in agrupados:
        registro = Equipamento.objects.filter(registro=item['ultimo_registro']).first()
        equipamentos.append({
            'equipamento': item['equipamento'],
            'total_quantidade': item['total_quantidade'],
            'foto': registro.foto.url if registro and registro.foto else None
        })

    return render(request, 'estoque/estoque_resumido.html', {
        'equipamentos': equipamentos
    })
    
    
def autocomplete_equipamento(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        term = request.GET.get('term', '').upper()
        equipamentos = Equipamento.objects.filter(equipamento__icontains=term).values_list('equipamento', flat=True).distinct()
        return JsonResponse(list(equipamentos), safe=False)
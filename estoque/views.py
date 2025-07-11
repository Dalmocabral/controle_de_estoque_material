from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from .forms import ColaboradorForm
from django.contrib.auth.models import User
from django.contrib import messages
import re
from .models import Colaborador
from django.shortcuts import get_object_or_404
from django.utils import timezone



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
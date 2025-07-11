from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from .forms import ColaboradorForm
from django.contrib.auth.models import User
from django.contrib import messages
import re


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
                colaborador.save()
                
                messages.success(request, 'Colaborador cadastrado com sucesso!')
                return redirect('cadastrar_colaborador')  # Redireciona para limpar o formulário
                
            except Exception as e:
                messages.error(request, f'Erro ao cadastrar colaborador: {str(e)}')
    else:
        form = ColaboradorForm()

    return render(request, 'estoque/cadastro_colaborador.html', {
        'colaborador_form': form
    })
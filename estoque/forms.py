from django import forms
from django.contrib.auth.models import User
from .models import Colaborador, Equipamento
from django.core.validators import validate_email
import re
from .models import AnexoCertificacao

class ColaboradorForm(forms.ModelForm):
    class Meta:
        model = Colaborador
        fields = ['matricula', 'nome', 'email', 'cpf', 'area', 'cargo']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Digite o nome completo'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@exemplo.com'
            }),
            'matricula': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de matrícula'
            }),
            'cpf': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '000.000.000-00',
                'data-mask': '000.000.000-00'
            }),
            'area': forms.Select(attrs={'class': 'form-select'}),
            'cargo': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def clean_nome(self):
        nome = self.cleaned_data.get('nome')
        return ' '.join(word.capitalize() for word in nome.split())
    
    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf')
        if not re.match(r'^\d{3}\.\d{3}\.\d{3}-\d{2}$', cpf):
            raise forms.ValidationError("Formato de CPF inválido. Use: 000.000.000-00")
        
        cpf_numeros = cpf.replace('.', '').replace('-', '')
        if Colaborador.objects.filter(cpf__contains=cpf_numeros).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise forms.ValidationError("Este CPF já está cadastrado.")
        
        return cpf
    
    def clean_matricula(self):
        matricula = self.cleaned_data.get('matricula')
        if User.objects.filter(username=matricula).exists():
            raise forms.ValidationError("Esta matrícula já está em uso.")
        if Colaborador.objects.filter(matricula=matricula).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise forms.ValidationError("Esta matrícula já está cadastrada.")
        return matricula
    
    def clean_matricula(self):
        matricula = self.cleaned_data.get('matricula')

        # Ignorar o user vinculado se for edição
        if self.instance and self.instance.user:
            if User.objects.filter(username=matricula).exclude(pk=self.instance.user.pk).exists():
                raise forms.ValidationError("Esta matrícula já está em uso.")
        else:
            if User.objects.filter(username=matricula).exists():
                raise forms.ValidationError("Esta matrícula já está em uso.")

        if Colaborador.objects.filter(matricula=matricula).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise forms.ValidationError("Esta matrícula já está cadastrada.")

        return matricula
    
    
class EquipamentoForm(forms.ModelForm):
    class Meta:
        model = Equipamento
        fields = [
            'equipamento', 'identificador', 'caracteristica', 'descricao_uso',
            'tipo_equipamento', 'quantidade', 'localizacao', 'foto',
            'data_certificacao', 'data_vencimento', 'empresa_certificacao',
            'codigo_certificado', 'detalhes_certificacao', 'anexo_certificacao'
        ]
        widgets = {
            'equipamento': forms.TextInput(attrs={'class': 'form-control'}),
            'identificador': forms.TextInput(attrs={'class': 'form-control'}),
            'caracteristica': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'descricao_uso': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'tipo_equipamento': forms.Select(attrs={'class': 'form-select'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control'}),
            'localizacao': forms.TextInput(attrs={'class': 'form-control'}),
            'foto': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'data_certificacao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_vencimento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'empresa_certificacao': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_certificado': forms.TextInput(attrs={'class': 'form-control'}),
            'detalhes_certificacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'anexo_certificacao': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        
        labels = {
            'equipamento': 'Nome do Equipamento:',
            'identificador': 'ID Único:',
            'caracteristica': 'Características Técnicas:',
            'descricao_uso': 'Descrição de Uso:',
            'tipo_equipamento': 'Tipo:',
            'quantidade': 'Quantidade em Estoque:',
            'localizacao': 'Local de Armazenamento:',
            'foto': 'Foto do Equipamento:',
            'data_certificacao': 'Data da Certificação:',
            'data_vencimento': 'Vencimento da Certificação:',
            'empresa_certificacao': 'Empresa Certificadora:',
            'codigo_certificado': 'Código do Certificado:',
            'anexo_certificacao': 'Detalhes Adicionais da Certificação:',
            # Se você ainda tivesse 'anexo_certificacao' aqui, poderia mudar seu label também
            # 'anexo_certificacao': 'Anexo de Certificação:',
        }

    def clean_equipamento(self):
        return self.cleaned_data['equipamento'].upper()

    def clean_localizacao(self):
        return self.cleaned_data['localizacao'].upper()

    def clean_empresa_certificacao(self):
        return self.cleaned_data['empresa_certificacao'].upper()



class AnexoCertificacaoForm(forms.ModelForm):
    class Meta:
        model = AnexoCertificacao
        fields = ['arquivo', 'descricao']
        widgets = {
            'arquivo': forms.ClearableFileInput(attrs={'class': 'form-control'}),  # apenas 1 arquivo
            'descricao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Descrição (opcional)'}),
        }
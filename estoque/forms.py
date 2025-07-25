from django import forms
from django.contrib.auth.models import User
from .models import Colaborador, Equipamento, Certificacao, Agendamento, PecaAgendada, ChecklistSaida, TermoRetirada, DevolucaoMaterial, InventarioEquipamento
from django.forms import inlineformset_factory
from django.core.validators import validate_email
import re


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
        }

    def clean_equipamento(self):
        return self.cleaned_data['equipamento'].upper()

    def clean_localizacao(self):
        return self.cleaned_data['localizacao'].upper()

class CertificacaoForm(forms.ModelForm):
    class Meta:
        model = Certificacao
        fields = [
            'nome_certificado', 'data_certificacao', 'data_vencimento',
            'empresa_certificadora', 'codigo_certificado', 'detalhes', 'anexo',
        ]
        widgets = {
            'nome_certificado': forms.TextInput(attrs={'class': 'form-control'}),
            'data_certificacao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_vencimento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'empresa_certificadora': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_certificado': forms.TextInput(attrs={'class': 'form-control'}),
            'detalhes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'anexo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

CertificacaoFormSet = inlineformset_factory(
    Equipamento,
    Certificacao,
    form=CertificacaoForm,
    extra=1,  # número de formulários extras a exibir
    can_delete=True
)


class AgendamentoForm(forms.ModelForm):
    class Meta:
        model = Agendamento
        fields = [
            'nome_solicitante', 'matricula', 'setor_solicitante',
            'local_uso', 'tipo_operacao', 'data_hora_agendamento'
        ]
        widgets = {
            'nome_solicitante': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome completo do solicitante'
            }),
            'matricula': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de matrícula'
            }),
            'setor_solicitante': forms.Select(attrs={
                'class': 'form-select'
            }),
            'local_uso': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Local onde o equipamento será utilizado'
            }),
            'tipo_operacao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descreva o tipo de operação que será realizada'
            }),
            'data_hora_agendamento': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
        }
        
        labels = {
            'nome_solicitante': 'Nome do Solicitante',
            'matricula': 'Matrícula',
            'setor_solicitante': 'Setor Solicitante',
            'local_uso': 'Local de Uso',
            'tipo_operacao': 'Tipo de Operação',
            'data_hora_agendamento': 'Data e Hora do Agendamento',
        }


class PecaAgendadaForm(forms.ModelForm):
    class Meta:
        model = PecaAgendada
        fields = ['equipamento']
        
        
class ChecklistSaidaForm(forms.ModelForm):
    class Meta:
        model = ChecklistSaida
        fields = ['alguma_avaria', 'validade_ok', 'certificacao_ok']
        widgets = {
            'alguma_avaria': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'validade_ok': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'certificacao_ok': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class TermoRetiradaForm(forms.ModelForm):
    class Meta:
        model = TermoRetirada
        fields = ['lido', 'assinatura_base64']
        widgets = {
            'lido': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'assinatura_base64': forms.HiddenInput(),
        }
        
        
class DevolucaoMaterialForm(forms.ModelForm):
    class Meta:
        model = DevolucaoMaterial
        fields = ['quantidade_devolvida', 'material_com_avaria', 'observacoes']
        widgets = {
            'observacoes': forms.Textarea(attrs={'rows': 3}),
        }
    



class InventarioForm(forms.ModelForm):
    class Meta:
        model = InventarioEquipamento
        fields = ['quantidade', 'descarte', 'perda', 'fora_validade', 'observacao']
        widgets = {
            'quantidade': forms.NumberInput(attrs={'class': 'form-control', 'required': True}),
            'descarte': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'perda': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'fora_validade': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'observacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
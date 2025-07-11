from django import forms
from .models import Colaborador
from django.core.validators import validate_email
import re

class ColaboradorForm(forms.ModelForm):
    class Meta:
        model = Colaborador
        fields = ['matricula', 'nome', 'email', 'cpf', 'data_admissao', 
                 'departamento', 'cargo', 'area', 'material_app']
        widgets = {
            'data_admissao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'cpf': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': '000.000.000-00',
                'data-mask': '000.000.000-00'
            }),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'matricula': forms.TextInput(attrs={'class': 'form-control'}),
            'departamento': forms.Select(attrs={'class': 'form-select'}),
            'cargo': forms.Select(attrs={'class': 'form-select'}),
            'area': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf')
        if not re.match(r'^\d{3}\.\d{3}\.\d{3}-\d{2}$', cpf):
            raise forms.ValidationError("Formato de CPF inválido. Use: 000.000.000-00")
        
        # Remove pontos e traço para verificar unicidade
        cpf_numeros = cpf.replace('.', '').replace('-', '')
        if Colaborador.objects.filter(cpf__contains=cpf_numeros).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise forms.ValidationError("Este CPF já está cadastrado.")
        
        return cpf
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            validate_email(email)
            if Colaborador.objects.filter(email=email).exclude(pk=self.instance.pk if self.instance else None).exists():
                raise forms.ValidationError("Este email já está cadastrado.")
        return email
    
    def clean_matricula(self):
        matricula = self.cleaned_data.get('matricula')
        if Colaborador.objects.filter(matricula=matricula).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise forms.ValidationError("Esta matrícula já está cadastrada.")
        return matricula
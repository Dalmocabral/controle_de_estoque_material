from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.utils import timezone

class Colaborador(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    matricula = models.CharField(max_length=20, unique=True)
    nome = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    cpf = models.CharField(
        max_length=14,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\d{3}\.\d{3}\.\d{3}-\d{2}$',
                message='CPF deve estar no formato: 000.000.000-00'
            )
        ]
    )
    data_criacao = models.DateTimeField(default=timezone.now)  # Correção aqui
    
    AREA_CHOICES = [
        ('OP', 'Operações'),
        ('ARM', 'Armazém'),
        ('MAT', 'Materiais'),
        ('MANU', 'Manutenção'),
    ]
    
    CARGO_CHOICES = [
        ('GER', 'Gerente'),
        ('CORD', 'Coordenador'),
        ('SUP', 'Supervisor'),
        ('OPR1', 'Operador I'),
        ('OPR2', 'Operador II'),
        ('AUX', 'Auxiliar'),
    ]
    
    area = models.CharField(max_length=6, choices=AREA_CHOICES)
    cargo = models.CharField(max_length=6, choices=CARGO_CHOICES)
    
    def save(self, *args, **kwargs):
        # Formata o nome com iniciais maiúsculas
        self.nome = ' '.join(word.capitalize() for word in self.nome.split())
        if not self.data_criacao:  # Se não tiver data de criação
            self.data_criacao = timezone.now()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.nome} ({self.matricula})"
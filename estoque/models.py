from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

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
    data_crate = models.DateField(null=True, blank=True)

    AREA = [
        ('OP', 'Operações'),
        ('ARM', 'Armazém'),
        ('MAT', 'Materiais'),
        ('MANU', 'Manutenção'),
        
    ]
    
    CARGOS = [
        ('GER', 'Gerente'),
        ('CORD', 'Coordenador'),
        ('SUP', 'Supervisor'),
        ('OPR1', 'Operador I'),
        ('OPR2', 'Operador II '),
        ('AUX', 'Auxiliar'),
    ]
    
    area = models.CharField(max_length=6, choices=AREA)
    cargo = models.CharField(max_length=6, choices=CARGOS)
    

    def __str__(self):
        return f"{self.nome} ({self.matricula})"
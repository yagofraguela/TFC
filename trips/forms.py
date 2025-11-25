from django import forms
from django.contrib.auth.models import User
from .models import Lugar

class AnadirParticipanteForm(forms.Form):
    usuario = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        label="Selecciona un usuario"
    )
    nombre_nuevo = forms.CharField(
        max_length=150,
        required=False,
        label="O crea un usuario nuevo"
    )

class CrearLugarForm(forms.ModelForm):
    class Meta:
        model = Lugar
        fields = ['nombre', 'descripcion']
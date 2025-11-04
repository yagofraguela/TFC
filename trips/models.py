
# Create your models here.
from django.db import models
from django.conf import settings
from decimal import Decimal

Usuario = settings.AUTH_USER_MODEL

class Lugar(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre


class MiembroLugar(models.Model):
    lugar = models.ForeignKey(Lugar, on_delete=models.CASCADE, related_name='miembros')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    fecha_union = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('lugar', 'usuario')

    def __str__(self):
        return f"{self.usuario} en {self.lugar}"


class Gasto(models.Model):
    lugar = models.ForeignKey(Lugar, on_delete=models.CASCADE, related_name='gastos')
    titulo = models.CharField(max_length=200)
    cantidad = models.DecimalField(max_digits=12, decimal_places=2)
    moneda = models.CharField(max_length=10, default='EUR')
    pagado_por = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='gastos_pagados')
    fecha = models.DateTimeField(auto_now_add=True)
    nota = models.TextField(blank=True)
    tipo_reparto = models.CharField(max_length=20, default='igual')  # igual / personalizado / porcentaje

    def __str__(self):
        return f"{self.titulo} - {self.cantidad} {self.moneda} ({self.lugar})"


class ParteGasto(models.Model):
    gasto = models.ForeignKey(Gasto, on_delete=models.CASCADE, related_name='partes')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    cantidad_parte = models.DecimalField(max_digits=12, decimal_places=2)
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    saldado = models.BooleanField(default=False)

    class Meta:
        unique_together = ('gasto', 'usuario')

    def __str__(self):
        return f"{self.usuario}: {self.cantidad_parte} ({self.gasto})"


class Liquidacion(models.Model):
    lugar = models.ForeignKey(Lugar, on_delete=models.CASCADE, related_name='liquidaciones')
    de_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='pagos_realizados')
    a_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='pagos_recibidos')
    cantidad = models.DecimalField(max_digits=12, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)
    nota = models.TextField(blank=True)

    def __str__(self):
        return f"{self.de_usuario} → {self.a_usuario}: {self.cantidad} ({self.lugar})"

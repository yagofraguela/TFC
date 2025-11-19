import os
import django
from decimal import Decimal

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tritrip.settings")
django.setup()

from django.contrib.auth.models import User
from trips.models import Lugar, MiembroLugar, Gasto, ParteGasto

# Limpiar datos antiguos
User.objects.all().delete()
Lugar.objects.all().delete()
MiembroLugar.objects.all().delete()
Gasto.objects.all().delete()
ParteGasto.objects.all().delete()

# Crear usuarios
user1 = User.objects.create_user(username='alice', password='1234')
user2 = User.objects.create_user(username='bob', password='1234')

# Crear lugares
lugar1 = Lugar.objects.create(nombre='Playa', descripcion='Lugar de vacaciones')
lugar2 = Lugar.objects.create(nombre='Montaña', descripcion='Excursión de fin de semana')

# Añadir miembros
MiembroLugar.objects.create(lugar=lugar1, usuario=user1)
MiembroLugar.objects.create(lugar=lugar1, usuario=user2)
MiembroLugar.objects.create(lugar=lugar2, usuario=user2)

# Crear gasto repartido automáticamente
gasto1 = Gasto.objects.create(lugar=lugar1, titulo='Cena', cantidad=Decimal('100.00'), moneda='EUR', pagado_por=user1, tipo_reparto='igual')
miembros = lugar1.miembros.all()
parte_cantidad = (gasto1.cantidad / miembros.count()).quantize(Decimal('0.01'))
for miembro in miembros:
    ParteGasto.objects.create(gasto=gasto1, usuario=miembro.usuario, cantidad_parte=parte_cantidad)

print("✅ Datos de prueba creados correctamente")

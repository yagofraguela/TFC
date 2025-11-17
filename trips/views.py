# /home/yago/TFC/trips/views.py
import json
from decimal import Decimal
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404
from django.views import View
from django.db import transaction
from .models import Lugar, MiembroLugar, Gasto, ParteGasto
from .utils import calcular_saldos_lugar, calcular_liquidaciones

# --- crear lugar (POST) ---
class CrearLugarView(View):
    def post(self, request):
        try:
            payload = json.loads(request.body)
            nombre = payload.get('nombre')
            descripcion = payload.get('descripcion', '')
            if not nombre:
                return HttpResponseBadRequest(json.dumps({'error': 'nombre requerido'}), content_type='application/json')
            lugar = Lugar.objects.create(nombre=nombre, descripcion=descripcion)
            return JsonResponse({'id': lugar.id, 'nombre': lugar.nombre, 'descripcion': lugar.descripcion}, status=201)
        except json.JSONDecodeError:
            return HttpResponseBadRequest(json.dumps({'error': 'JSON inválido'}), content_type='application/json')

# --- añadir miembro a lugar (POST) ---
class AñadirMiembroView(View):
    def post(self, request, lugar_id):
        try:
            payload = json.loads(request.body)
            usuario_id = payload.get('usuario_id')
            if not usuario_id:
                return HttpResponseBadRequest(json.dumps({'error': 'usuario_id requerido'}), content_type='application/json')
            lugar = get_object_or_404(Lugar, pk=lugar_id)
            miembro, created = MiembroLugar.objects.get_or_create(lugar=lugar, usuario_id=usuario_id)
            return JsonResponse({'lugar': lugar.id, 'usuario_id': usuario_id, 'creado': created})
        except json.JSONDecodeError:
            return HttpResponseBadRequest(json.dumps({'error': 'JSON inválido'}), content_type='application/json')

# --- crear gasto (POST) ---
class CrearGastoView(View):
    """
    POST /api/lugares/<id>/gastos/
    payload ejemplo:
    {
      "titulo": "Cena",
      "cantidad": "90.00",
      "moneda": "EUR",
      "pagado_por_id": 1,
      "tipo_reparto": "igual",  # o "personalizado"
      "partes": [ {"usuario_id": 1, "cantidad_parte": "30.00"}, ... ]  # opcional si tipo_reparto == "igual"
    }
    """
    @transaction.atomic
    def post(self, request, lugar_id):
        try:
            payload = json.loads(request.body)
            titulo = payload.get('titulo')
            cantidad = payload.get('cantidad')
            moneda = payload.get('moneda', 'EUR')
            pagado_por_id = payload.get('pagado_por_id')
            tipo_reparto = payload.get('tipo_reparto', 'igual')
            partes = payload.get('partes', None)

            if not all([titulo, cantidad, pagado_por_id]):
                return HttpResponseBadRequest(json.dumps({'error': 'titulo, cantidad y pagado_por_id son requeridos'}), content_type='application/json')

            lugar = get_object_or_404(Lugar, pk=lugar_id)
            gasto = Gasto.objects.create(
                lugar=lugar,
                titulo=titulo,
                cantidad=Decimal(str(cantidad)),
                moneda=moneda,
                pagado_por_id=pagado_por_id,
                tipo_reparto=tipo_reparto
            )

            # si reparto igual y no se pasan partes, crear partes a partir de MiembroLugar
            if tipo_reparto == 'igual' and not partes:
                miembros = list(MiembroLugar.objects.filter(lugar=lugar).values_list('usuario_id', flat=True))
                if not miembros:
                    raise ValueError('No hay miembros en el lugar para repartir')
                n = len(miembros)
                parte = (Decimal(str(cantidad)) / Decimal(n)).quantize(Decimal('0.01'))
                for uid in miembros:
                    ParteGasto.objects.create(gasto=gasto, usuario_id=uid, cantidad_parte=parte)
            else:
                # se esperan partes dadas por el cliente
                if not partes:
                    return HttpResponseBadRequest(json.dumps({'error': 'partes requeridas para tipo_reparto personalizado'}), content_type='application/json')
                total = Decimal('0.00')
                for p in partes:
                    uid = p.get('usuario_id')
                    cant = Decimal(str(p.get('cantidad_parte', '0.00')))
                    ParteGasto.objects.create(gasto=gasto, usuario_id=uid, cantidad_parte=cant)
                    total += cant
                if total != Decimal(str(cantidad)):
                    return HttpResponseBadRequest(json.dumps({'error': 'suma de partes no coincide con cantidad total', 'total_partes': str(total)}), content_type='application/json')

            return JsonResponse({'gasto_id': gasto.id, 'titulo': gasto.titulo}, status=201)
        except json.JSONDecodeError:
            return HttpResponseBadRequest(json.dumps({'error': 'JSON inválido'}), content_type='application/json')
        except ValueError as e:
            return HttpResponseBadRequest(json.dumps({'error': str(e)}), content_type='application/json')

# --- editar gasto (PUT) ---
class EditarGastoView(View):
    @transaction.atomic
    def put(self, request, gasto_id):
        try:
            payload = json.loads(request.body)
            gasto = get_object_or_404(Gasto, pk=gasto_id)
            titulo = payload.get('titulo')
            cantidad = payload.get('cantidad')
            moneda = payload.get('moneda')
            tipo_reparto = payload.get('tipo_reparto')
            partes = payload.get('partes', None)

            if titulo is not None:
                gasto.titulo = titulo
            if cantidad is not None:
                gasto.cantidad = Decimal(str(cantidad))
            if moneda is not None:
                gasto.moneda = moneda
            if tipo_reparto is not None:
                gasto.tipo_reparto = tipo_reparto
            gasto.save()

            if partes is not None:
                # eliminar partes previas y recrear
                gasto.partes.all().delete()
                total = Decimal('0.00')
                for p in partes:
                    uid = p.get('usuario_id')
                    cant = Decimal(str(p.get('cantidad_parte', '0.00')))
                    ParteGasto.objects.create(gasto=gasto, usuario_id=uid, cantidad_parte=cant)
                    total += cant
                if total != gasto.cantidad:
                    return HttpResponseBadRequest(json.dumps({'error': 'suma de partes no coincide con cantidad total'}), content_type='application/json')

            return JsonResponse({'ok': True})
        except json.JSONDecodeError:
            return HttpResponseBadRequest(json.dumps({'error': 'JSON inválido'}), content_type='application/json')

    # permitir DELETE también aquí o usar vista separada
    def delete(self, request, gasto_id):
        gasto = get_object_or_404(Gasto, pk=gasto_id)
        gasto.delete()
        return JsonResponse({'ok': True})

# --- resumen del lugar: totales y deudas sugeridas ---
class ResumenLugarView(View):
    def get(self, request, lugar_id):
        lugar = get_object_or_404(Lugar, pk=lugar_id)
        saldos = calcular_saldos_lugar(lugar)  # dict user_id -> Decimal
        # transformar a info legible
        detalle = {}
        from django.contrib.auth import get_user_model
        User = get_user_model()
        for uid, saldo in saldos.items():
            user = User.objects.filter(pk=uid).first()
            detalle[user.username if user else str(uid)] = float(saldo)

        # liquidaciones sugeridas
        liquid = calcular_liquidaciones(saldos)
        liquid_readable = []
        for de, a, cantidad in liquid:
            u_de = User.objects.filter(pk=de).first()
            u_a = User.objects.filter(pk=a).first()
            liquid_readable.append({
                'de_usuario': u_de.username if u_de else str(de),
                'a_usuario': u_a.username if u_a else str(a),
                'cantidad': float(cantidad)
            })

        # totales
        total_gastado = float(sum([g.cantidad for g in lugar.gastos.all()]))
        return JsonResponse({
            'lugar': lugar.nombre,
            'total_gastado': total_gastado,
            'saldos': detalle,
            'liquidaciones_sugeridas': liquid_readable
        })

# --- listar gastos de un lugar (GET) ---
class ListaGastosLugarView(View):
    def get(self, request, lugar_id):
        lugar = get_object_or_404(Lugar, pk=lugar_id)
        gastos = []
        for g in lugar.gastos.all().order_by('-fecha'):
            partes = [{'usuario_id': p.usuario_id, 'cantidad_parte': float(p.cantidad_parte)} for p in g.partes.all()]
            gastos.append({
                'id': g.id,
                'titulo': g.titulo,
                'cantidad': float(g.cantidad),
                'moneda': g.moneda,
                'pagado_por_id': g.pagado_por_id,
                'tipo_reparto': g.tipo_reparto,
                'partes': partes,
                'fecha': g.fecha.isoformat()
            })
        return JsonResponse(gastos, safe=False)

class DetalleLugarView(View):
    def get(self, request, lugar_id):
        lugar = get_object_or_404(Lugar, id=lugar_id)

        miembros = MiembroLugar.objects.filter(lugar=lugar).select_related("usuario")

        lista_miembros = [
            {
                "id": m.usuario.id,
                "username": m.usuario.username
            }
            for m in miembros
        ]

        return JsonResponse({
            "id": lugar.id,
            "nombre": lugar.nombre,
            "fecha_creacion": lugar.fecha_creacion,
            "miembros": lista_miembros
        })

class ListaLugaresView(View):
    def get(self, request):
        lugares = Lugar.objects.all().values('id', 'nombre', 'descripcion', 'fecha_creacion')
        return JsonResponse(list(lugares), safe=False)

        
def prueba(request):
    return JsonResponse({'mensaje': 'Esto es una prueba desde TriTrip!'})

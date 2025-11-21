# /home/yago/TFC/trips/views.py
import json
from decimal import Decimal
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404
from django.views import View
from django.db import transaction
from .models import Lugar, MiembroLugar, Gasto, ParteGasto
from .utils import calcular_saldos_lugar, calcular_liquidaciones
from django.shortcuts import render
from django.shortcuts import render

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
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from decimal import Decimal
from .models import Lugar, Gasto, ParteGasto, MiembroLugar


class CrearGastoFormView(View):
    def get(self, request, lugar_id):
        lugar = get_object_or_404(Lugar, pk=lugar_id)
        miembros = MiembroLugar.objects.filter(lugar=lugar)

        return render(request, "trips/crear_gasto.html", {
            "lugar": lugar,
            "miembros": miembros
        })

    def post(self, request, lugar_id):
        lugar = get_object_or_404(Lugar, pk=lugar_id)

        titulo = request.POST.get("titulo")
        cantidad = request.POST.get("cantidad")
        pagado_por = request.POST.get("pagado_por")
        seleccionados = request.POST.getlist("usuarios")

        if not titulo or not cantidad or not pagado_por or not seleccionados:
            return render(request, "crear_gasto.html", {
                "lugar": lugar,
                "miembros": MiembroLugar.objects.filter(lugar=lugar),
                "error": "Todos los campos son obligatorios"
            })

        cantidad = Decimal(cantidad)
        n = len(seleccionados)
        parte = (cantidad / n).quantize(Decimal("0.01"))

        gasto = Gasto.objects.create(
            lugar=lugar,
            titulo=titulo,
            cantidad=cantidad,
            moneda="EUR",
            pagado_por_id=pagado_por,
            tipo_reparto="igual"
        )

        for uid in seleccionados:
            ParteGasto.objects.create(
                gasto=gasto,
                usuario_id=uid,
                cantidad_parte=parte
            )

        return redirect(f"/lugares/{lugar.id}/")


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

# views.py (código sugerido para DetalleLugarView)
class DetalleLugarView(View):
    def get(self, request, lugar_id):
        lugar = get_object_or_404(Lugar, id=lugar_id)
        
        # OBTENER LOS OBJETOS NECESARIOS:
        miembros = lugar.miembros.select_related('usuario')
        gastos = lugar.gastos.select_related('pagado_por').order_by('-fecha')

        # Calcular total de gastos (esto ya lo tenías)
        total_gastos = sum([g.cantidad for g in gastos])
        moneda = gastos.first().moneda if gastos.exists() else "EUR"

        # Pasar a plantilla (contexto completo)
        return render(request, "trips/detalle_lugar.html", {
            "lugar": lugar,
            "miembros": miembros,   # <--- AÑADIDO
            "gastos": gastos,       # <--- AÑADIDO
            "total_gastos": total_gastos,
            "moneda": moneda
        })

class ListaLugaresHTMLView(View):
    def get(self, request):
        lugares = Lugar.objects.all()
        return render(request, "trips/lugares.html", {"lugares": lugares})


        
def prueba(request):
    return JsonResponse({'mensaje': 'Esto es una prueba desde TriTrip!'})


def dashboard(request):
    lugares = Lugar.objects.all()
    return render(request, 'trips/dashboard.html', {'lugares': lugares})


class DashboardView(View):
    def get(self, request):
        lugares = Lugar.objects.all()
        lugares_data = []

        for lugar in lugares:
            total_gastos = sum([g.cantidad for g in lugar.gastos.all()])
            moneda = lugar.gastos.first().moneda if lugar.gastos.exists() else "EUR"
            lugares_data.append({
                "lugar": lugar,
                "total_gastos": total_gastos,
                "moneda": moneda
            })

        return render(request, "trips/dashboard.html", {
            "lugares_data": lugares_data
        })

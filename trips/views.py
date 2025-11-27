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
from .forms import AnadirParticipanteForm
from django.contrib.auth.models import User
from .forms import CrearLugarForm
from decimal import Decimal


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
            return render(request, "trips/crear_gasto.html", {
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
# trips/views.py


class DetalleLugarView(View):
    def get(self, request, lugar_id):
        lugar = get_object_or_404(Lugar, id=lugar_id)
        miembros = lugar.miembros.select_related('usuario')
        gastos = lugar.gastos.select_related('pagado_por').order_by('-fecha')
        total_gastos = sum([g.cantidad for g in gastos])
        moneda = gastos.first().moneda if gastos.exists() else "EUR"

        # --- calcular saldos correctamente ---
        saldos = {m.usuario.id: Decimal('0.00') for m in miembros}

        for gasto in gastos:
            pagador_id = gasto.pagado_por.id
            for parte in gasto.partes.all():
                uid = parte.usuario.id
                if uid != pagador_id:
                    # el usuario debe su parte
                    saldos[uid] -= parte.cantidad_parte
                    # el pagador recibe esa parte
                    saldos[pagador_id] += parte.cantidad_parte

        # --- generar deudas ---
        deudores = {uid: s for uid, s in saldos.items() if s < 0}  # saldo negativo = debe
        acreedores = {uid: s for uid, s in saldos.items() if s > 0}  # saldo positivo = recibe

        deudas = []

        for de_id, de_saldo in deudores.items():
            deuda_restante = -de_saldo  # convertir a positivo
            for a_id, a_saldo in list(acreedores.items()):
                if a_saldo <= 0:
                    continue
                pago = min(deuda_restante, a_saldo)
                if pago > 0:
                    de_user = miembros.get(usuario_id=de_id).usuario
                    a_user = miembros.get(usuario_id=a_id).usuario
                    deudas.append({
                        "de": de_user.username,
                        "a": a_user.username,
                        "cantidad": float(pago)
                    })
                    deuda_restante -= pago
                    acreedores[a_id] -= pago
                if deuda_restante <= 0:
                    break

        return render(request, "trips/detalle_lugar.html", {
            "lugar": lugar,
            "miembros": miembros,
            "gastos": gastos,
            "total_gastos": total_gastos,
            "moneda": moneda,
            "deudas": deudas
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

        # 1️⃣ Obtener el valor del filtro por usuario (opcional)
        user_filter = request.GET.get("user", "")

        # 2️⃣ Obtener todos los lugares
        lugares = Lugar.objects.all()

        # 3️⃣ Si hay filtro, solo mostrar lugares donde ese usuario es miembro
        if user_filter:
            lugares = lugares.filter(miembros__usuario__id=user_filter).distinct()

        # 4️⃣ Preparar información de cada lugar
        lugares_data = []
        for lugar in lugares:
            total_gastos = sum([g.cantidad for g in lugar.gastos.all()])
            moneda = lugar.gastos.first().moneda if lugar.gastos.exists() else "EUR"

            lugares_data.append({
                "lugar": lugar,
                "total_gastos": total_gastos,
                "moneda": moneda
            })

        # 5️⃣ Obtener todos los usuarios que aparecen en miembros (para el filtro)
        todos_los_miembros = MiembroLugar.objects.select_related("usuario").all().distinct()

        # 6️⃣ Render
        return render(request, "trips/dashboard.html", {
            "lugares_data": lugares_data,
            "todos_los_miembros": todos_los_miembros,
            "user_filter": user_filter
        })


class AnadirParticipanteView(View):
    template_name = "trips/anadir_participante.html"

    def get(self, request, pk):
        lugar = get_object_or_404(Lugar, pk=pk)
        form = AnadirParticipanteForm()
        return render(request, self.template_name, {
            "lugar": lugar,
            "form": form
        })

    def post(self, request, pk):
        lugar = get_object_or_404(Lugar, pk=pk)
        form = AnadirParticipanteForm(request.POST)

        if form.is_valid():
            usuario = form.cleaned_data.get("usuario")
            nombre_nuevo = form.cleaned_data.get("nombre_nuevo")

            # 🔹 Verificar existencia antes de crear
            if not usuario and nombre_nuevo:
                usuario, created = User.objects.get_or_create(username=nombre_nuevo)

            if not usuario:
                form.add_error(None, "Debes seleccionar un usuario o escribir uno nuevo.")
                return render(request, self.template_name, {
                    "lugar": lugar,
                    "form": form
                })

            # Crear relación MiembroLugar
            MiembroLugar.objects.get_or_create(lugar=lugar, usuario=usuario)

            return redirect("detalle_lugar", lugar_id=lugar.id)

        return render(request, self.template_name, {
            "lugar": lugar,
            "form": form
        })



class CrearLugarView(View):
    template_name = "trips/crear_lugar.html"

    def get(self, request):
        # Mostrar el formulario
        form = CrearLugarForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        # Procesar el formulario
        form = CrearLugarForm(request.POST)
        if form.is_valid():
            lugar = form.save()
            return redirect("detalle_lugar", lugar_id=lugar.id)
        return render(request, self.template_name, {"form": form})

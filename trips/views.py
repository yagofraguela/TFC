
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View
from django.db.models import Sum
from decimal import Decimal
from .models import Lugar, Gasto, ParteGasto, MiembroLugar


def prueba(request):
    return JsonResponse({'mensaje': 'Esto es una prueba desde TriTrip!'})


class BalanceLugarView(View):
    def get(self, request, lugar_id):
        lugar = get_object_or_404(Lugar, id=lugar_id)

        miembros = MiembroLugar.objects.filter(lugar=lugar).select_related('usuario')

        balances = {}

        for miembro in miembros:
            usuario = miembro.usuario

            total_pagado = (
                Gasto.objects.filter(lugar=lugar, pagado_por=usuario)
                .aggregate(Sum('cantidad'))['cantidad__sum'] or Decimal('0.00')
            )

            total_debe = (
                ParteGasto.objects.filter(gasto__lugar=lugar, usuario=usuario)
                .aggregate(Sum('cantidad_parte'))['cantidad_parte__sum'] or Decimal('0.00')
            )

            saldo = total_pagado - total_debe

            balances[usuario.username] = {
                'total_pagado': float(total_pagado),
                'total_debe': float(total_debe),
                'saldo': float(saldo)
            }

        return JsonResponse({
            'lugar': lugar.nombre,
            'balances': balances
        })

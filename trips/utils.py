from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

def calcular_saldos_lugar(lugar):
    """
    Devuelve un diccionario {usuario_id: saldo}.
    Saldo = total_pagado - total_debido (positivo => le deben, negativo => debe).
    """
    pagado = defaultdict(Decimal)
    debido = defaultdict(Decimal)

    for gasto in lugar.gastos.select_related('pagado_por').prefetch_related('partes'):
        pagado[gasto.pagado_por_id] += gasto.cantidad
        for parte in gasto.partes.all():
            debido[parte.usuario_id] += parte.cantidad_parte

    usuarios = set(list(pagado.keys()) + list(debido.keys()))
    saldos = {}
    for uid in usuarios:
        saldo = pagado.get(uid, Decimal('0.00')) - debido.get(uid, Decimal('0.00'))
        saldos[uid] = saldo.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return saldos


def calcular_liquidaciones(saldos):
    """
    Genera una lista de liquidaciones recomendadas.
    saldos: {usuario_id: Decimal}
    Devuelve lista [(de_usuario_id, a_usuario_id, cantidad)]
    """
    acreedores = []
    deudores = []

    for uid, saldo in saldos.items():
        if saldo > 0:
            acreedores.append([uid, saldo])
        elif saldo < 0:
            deudores.append([uid, -saldo])

    acreedores.sort(key=lambda x: x[1], reverse=True)
    deudores.sort(key=lambda x: x[1], reverse=True)

    liquidaciones = []
    i = j = 0

    while i < len(acreedores) and j < len(deudores):
        acreedor, cantidad_a_recibir = acreedores[i]
        deudor, cantidad_a_pagar = deudores[j]

        transferencia = min(cantidad_a_recibir, cantidad_a_pagar)
        liquidaciones.append((deudor, acreedor, transferencia))

        acreedores[i][1] -= transferencia
        deudores[j][1] -= transferencia

        if acreedores[i][1] == 0:
            i += 1
        if deudores[j][1] == 0:
            j += 1

    return liquidaciones

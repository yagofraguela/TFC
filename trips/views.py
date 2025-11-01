from django.http import JsonResponse


def prueba(request):
    return JsonResponse({'mensaje': 'Esto es una prueba desde TriTrip!'})

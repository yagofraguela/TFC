📌 TriTrips – Gestión de viajes, gastos y participantes

TriTrips es una aplicación web desarrollada con Django que permite gestionar viajes, añadir participantes, registrar gastos y calcular automáticamente la parte correspondiente de cada usuario. Está diseñada para ser intuitiva, rápida y visualmente clara.

Este proyecto fue realizado como práctica de desarrollo web, incluyendo diseño de frontend, backend, base de datos, autenticación y documentación de API.

📚 Tabla de contenidos

Características principales

Tecnologías utilizadas

Arquitectura del proyecto

Instalación

Ejecución del proyecto

Estructura de directorios

Modelos del sistema

Endpoints principales

Uso del sistema

Estilo visual y elección de colores

Herramientas utilizadas durante el desarrollo

Reiniciar la base de datos

Autor

🚀 Características principales

✔️ Creación y gestión de lugares (destinos)
✔️ Añadir participantes a cada viaje
✔️ Registrar gastos compartidos y dividirlos automáticamente
✔️ Panel de control (Dashboard) claro y moderno
✔️ Filtros por usuarios
✔️ Eliminación de lugares con botón dedicado
✔️ Validación automática de formularios
✔️ API documentada con Swagger
✔️ Comprobación de consistencia mediante un agente Gemini

🛠️ Tecnologías utilizadas
Backend

Django 4.x

Python 3.10+

SQLite (por simplicidad en desarrollo)

Django Template Engine

Django Rest Framework

Swagger / drf-yasg (documentación API)

Frontend

HTML5 + CSS3

Estilo personalizado (verde + blanco)

Plantillas reutilizables (extends/base.html)

Desarrollo

Visual Studio Code

Máquina Virtual con VirtualBox (entorno aislado)

Navegador Firefox / Mozilla para pruebas visuales

Postman para pruebas de API

Gemini (agente IA) para verificación y control de calidad

📦 Instalación
1️⃣ Clonar el repositorio
git clone https://github.com/yagofraguela/TFC
cd TriTrips

2️⃣ Crear un entorno virtual
python3 -m venv venv
source venv/bin/activate

3️⃣ Instalar dependencias
pip install -r requirements.txt

4️⃣ Aplicar migraciones
python manage.py migrate

5️⃣ Crear superusuario
python manage.py createsuperuser

▶️ Ejecución del proyecto
python manage.py runserver


La aplicación estará disponible en
👉 http://127.0.0.1:8000

🧩 Modelos del sistema
Lugar

Representa un destino o viaje.

MiembroLugar

Usuarios que participan en un viaje.

Gasto

Gastos realizados en un destino.

ParteGasto

Cálculo automático de cuánto debe pagar cada participante.

El sistema garantiza integridad y relaciones correctas mediante claves externas.

🔗 Endpoints principales
📍 Lugares
Método	Endpoint	Descripción
GET	/lugares/	Lista de lugares
GET	/lugares/<id>/	Detalle del lugar
POST	/lugares/crear/	Crear nuevo lugar
POST	/lugares/<id>/eliminar/	Eliminar lugar
💸 Gastos
Método	Endpoint	Descripción
POST	/lugares/<id>/gastos/crear/	Crear un gasto
GET	/api/gastos/	Lista de gastos (API REST)
👥 Participantes

| POST | /lugares/<id>/anadir-participante/ | Añadir participante |

🖥️ Uso del sistema

Crear un nuevo viaje desde el dashboard.

Añadir participantes al viaje.

Registrar gastos indicando:

descripción

cantidad

quién pagó

El sistema divide el gasto entre participantes.

El usuario puede filtrar la vista por participantes.

Un botón permite eliminar el lugar completo si se desea resetear.

🎨 Estilo visual y elección de colores

La aplicación utiliza un diseño basado en tonos verde y blanco, buscando transmitir claridad, organización y sensación de aplicación moderna.
El verde fue escogido por ser un color asociado a:

equilibrio y control financiero (relacionado con la gestión de gastos),

armonía y facilidad de lectura,

contraste limpio con el fondo blanco.

Además, permite destacar elementos importantes como botones, banners o cabeceras sin saturar visualmente.

🧪 Herramientas utilizadas durante el desarrollo

Visual Studio Code: editor principal.

VirtualBox: entorno aislado para ejecutar Django.

Firefox/Mozilla: comprobación de diseño responsive y consola.

Postman: pruebas de API.

Swagger: documentación automática.

Gemini: validación inteligente de estructura, endpoints y coherencia.

♻️ Reiniciar la base de datos

Si quieres borrar todos los datos manteniendo las tablas:

python manage.py shell

from trips.models import Lugar, MiembroLugar, Gasto, ParteGasto
Lugar.objects.all().delete()
MiembroLugar.objects.all().delete()
Gasto.objects.all().delete()
ParteGasto.objects.all().delete()


Si quieres empezar completamente desde cero:

rm db.sqlite3
python manage.py migrate

👤 Autor

Yago — Desarrollador Web
Estudiante de desarrollo de aplicaciones web.

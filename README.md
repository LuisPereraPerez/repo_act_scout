# ⚜️ ScoutRepo — Repositorio de Actividades Scouts

MVP completo en Flask con autenticación, filtros dinámicos y panel de administración.

---

## Estructura del proyecto

```
scout-app/
├── run.py                        # Punto de entrada
├── requirements.txt
├── .env.example
└── app/
    ├── __init__.py               # App factory
    ├── models.py                 # Modelos SQLAlchemy + seed
    ├── auth/
    │   ├── __init__.py
    │   └── routes.py             # Registro, login, logout
    ├── main/
    │   ├── __init__.py
    │   └── routes.py             # Index + filtros + detalle + subida
    ├── admin/
    │   ├── __init__.py
    │   └── routes.py             # Panel admin + aprobar/rechazar
    └── templates/
        ├── base.html
        ├── auth/
        │   ├── login.html
        │   └── register.html
        ├── main/
        │   ├── index.html
        │   ├── activity_detail.html
        │   └── upload.html
        └── admin/
            └── panel.html
```

---

## Instalación y puesta en marcha

```bash
# 1. Clonar o copiar el proyecto
cd scout-app

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env y cambiar SECRET_KEY

# 5. Arrancar la aplicación
python run.py
```

La app estará en **http://localhost:5000**

---

## Credenciales de administrador por defecto

| Campo | Valor |
|-------|-------|
| Email | `admin@scouts.es` |
| Contraseña | `admin1234` |

> ⚠️ **Cambia la contraseña de admin** antes de desplegarlo en producción.

---

## Funcionalidades del MVP

### Roles
- **Visitante** — puede explorar y buscar actividades aprobadas.
- **Scouter** — puede registrarse, iniciar sesión y subir actividades.
- **Admin** — puede revisar actividades pendientes y aprobarlas o rechazarlas.

### Filtros disponibles
- Búsqueda por texto (título y descripción)
- Sección scout (Castores, Lobatos, Scouts, Escultas, Rovers)
- Tipo de actividad (Acecho, Velada, Taller, Gran Juego…)
- Entorno (Interior / Exterior / Indiferente)
- Duración (<30 min / 30-60 min / +60 min)

---

## Posibles mejoras post-MVP

- Paginación de resultados
- Sistema de valoraciones/favoritos
- Subida de imágenes o PDFs adjuntos
- Notificaciones por email al aprobar actividades
- Búsqueda full-text con PostgreSQL
- API REST para una futura app móvil

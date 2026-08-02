# ERP - Tienda de Tecnología 🖥️

Sistema ERP transaccional para una tienda de tecnología. Proyecto universitario — Sistemas Transaccionales.

## 📋 Módulos

| Módulo | Funcionalidad |
|---|---|
| **Catálogo Público** | Visualización, búsqueda y filtro de productos (RF03, RF04) |
| **Autenticación** | Login, registro con roles: admin, vendedor, cliente (RF01, RF02) |
| **Inventario** | CRUD de productos, consulta de stock (RF05, RF06) |
| **Facturación** | Creación de facturas con transacción ACID, anulación (RF07-RF10, RNF01) |
| **Reportes** | Ventas totales, stock bajo (RF12) |
| **Historial** | Registro de facturas por usuario (RF11) |

## 🛠️ Stack Tecnológico

- **Backend:** Python 3 + Flask
- **Base de datos:** PostgreSQL 16
- **ORM:** SQLAlchemy
- **Autenticación:** Flask-Login + hash seguro (scrypt)
- **Frontend:** Bootstrap 5 + Jinja2 (server-side rendering)
- **Contenedores:** Docker / Podman (compatible con ambos)

## 📁 Estructura del Proyecto

```
src/
├── docker-compose.yml      # Orquestación de servicios
├── Dockerfile              # Imagen de la aplicación
├── requirements.txt        # Dependencias Python
├── init.sql                # Schema y datos iniciales
├── run.py                  # Punto de entrada
└── app/
    ├── __init__.py         # Fábrica de aplicación Flask
    ├── config.py           # Configuración centralizada
    ├── models.py           # Modelos: Usuario, Producto, Factura, DetalleFactura
    ├── main.py             # Rutas públicas (catálogo)
    ├── auth.py             # Autenticación (login/registro)
    ├── products.py         # Gestión de productos e inventario
    ├── invoices.py         # Facturación (transacciones ACID)
    ├── reports.py          # Reportes administrativos
    ├── templates/          # Plantillas HTML (Jinja2)
    │   ├── base.html       # Layout común
    │   ├── index.html      # Catálogo público
    │   ├── login.html      # Inicio de sesión
    │   ├── register.html   # Registro
    │   ├── products/       # Vistas de productos
    │   ├── invoices/       # Vistas de facturación
    │   └── reports/        # Vistas de reportes
    └── static/
        └── style.css       # Estilos personalizados
```

## 🚀 Instrucciones de Ejecución

### Requisitos Previos

- **Docker** y **docker-compose** instalados, **o**
- **Podman** con capa de integración Docker (`podman-docker`)

### Opción 1: Con Docker

```bash
# 1. Clonar el repositorio
git clone <url-del-repo>
cd guia-001/src/

# 2. Construir e iniciar los contenedores
docker-compose up --build

# 3. Acceder a la aplicación
# Abrir en el navegador: http://localhost:5000
```

### Opción 2: Con Podman

```bash
# 1. Clonar el repositorio
git clone <url-del-repo>
cd guia-001/src/

# 2. Construir e iniciar los contenedores
podman-compose up --build

# 3. Acceder a la aplicación
# Abrir en el navegador: http://localhost:5000
```

### Opción 3: Ejecución Local (sin Docker)

```bash
# 1. Requisitos: Python 3.10+ y PostgreSQL 16 instalados

# 2. Crear base de datos
psql -U postgres -c "CREATE USER erp_user WITH PASSWORD 'erp_password';"
psql -U postgres -c "CREATE DATABASE erp_db OWNER erp_user;"
psql -U erp_user -d erp_db -f src/init.sql

# 3. Instalar dependencias
cd src/
pip install -r requirements.txt

# 4. Ejecutar la aplicación
python run.py

# 5. Acceder en: http://localhost:5000
```

## 👥 Roles del Sistema

| Rol | Permisos |
|---|---|
| **admin** | Acceso total: CRUD productos, facturación, reportes, anulación |
| **vendedor** | Ver productos, crear facturas, ver sus propias facturas |
| **cliente** | Ver catálogo, registrarse, ver sus propias facturas |

## 🔐 Seguridad

- Contraseñas almacenadas con hash scrypt (nunca en texto plano) — RNF03
- Protección de rutas según rol de usuario
- Integridad referencial en base de datos (llaves foráneas) — RNF05
- Transacciones ACID para facturación — RNF01

## 📄 Licencia

Proyecto académico — Universidad Manuela Beltrán.

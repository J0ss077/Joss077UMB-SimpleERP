# ERP - Tienda de Tecnologia

Sistema ERP transaccional para una tienda de tecnologia.

## Modulos

| Modulo | Funcionalidad |
|---|---|
| **Catalogo Publico** | Visualizacion, busqueda y filtro de productos (RF03, RF04) |
| **Autenticacion** | Login, registro con roles: admin, vendedor, cliente (RF01, RF02) |
| **Inventario** | CRUD de productos, consulta de stock (RF05, RF06) |
| **Facturacion** | Creacion de facturas con transaccion ACID, anulacion (RF07-RF10, RNF01) |
| **Reportes** | Ventas totales, stock bajo (RF12) |
| **Historial** | Registro de facturas por usuario (RF11) |

## Stack Tecnologico

- **Backend:** Python 3 + Flask
- **Base de datos:** PostgreSQL 16
- **ORM:** SQLAlchemy
- **Autenticacion:** Flask-Login + hash seguro (scrypt)
- **Frontend:** Bootstrap 5 + Jinja2 (server-side rendering)
- **Contenedores:** Docker

## Estructura del Proyecto

```
src/
├── docker-compose.yml      # Orquestacion de servicios
├── Dockerfile              # Imagen de la aplicacion
├── requirements.txt        # Dependencias Python
├── init.sql                # Schema y datos iniciales
├── run.py                  # Punto de entrada
└── app/
    ├── __init__.py         # Fabrica de aplicacion Flask
    ├── config.py           # Configuracion centralizada
    ├── models.py           # Modelos: Usuario, Producto, Factura, DetalleFactura
    ├── main.py             # Rutas publicas (catalogo)
    ├── auth.py             # Autenticacion (login/registro)
    ├── products.py         # Gestion de productos e inventario
    ├── invoices.py         # Facturacion (transacciones ACID)
    ├── reports.py          # Reportes administrativos
    ├── templates/          # Plantillas HTML (Jinja2)
    │   ├── base.html       # Layout comun
    │   ├── index.html      # Catalogo publico
    │   ├── login.html      # Inicio de sesion
    │   ├── register.html   # Registro
    │   ├── products/       # Vistas de productos
    │   ├── invoices/       # Vistas de facturacion
    │   └── reports/        # Vistas de reportes
    └── static/
        └── style.css       # Estilos personalizados
```

## Instrucciones de Ejecucion

### Requisitos Previos

- Docker y docker-compose instalados.

### Montaje con Docker

```bash
# 1. Clonar el repositorio
git clone <url-del-repo>
cd guia-001/src/

# 2. Construir e iniciar los contenedores
docker-compose up --build

# 3. Acceder a la aplicacion
# Abrir en el navegador: http://localhost:5000
```

## Roles del Sistema

| Rol | Permisos |
|---|---|
| **admin** | Acceso total: CRUD productos, facturacion, reportes, anulacion |
| **vendedor** | Ver productos, crear facturas, ver sus propias facturas |
| **cliente** | Ver catalogo, registrarse, ver sus propias facturas |

## Seguridad

- Contrasenas almacenadas con hash scrypt (nunca en texto plano) — RNF03
- Proteccion de rutas segun rol de usuario
- Integridad referencial en base de datos (llaves foraneas) — RNF05
- Transacciones ACID para facturacion — RNF01

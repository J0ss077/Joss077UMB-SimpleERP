# ERP - Tienda de Tecnologia

Sistema ERP transaccional para una tienda de tecnologia, construido con Flask. Incluye un **portal de inicio de empresa**, un **catalogo con carrito de compras para clientes**, facturacion con **transacciones ACID** y reportes administrativos, todo con modo claro/oscuro y animaciones.

## Modulos

| Modulo | Funcionalidad |
|---|---|
| **Portal de Inicio** | Hero de bienvenida, banner promocional, features del sistema y productos destacados |
| **Catalogo** | Visualizacion, busqueda, filtro por categoria, ordenamiento y paginacion (RF03, RF04) |
| **Autenticacion** | Login y registro con roles: admin, vendedor, cliente (RF01, RF02) |
| **Tienda del Cliente** | Carrito y favoritos persistentes en BD, checkout en 2 pasos con datos de envio, estado del pedido y recompra |
| **Perfil de Usuario** | Datos personales, foto, datos de envio, preferencias (tema/newsletter), cambio de contrasena y resumen de actividad |
| **Inventario** | CRUD de productos e imagenes, consulta de stock con indicador visual (RF05, RF06) |
| **Facturacion** | Creacion de facturas con transaccion ACID, anulacion y reversion de stock (RF07-RF10, RNF01) |
| **Usuarios (admin)** | Gestion de cuentas: crear, cambiar rol, resetear contrasena y bloquear/desbloquear |
| **Reportes** | Panel con metricas, ventas con filtro de fechas y CSV, ventas por categoria, top 5 productos, ventas por cliente y stock bajo (RF12) |
| **Historial** | Registro de facturas por usuario con mini-metricas (RF11) |

## Roles del Sistema

| Rol | Permisos |
|---|---|
| **admin** | Acceso total: CRUD de productos, facturacion, reportes, gestion de usuarios, anulacion de facturas |
| **vendedor** | Catalogo, gestion de productos, facturacion directa, todas las facturas con mini-metricas, actualizacion del estado del pedido |
| **cliente** | Portal, catalogo, carrito, favoritos, checkout con envio, historial de sus compras y recompra de pedidos |

### Cuentas de prueba

| Rol | Email | Contrasena |
|---|---|---|
| admin | `admin@erp.local` | `admin123` |
| vendedor | `vendedor@erp.local` | `vendedor123` |
| cliente | `cliente@erp.local` | `cliente123` |

> Nota: se pueden crear cuentas nuevas desde el formulario de registro.

## Stack Tecnologico

- **Backend:** Python 3 + Flask
- **Base de datos:** PostgreSQL 16 (o SQLite en modo desarrollo local)
- **ORM:** SQLAlchemy
- **Autenticacion:** Flask-Login + hash seguro (scrypt)
- **Frontend:** Bootstrap 5 + Jinja2 (server-side rendering), CSS con variables y animaciones
- **Interaccion:** JavaScript vanilla (tema claro/oscuro, ripple, reveal al scroll, navbar dinamica)
- **Contenedores:** Docker / Docker Compose

## Estructura del Proyecto

```
src/
├── docker-compose.yml      # Orquestacion de servicios (web + PostgreSQL)
├── Dockerfile              # Imagen de la aplicacion
├── requirements.txt        # Dependencias Python
├── init.sql                # Schema y datos iniciales
├── run.py                  # Punto de entrada
└── app/
    ├── __init__.py         # Fabrica de aplicacion, blueprints y contexto global (carrito/favoritos en BD)
    ├── config.py           # Configuracion centralizada (variables de entorno)
    ├── models.py           # Modelos: Usuario, Producto, Factura, DetalleFactura, CarritoItem, Favorito
    ├── main.py             # Portal de inicio y catalogo (busqueda, filtro, orden, paginacion)
    ├── auth.py             # Autenticacion (login/registro, bloqueo de cuentas inactivas)
    ├── products.py         # Gestion de productos e inventario
    ├── invoices.py         # Facturacion (transacciones ACID compartidas, estado del pedido)
    ├── tienda.py           # Carrito y favoritos en BD, checkout 2 pasos, pedidos y recompra
    ├── perfil.py           # Perfil de usuario (datos, envio, preferencias, contrasena)
    ├── usuarios.py         # Gestion de usuarios (solo admin)
    ├── utils.py            # Utilidades compartidas (subida de imagenes)
    ├── reports.py          # Reportes administrativos avanzados (+ export CSV)
    ├── templates/          # Plantillas HTML (Jinja2)
    │   ├── base.html       # Layout comun (navbar por rol, avatar, modo oscuro)
    │   ├── _macros.html    # Macro reutilizable de tarjeta de producto
    │   ├── home.html       # Portal de inicio de la empresa
    │   ├── index.html      # Catalogo con busqueda, filtros, orden y paginacion
    │   ├── producto_detalle.html  # Detalle de producto
    │   ├── carrito.html    # Carrito de compras
    │   ├── checkout.html   # Paso 1 del checkout: confirmacion de envio
    │   ├── favoritos.html  # Productos favoritos
    │   ├── pedido.html     # Confirmacion de pedido (estado y envio)
    │   ├── perfil.html     # Perfil del usuario
    │   ├── login.html      # Inicio de sesion (pantalla dividida)
    │   ├── register.html   # Registro (pantalla dividida)
    │   ├── products/       # Vistas de productos
    │   ├── invoices/       # Vistas de facturacion
    │   ├── usuarios/       # Vistas de gestion de usuarios
    │   └── reports/        # Vistas de reportes
    └── static/
        ├── style.css       # Tema claro/oscuro, componentes y animaciones
        └── app.js          # Tema, ripple, reveal, navbar dinamica
```

## Flujo de Compra (rol cliente)

1. Ingresar al sistema (login o registro).
2. Desde el **Portal de Inicio** o el **Catalogo**, agregar productos al **carrito** (con validacion de stock).
3. Ajustar cantidades o quitar productos en la vista del **carrito** (badge en la navbar muestra el total).
4. **Finalizar Compra** (paso 1): confirmar los datos de envio (direccion, ciudad y telefono, pre-llenados desde el perfil).
5. **Confirmar y pagar** (paso 2): se genera la factura con transaccion ACID (factura + descuento de stock atomicos) y se vacia el carrito.
6. Ver la **confirmacion del pedido** con el estado del envio (pendiente/enviado/entregado) y el detalle de la factura en "Mis Facturas".
7. Desde un pedido anterior se puede **Comprar de nuevo** para volver a agregar sus productos al carrito.

## Instrucciones de Ejecucion

### Opcion A: Docker (recomendada)

Requisitos: Docker y Docker Compose instalados.

```bash
# 1. Clonar el repositorio
git clone <url-del-repo>
cd Joss077UMB-SimpleERP/src/

# 2. Construir e iniciar los contenedores
docker-compose up --build

# 3. Acceder a la aplicacion
# Abrir en el navegador: http://localhost:5000
```

### Opcion B: Desarrollo local con SQLite

Requisitos: Python 3.10+ instalado.

```bash
# 1. Crear entorno virtual e instalar dependencias
cd Joss077UMB-SimpleERP/
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r src/requirements.txt

# 2. Ejecutar con SQLite (sin PostgreSQL)
cd src
DATABASE_URL="sqlite:///erp.db" python run.py

# 3. Acceder a la aplicacion
# Abrir en el navegador: http://localhost:5000
```

> El esquema se crea automaticamente al iniciar (db.create_all). Para datos de ejemplo,
> registrar usuarios desde el formulario de registro y crear productos desde el rol admin.

## Frontend

- **Modo claro/oscuro:** boton flotante con persistencia en `localStorage` y respeto a la preferencia del sistema.
- **Navbar dinamica:** sticky, se oculta al bajar y reaparece al subir, marca con gradiente animado y link activo resaltado.
- **Animaciones:** revelado al hacer scroll (IntersectionObserver), contadores en metricas, ripple en botones, transiciones de pagina (View Transitions API) y barra de progreso de carga.
- **Login/Registro:** pantalla dividida con panel de marca y formulario, adaptados a ambos temas.
- **Accesibilidad:** respeta `prefers-reduced-motion`.

## Seguridad

- Contrasenas almacenadas con hash scrypt (nunca en texto plano) — RNF03
- Proteccion de rutas y navbar segun rol de usuario (cliente limitado a la tienda)
- Validacion de stock en carrito y checkout
- Bloqueo de cuentas desde la gestion de usuarios (no pueden iniciar sesion)
- Integridad referencial en base de datos (llaves foraneas) — RNF05
- Transacciones ACID para facturacion y compras — RNF01

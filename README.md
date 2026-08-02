# ERP - Tienda de Tecnologia

Sistema **ERP transaccional** para una tienda de tecnologia, construido con **Python + Flask**.

Incluye un **portal de inicio de empresa** con marca propia, un **catalogo con carrito y favoritos persistentes**, **facturacion con transacciones ACID** (factura + descuento de stock atomicos), **checkout en 2 pasos con envio**, **estado de pedidos**, **gestion de usuarios**, **reportes administrativos avanzados** y **perfil de usuario completo** — todo con modo claro/oscuro y animaciones.

---

## Caracteristicas principales

- **Portal de inicio de empresa**: hero, banner promocional, categorias, ventajas, "lo que dicen nuestros clientes" (testimonios) y CTA final.
- **Catalogo completo**: busqueda por texto, filtro por categoria, ordenamiento (nombre, precio, stock) y **paginacion** (12 productos por pagina).
- **Tienda del cliente real**: carrito y favoritos **persistentes en BD** (sobreviven al cierre de sesion), validacion de stock en cada paso.
- **Checkout en 2 pasos**: confirmacion de envio (direccion, ciudad, telefono pre-llenados desde el perfil) + transaccion ACID.
- **Estado del pedido**: `pendiente` → `enviado` → `entregado`, actualizable por admin/vendedor y visible para el cliente.
- **Recompra**: un cliente puede volver a agregar al carrito los productos de una factura anterior en un clic.
- **Facturacion directa** (admin/vendedor): transaccion ACID, anulacion con reversion de stock y mini-metricas en el listado.
- **Gestion de usuarios** (solo admin): crear cuentas, cambiar rol, resetear contrasena, bloquear/desbloquear.
- **Reportes avanzados**: ventas con rango de fechas y exportacion CSV, ventas por categoria, top 5 productos, ventas por cliente y stock bajo.
- **Perfil de usuario**: datos personales, foto de perfil, datos de envio, preferencias (tema claro/oscuro, newsletter), cambio de contrasena y resumen de actividad.
- **Diseño moderno**: modo claro/oscuro, navbar dinamica, animaciones y responsive (Bootstrap 5).

---

## Modulos

| Modulo | Funcionalidad |
|---|---|
| **Portal de Inicio** | Hero, banner promocional, categorias, ventajas, testimonios y CTA (RF03) |
| **Catalogo** | Visualizacion, busqueda, filtro por categoria, ordenamiento y paginacion (RF03, RF04) |
| **Autenticacion** | Login y registro con roles; bloqueo de cuentas inactivas (RF01, RF02) |
| **Tienda del Cliente** | Carrito y favoritos en BD, checkout 2 pasos con envio, estado del pedido, recompra |
| **Perfil de Usuario** | Datos, foto, envio, preferencias, contrasena y resumen de actividad |
| **Inventario** | CRUD de productos con imagenes y stock (RF05, RF06) |
| **Facturacion** | Transacciones ACID, anulacion con reversion de stock (RF07-RF10, RNF01) |
| **Usuarios (admin)** | Crear, cambiar rol, resetear contrasena, bloquear/desbloquear |
| **Reportes** | Ventas (fechas + CSV), categorias, top 5, clientes y stock bajo (RF12) |
| **Historial** | Facturas por usuario con mini-metricas (RF11) |

---

## Roles del Sistema

| Rol | Permisos |
|---|---|
| **admin** | Acceso total: CRUD de productos, facturacion y anulacion, reportes, gestion de usuarios, estado de pedidos |
| **vendedor** | Catalogo, gestion de productos, facturacion directa, todas las facturas con mini-metricas, estado de pedidos |
| **cliente** | Portal, catalogo, carrito, favoritos, checkout con envio, historial y recompra de pedidos |

La **navbar se adapta por rol**: el cliente ve Tienda/Favoritos/Carrito; vendedor y admin ven Productos/Facturas (+ Nueva Factura para el vendedor); el admin ve ademas Reportes y Usuarios.

### Cuentas demo (creadas con `init.sql`)

| Rol | Nombre | Email | Contrasena |
|---|---|---|---|
| admin | Admin Demo | `admin@erp.local` | `admin123` |
| vendedor | Vendedor Demo | `vendedor@erp.local` | `vendedor123` |
| cliente | Cliente Demo | `cliente@erp.local` | `cliente123` |

> El cliente demo viene con telefono, direccion y ciudad de envio pre-cargadas para probar el checkout de inmediato.
> Tambien se pueden crear cuentas nuevas desde el formulario de registro.

---

## Flujos de trabajo por rol

### Cliente: compra completa

1. Ingresar (login o registro) y navegar el **Catalogo** o el **Portal**.
2. Agregar productos al **carrito** (se valida stock) o marcarlos como **favoritos**.
3. En el carrito: ajustar cantidades, eliminar o vaciar (badge en la navbar muestra el total).
4. **Finalizar Compra** (paso 1): confirmar direccion, ciudad y telefono de envio (pre-llenados desde el perfil).
5. **Confirmar y pagar** (paso 2): se ejecuta la transaccion ACID (factura + descuento de stock atomicos) y se vacia el carrito.
6. Ver la **confirmacion del pedido**: resumen, datos de envio y estado (`pendiente`/`enviado`/`entregado`).
7. Desde un pedido anterior usar **"Comprar de nuevo"** para repetir la compra en un clic.

### Vendedor: facturacion directa

1. **Nueva Factura**: seleccionar el cliente con busqueda (datalist) y elegir cantidades (el stock disponible se muestra por producto).
2. El sistema genera factura + detalle + descuento de stock **todo en una transaccion atomica** (RNF01).
3. Desde el listado (con mini-metricas: total facturado, promedio, pendientes) o el detalle, actualizar el **estado del pedido**.

### Admin: control total

1. **Usuarios**: crear cuentas, cambiar roles, resetear contrasenas y bloquear/desbloquear (un bloqueado no puede iniciar sesion).
2. **Facturas**: ver todo, **anular** con reversion automatica del stock.
3. **Reportes**: ventas con filtro de fechas y CSV, categorias, top 5, clientes y stock bajo.

---

## Modelo de datos

| Tabla | Descripcion |
|---|---|
| `usuarios` | Cuentas: nombre, email (unico), hash scrypt, rol, datos de envio, foto, newsletter, tema, estado `activo` |
| `productos` | Catalogo: nombre, descripcion, precio, stock, categoria, imagen |
| `facturas` | Cabecera: cliente, fecha, total, estado (activa/anulada), datos de envio y `estado_pedido` |
| `detalle_factura` | Lineas: producto, cantidad, precio unitario congelado, subtotal |
| `carrito_items` | Carrito persistente: usuario + producto + cantidad (unico por par) |
| `favoritos` | Favoritos persistentes: usuario + producto (unico por par) |

El esquema completo vive en **`src/init.sql`** (PostgreSQL) y tambien se crea automaticamente con `db.create_all()` (SQLite local).

---

## Requisitos funcionales y no funcionales

| Codigo | Requisito | Implementacion |
|---|---|---|
| RF01 | Login obligatorio para acceder a modulos internos | `auth.py` + Flask-Login |
| RF02 | Registro de nuevos usuarios con rol asignado | `auth.py` (rol por defecto `cliente`) |
| RF03 | Consultar catalogo de productos | `main.py` + `index.html` |
| RF04 | Buscar y filtrar productos | Texto + categoria + orden + paginacion |
| RF05 | Gestionar productos (crear, editar, eliminar) | `products.py` (CRUD + imagenes) |
| RF06 | Consultar stock disponible | Vista de inventario con indicador visual |
| RF07 | Generar factura con fecha, cliente, detalle y total | `invoices.py` (compartido con la tienda) |
| RF08 | Calcular total de la factura | `Factura.calcular_total()` |
| RF09 | Descontar stock al facturar | Dentro de la transaccion ACID |
| RF10 | Anular factura revirtiendo stock | `invoices.py` (solo admin, atomico) |
| RF11 | Historial de facturas | `invoices.py` + `list.html` con mini-metricas |
| RF12 | Reportes de ventas y stock bajo (admin) | `reports.py` (avanzados + CSV) |
| RNF01 | Transacciones ACID en facturacion y compras | `crear_factura_transaccional()` con commit/rollback |
| RNF03 | Contrasenas nunca en texto plano | Hash scrypt (`werkzeug.security`) |
| RNF05 | Integridad referencial | Llaves foraneas en BD |

---

## Stack Tecnologico

- **Backend:** Python 3 + Flask (application factory)
- **Base de datos:** PostgreSQL 16 (produccion/Docker) o SQLite (desarrollo local)
- **ORM:** SQLAlchemy 2
- **Autenticacion:** Flask-Login + hash scrypt
- **Frontend:** Bootstrap 5 + Jinja2 (SSR), CSS con variables (tema claro/oscuro) y animaciones
- **Interaccion:** JavaScript vanilla (tema, ripple, reveal al scroll, navbar dinamica, contadores)
- **Contenedores:** Docker / Docker Compose

---

## Estructura del Proyecto

```
src/
├── docker-compose.yml      # Orquestacion de servicios (web + PostgreSQL)
├── Dockerfile              # Imagen de la aplicacion
├── requirements.txt        # Dependencias Python
├── init.sql                # Schema completo + datos iniciales + cuentas demo
├── run.py                  # Punto de entrada
└── app/
    ├── __init__.py         # Fabrica de aplicacion, blueprints y contexto global (carrito/favoritos en BD)
    ├── config.py           # Configuracion centralizada (variables de entorno)
    ├── models.py           # Modelos: Usuario, Producto, Factura, DetalleFactura, CarritoItem, Favorito
    ├── main.py             # Portal de inicio y catalogo (busqueda, filtro, orden, paginacion)
    ├── auth.py             # Autenticacion (login/registro, bloqueo de cuentas inactivas)
    ├── products.py         # Gestion de productos e inventario (CRUD + imagenes)
    ├── invoices.py         # Facturacion (transacciones ACID compartidas, anulacion, estado del pedido)
    ├── tienda.py           # Carrito y favoritos en BD, checkout 2 pasos, pedidos y recompra
    ├── perfil.py           # Perfil de usuario (datos, envio, preferencias, contrasena)
    ├── usuarios.py         # Gestion de usuarios (solo admin)
    ├── utils.py            # Utilidades compartidas (subida de imagenes)
    ├── reports.py          # Reportes administrativos avanzados (+ export CSV)
    ├── templates/          # Plantillas HTML (Jinja2)
    │   ├── base.html       # Layout comun (navbar por rol, avatar, modo oscuro)
    │   ├── _macros.html    # Macros reutilizables (tarjeta de producto, icono de categoria)
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
    │   ├── products/       # Vistas de productos (listado, crear, editar)
    │   ├── invoices/       # Vistas de facturacion (listado, crear, detalle)
    │   ├── usuarios/       # Vistas de gestion de usuarios
    │   └── reports/        # Vistas de reportes (panel, ventas, categorias, top, clientes, stock)
    └── static/
        ├── style.css       # Tema claro/oscuro, componentes y animaciones
        ├── app.js          # Tema, ripple, reveal, navbar dinamica, contadores
        └── uploads/        # Imagenes subidas (productos y fotos de perfil)
```

---

## Instrucciones de Ejecucion

### Opcion A: Docker (recomendada)

Requisitos: Docker y Docker Compose instalados.

```bash
# 1. Clonar el repositorio
git clone <url-del-repo>
cd Joss077UMB-SimpleERP/src/

# 2. Construir e iniciar los contenedores (web + PostgreSQL + init.sql)
docker-compose up --build

# 3. Acceder a la aplicacion
# Abrir en el navegador: http://localhost:5000
```

> `init.sql` se ejecuta automaticamente al crear el volumen de PostgreSQL: crea el esquema completo,
> 15 productos de ejemplo y las 3 cuentas demo (admin123 / vendedor123 / cliente123).

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

> El esquema se crea automaticamente al iniciar (`db.create_all`). Para datos de ejemplo,
> registrar usuarios desde el formulario de registro y crear productos desde el rol admin,
> o aplicar el contenido de `init.sql` a mano.

---

## Configuracion (variables de entorno)

| Variable | Descripcion | Default |
|---|---|---|
| `DATABASE_URL` | Cadena de conexion a la base de datos | `postgresql://erp_user:erp_password@localhost:5432/erp_db` |
| `SECRET_KEY` | Clave para sesiones y cookies | valor de desarrollo |
| `UPLOAD_FOLDER` | Carpeta para imagenes subidas | `app/static/uploads` |
| `MAX_CONTENT_LENGTH` | Tamano maximo de archivo subido | 5 MB |

---

## Reportes (rol admin)

| Reporte | Descripcion |
|---|---|
| **Panel** | Metricas generales: productos, facturas activas, stock bajo |
| **Ventas** | Total facturado, cantidad y promedio por rango de fechas + **exportacion CSV** |
| **Por Categoria** | Unidades y facturacion agrupadas por categoria |
| **Top 5 Productos** | Mas vendidos por unidades y por ingresos |
| **Por Cliente** | Facturas y total comprado de cada cliente |
| **Stock Bajo** | Productos con stock menor a 5 unidades |

Todos los reportes aceptan filtro de rango de fechas (desde/hasta).

---

## Frontend

- **Modo claro/oscuro:** boton flotante, persistencia en `localStorage`, preferencia de tema por usuario (sincronizada con la BD via perfil) y respeto a `prefers-color-scheme`.
- **Navbar dinamica:** sticky con ocultado al bajar, marca con gradiente animado, link activo resaltado con linea corta centrada y separacion limpia entre items.
- **Animaciones:** revelado al scroll (IntersectionObserver), contadores en metricas, ripple en botones, transiciones de pagina (View Transitions API) y barra de progreso de carga.
- **Login/Registro:** pantalla dividida con panel de marca, adaptados a ambos temas.
- **Portal de empresa:** hero con degradado, banner promocional, categorias con iconos, ventajas, testimonios y CTA.
- **Accesibilidad:** respeta `prefers-reduced-motion` y usa `aria` en iconos decorativos.

---

## Seguridad

- Contrasenas con hash **scrypt** (nunca en texto plano) — RNF03
- Proteccion de rutas y navbar segun rol (el cliente solo accede a la tienda)
- Validacion de stock en carrito, checkout y facturacion directa
- Bloqueo de cuentas desde la gestion de usuarios (no pueden iniciar sesion)
- Integridad referencial en base de datos (llaves foraneas) — RNF05
- **Transacciones ACID** en facturacion y compras: si algo falla, todo se revierte — RNF01
- Validacion de entrada en formularios (cantidades numericas, emails unicos, estados permitidos)

---

## Probar el sistema (resumen de cobertura)

- **Cliente**: catalogo con filtros/orden/paginacion, carrito persistente, checkout 2 pasos con envio, pedido con estado, recompra, favoritos, perfil completo.
- **Vendedor**: crear factura con busqueda de cliente, mini-metricas, cambiar estado del pedido (sin poder anular).
- **Admin**: gestion de usuarios (crear/rol/password/bloquear), anular facturas con reversion de stock, los 6 reportes + CSV.

---

## Mejoras futuras (roadmap)

- Pago en linea (pasarela simulada) e historial de transacciones de pago.
- Notificaciones por email del estado del pedido (cambio de estado → email al cliente).
- Graficos interactivos en el panel de reportes.
- Paginacion y filtros en el historial de facturas.
- Varias direcciones de envio por cliente.
- API REST (Flask-RESTful o similar) para integraciones externas.

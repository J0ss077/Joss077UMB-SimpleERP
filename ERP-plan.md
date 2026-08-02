# ERP - Tienda de Tecnología (Sistema Transaccional)

## 1. Marco teórico (resumen)

Sistema transaccional: procesa operaciones que deben cumplir ACID (atomicidad, consistencia, aislamiento, durabilidad). ERP integra módulos (ventas, inventario, facturación, usuarios) sobre una BD compartida. Arquitectura: 3 capas (presentación web, lógica de negocio/API, datos), con componente cloud (pasarela de pago).

## 2. Requerimientos funcionales (RF)

| ID   | Requerimiento                                                                         |
| ---- | ------------------------------------------------------------------------------------- |
| RF01 | Usuario debe autenticarse (login) antes de acceder a módulos internos                 |
| RF02 | Sistema permite registro de nuevos usuarios con rol asignado (admin/vendedor/cliente) |
| RF03 | Página web muestra catálogo público de productos (nombre, precio, stock, categoría)   |
| RF04 | Página web permite buscar y filtrar productos por categoría                           |
| RF05 | Admin puede registrar, editar y eliminar productos (CRUD inventario)                  |
| RF06 | Sistema consulta stock disponible de un producto                                      |
| RF07 | Sistema genera factura con fecha, cliente, detalle de productos y total               |
| RF08 | Sistema calcula automáticamente el total de la factura (suma de subtotales)           |
| RF09 | Sistema descuenta stock de inventario al confirmar una factura                        |
| RF10 | Sistema permite anular una factura (y revertir el stock descontado)                   |
| RF11 | Sistema almacena historial de facturas por usuario/cliente                            |
| RF12 | Admin puede consultar reportes básicos (ventas, stock bajo)                           |

## 3. Requerimientos no funcionales (RNF)

| ID    | Requerimiento                                                                                                               |
| ----- | --------------------------------------------------------------------------------------------------------------------------- |
| RNF01 | Transacción de facturación debe ser atómica: factura + descuento de stock ocurren juntos, o ninguno (ACID)                  |
| RNF02 | Tiempo de respuesta de la página web debe ser menor a 2 segundos                                                            |
| RNF03 | Contraseñas deben almacenarse con hash (no texto plano)                                                                     |
| RNF04 | Sistema debe ser escalable para soportar aumento de usuarios/transacciones                                                  |
| RNF05 | Base de datos debe garantizar integridad referencial (llaves foráneas entre Facturas, Detalle_Factura, Productos, Usuarios) |
| RNF06 | Interfaz web debe ser responsive (accesible desde móvil y escritorio)                                                       |
| RNF07 | Sistema debe registrar logs de accesos y operaciones críticas (auditoría)                                                   |
| RNF08 | Comunicación entre cliente y servidor debe usar HTTPS                                                                       |
| RNF09 | Sistema debe tener disponibilidad mínima 99% (si se despliega en cloud)                                                     |

## 4. Modelo de clases preliminar

**Usuario**: id, nombre, email, passwordHash, rol
Métodos: getId(), getEmail(), getRol(), login(), validarCredenciales()

**Producto**: id, nombre, descripcion, precio, stock, categoria
Métodos: getStock(), getPrecio(), actualizarStock(cantidad), registrarProducto()

**Factura**: id, fecha, idUsuario, total, estado
Métodos: getTotal(), generarFactura(), calcularTotal(), anularFactura()

**DetalleFactura**: id, idFactura, idProducto, cantidad, precioUnitario, subtotal
Métodos: getSubtotal()

Relaciones: Usuario 1--0.._ Factura | Factura 1--1.._ DetalleFactura | DetalleFactura 1--1 Producto

## 5. Modelo de base de datos (tablas)

```
USUARIOS (id_usuario PK, nombre, email, password_hash, rol)
PRODUCTOS (id_producto PK, nombre, descripcion, precio, stock, categoria)
FACTURAS (id_factura PK, id_usuario FK, fecha, total, estado)
DETALLE_FACTURA (id_detalle PK, id_factura FK, id_producto FK, cantidad, precio_unitario, subtotal)
```

## 6. Arquitectura del sistema (PlantUML - Componentes/Despliegue)

> check "assets/ERP-architecture-diagram.txt"

## 7. Diagrama de clases (PlantUML)

> check "assets/ERP-classes-diagram.txt"

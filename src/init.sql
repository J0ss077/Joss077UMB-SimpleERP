-- ERP - Tienda de Tecnologia
-- Script de inicializacion de la base de datos
-- Se ejecuta automaticamente al crear el contenedor PostgreSQL por primera vez

-- Tabla: USUARIOS
-- Almacena cuentas de acceso al sistema con roles (admin, vendedor, cliente)
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(20) NOT NULL CHECK (rol IN ('admin', 'vendedor', 'cliente')),
    telefono VARCHAR(20),
    direccion VARCHAR(255),
    ciudad VARCHAR(100),
    imagen VARCHAR(255),
    newsletter BOOLEAN NOT NULL DEFAULT FALSE,
    tema_preferido VARCHAR(10) NOT NULL DEFAULT 'auto',
    activo BOOLEAN NOT NULL DEFAULT TRUE
);

-- Tabla: PRODUCTOS
-- Catalogo de productos de la tienda de tecnologia
CREATE TABLE IF NOT EXISTS productos (
    id_producto SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    descripcion TEXT,
    precio DECIMAL(10, 2) NOT NULL CHECK (precio >= 0),
    stock INTEGER NOT NULL CHECK (stock >= 0),
    categoria VARCHAR(100),
    imagen VARCHAR(255)
);

-- Tabla: FACTURAS
-- Cabecera de cada factura emitida
CREATE TABLE IF NOT EXISTS facturas (
    id_factura SERIAL PRIMARY KEY,
    id_usuario INTEGER NOT NULL REFERENCES usuarios(id_usuario),
    fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total DECIMAL(12, 2) NOT NULL DEFAULT 0,
    estado VARCHAR(20) NOT NULL DEFAULT 'activa' CHECK (estado IN ('activa', 'anulada')),
    direccion_envio TEXT,
    ciudad_envio VARCHAR(100),
    telefono_contacto VARCHAR(20),
    estado_pedido VARCHAR(20) NOT NULL DEFAULT 'pendiente' CHECK (estado_pedido IN ('pendiente', 'enviado', 'entregado'))
);

-- Tabla: DETALLE_FACTURA
-- Lineas de detalle de cada factura (productos vendidos)
CREATE TABLE IF NOT EXISTS detalle_factura (
    id_detalle SERIAL PRIMARY KEY,
    id_factura INTEGER NOT NULL REFERENCES facturas(id_factura) ON DELETE CASCADE,
    id_producto INTEGER NOT NULL REFERENCES productos(id_producto),
    cantidad INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unitario DECIMAL(10, 2) NOT NULL,
    subtotal DECIMAL(12, 2) NOT NULL
);

-- Tabla: CARRITO_ITEMS
-- Carrito de compras persistente por usuario (sobrevive al cierre de sesion)
CREATE TABLE IF NOT EXISTS carrito_items (
    id_carrito SERIAL PRIMARY KEY,
    id_usuario INTEGER NOT NULL REFERENCES usuarios(id_usuario),
    id_producto INTEGER NOT NULL REFERENCES productos(id_producto),
    cantidad INTEGER NOT NULL DEFAULT 1 CHECK (cantidad > 0),
    UNIQUE (id_usuario, id_producto)
);

-- Tabla: FAVORITOS
-- Productos favoritos persistentes por usuario
CREATE TABLE IF NOT EXISTS favoritos (
    id_favorito SERIAL PRIMARY KEY,
    id_usuario INTEGER NOT NULL REFERENCES usuarios(id_usuario),
    id_producto INTEGER NOT NULL REFERENCES productos(id_producto),
    UNIQUE (id_usuario, id_producto)
);

-- Datos iniciales de prueba (opcionales)
-- Se insertan solo si las tablas estan vacias

-- Cuentas demo: admin123 / vendedor123 / cliente123
INSERT INTO usuarios (nombre, email, password_hash, rol, telefono, direccion, ciudad, newsletter, tema_preferido, activo)
SELECT 'Admin Demo', 'admin@erp.local', 'scrypt:32768:8:1$qV66BI8fytaUfQqB$f3fd0de898dda9953d07b5e023c967c72de1368506dd12adb15a1f0aeaeb0bd33f5bc6f350a59f90667ba5798b34294e65c79e1b9f2b77418ad2e3334a9af289', 'admin', NULL, NULL, NULL, FALSE, 'auto', TRUE
WHERE NOT EXISTS (SELECT 1 FROM usuarios LIMIT 1);

INSERT INTO usuarios (nombre, email, password_hash, rol, telefono, direccion, ciudad, newsletter, tema_preferido, activo)
SELECT 'Vendedor Demo', 'vendedor@erp.local', 'scrypt:32768:8:1$UjFBsitDuRA37fTB$8e4a3f26d6eedee4d1d81a6e77d0f1aa1b5b27f57416f6541b0261b31b1f77cd94a24246e5ffe170f3b9156623d564e6d58389e3350fdd2e5ba7786fc7285842', 'vendedor', '3105556789', 'Av. Los Estudiantes # 20-15', 'Pasto', FALSE, 'auto', TRUE
WHERE NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'vendedor@erp.local');

INSERT INTO usuarios (nombre, email, password_hash, rol, telefono, direccion, ciudad, newsletter, tema_preferido, activo)
SELECT 'Cliente Demo', 'cliente@erp.local', 'scrypt:32768:8:1$4x4hJfCPZCR9e0kP$c40fc52eab8e5f2430ca1cd037d245d5c1458f0a7fca5545e381a6f0d2ce84fe11669170010f00d75161cf77ca2bd7075972e6f1c1b22f4c11a03279e8ff22e0', 'cliente', '3005551234', 'Calle 10 # 5-30, Apto 201', 'Pasto', TRUE, 'auto', TRUE
WHERE NOT EXISTS (SELECT 1 FROM usuarios WHERE email = 'cliente@erp.local');

INSERT INTO productos (nombre, descripcion, precio, stock, categoria)
SELECT 'Laptop Pro 15"', 'Laptop de alto rendimiento, 16GB RAM, 512GB SSD', 899.99, 25, 'Computadoras'
WHERE NOT EXISTS (SELECT 1 FROM productos LIMIT 1);

INSERT INTO productos (nombre, descripcion, precio, stock, categoria)
SELECT 'Mouse Inalambrico', 'Mouse ergonomico Bluetooth 5.0', 29.99, 100, 'Perifericos'
WHERE NOT EXISTS (SELECT 1 FROM productos OFFSET 1 LIMIT 1);

INSERT INTO productos (nombre, descripcion, precio, stock, categoria)
SELECT 'Teclado Mecanico RGB', 'Teclado mecanico switches Cherry MX, retroiluminacion RGB', 79.99, 50, 'Perifericos'
WHERE NOT EXISTS (SELECT 1 FROM productos OFFSET 2 LIMIT 1);

INSERT INTO productos (nombre, descripcion, precio, stock, categoria)
SELECT 'Monitor 27" 4K', 'Monitor IPS 4K UHD, HDR, refresco 144Hz', 449.99, 15, 'Monitores'
WHERE NOT EXISTS (SELECT 1 FROM productos OFFSET 3 LIMIT 1);

INSERT INTO productos (nombre, descripcion, precio, stock, categoria)
SELECT 'SSD 1TB NVMe', 'Disco de estado solido NVMe M.2, lectura 7000MB/s', 119.99, 40, 'Almacenamiento'
WHERE NOT EXISTS (SELECT 1 FROM productos OFFSET 4 LIMIT 1);

INSERT INTO productos (nombre, descripcion, precio, stock, categoria)
SELECT 'Audifonos Gamer 7.1', 'Audifonos con sonido envolvente 7.1, microfono con cancelacion de ruido', 59.99, 60, 'Audio'
WHERE NOT EXISTS (SELECT 1 FROM productos OFFSET 5 LIMIT 1);

INSERT INTO productos (nombre, descripcion, precio, stock, categoria)
SELECT 'Parlante Bluetooth', 'Parlante portatil 20W, resistente al agua, bateria de 12 horas', 34.99, 45, 'Audio'
WHERE NOT EXISTS (SELECT 1 FROM productos OFFSET 6 LIMIT 1);

INSERT INTO productos (nombre, descripcion, precio, stock, categoria)
SELECT 'Tablet 10.5"', 'Tablet Android 10.5" 2K, 8GB RAM, 128GB, incluye lapiz', 349.99, 20, 'Tablets'
WHERE NOT EXISTS (SELECT 1 FROM productos OFFSET 7 LIMIT 1);

INSERT INTO productos (nombre, descripcion, precio, stock, categoria)
SELECT 'Camara Web HD', 'Camara web 1080p Full HD con microfono dual y tapa de privacidad', 24.99, 30, 'Perifericos'
WHERE NOT EXISTS (SELECT 1 FROM productos OFFSET 8 LIMIT 1);

INSERT INTO productos (nombre, descripcion, precio, stock, categoria)
SELECT 'Router WiFi 6', 'Router dual band WiFi 6, velocidad hasta 3000Mbps, 4 antenas', 89.99, 18, 'Redes'
WHERE NOT EXISTS (SELECT 1 FROM productos OFFSET 9 LIMIT 1);

INSERT INTO productos (nombre, descripcion, precio, stock, categoria)
SELECT 'Consola Retro 64GB', 'Consola retro con 1000 juegos incluidos, salida HDMI 4K', 189.99, 12, 'Gaming'
WHERE NOT EXISTS (SELECT 1 FROM productos OFFSET 10 LIMIT 1);

INSERT INTO productos (nombre, descripcion, precio, stock, categoria)
SELECT 'Silla Gamer', 'Silla ergonomica reclinable con soporte lumbar y reposabrazos ajustables', 149.99, 8, 'Gaming'
WHERE NOT EXISTS (SELECT 1 FROM productos OFFSET 11 LIMIT 1);

INSERT INTO productos (nombre, descripcion, precio, stock, categoria)
SELECT 'Impresora Multifuncional', 'Impresora laser WiFi: imprime, escanea y copia a doble cara', 179.99, 10, 'Oficina'
WHERE NOT EXISTS (SELECT 1 FROM productos OFFSET 12 LIMIT 1);

INSERT INTO productos (nombre, descripcion, precio, stock, categoria)
SELECT 'Cargador Rapido 65W', 'Cargador GaN 65W USB-C compatible con laptop y celulares', 27.99, 55, 'Accesorios'
WHERE NOT EXISTS (SELECT 1 FROM productos OFFSET 13 LIMIT 1);

INSERT INTO productos (nombre, descripcion, precio, stock, categoria)
SELECT 'Hub USB-C 8 en 1', 'Hub con HDMI 4K, 3x USB 3.0, lectura de tarjetas y cargador PD', 42.99, 35, 'Accesorios'
WHERE NOT EXISTS (SELECT 1 FROM productos OFFSET 14 LIMIT 1);

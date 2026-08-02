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
    rol VARCHAR(20) NOT NULL CHECK (rol IN ('admin', 'vendedor', 'cliente'))
);

-- Tabla: PRODUCTOS
-- Catalogo de productos de la tienda de tecnologia
CREATE TABLE IF NOT EXISTS productos (
    id_producto SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    descripcion TEXT,
    precio DECIMAL(10, 2) NOT NULL CHECK (precio >= 0),
    stock INTEGER NOT NULL CHECK (stock >= 0),
    categoria VARCHAR(100)
);

-- Tabla: FACTURAS
-- Cabecera de cada factura emitida
CREATE TABLE IF NOT EXISTS facturas (
    id_factura SERIAL PRIMARY KEY,
    id_usuario INTEGER NOT NULL REFERENCES usuarios(id_usuario),
    fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total DECIMAL(12, 2) NOT NULL DEFAULT 0,
    estado VARCHAR(20) NOT NULL DEFAULT 'activa' CHECK (estado IN ('activa', 'anulada'))
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

-- Datos iniciales de prueba (opcionales)
-- Se insertan solo si las tablas estan vacias
INSERT INTO usuarios (nombre, email, password_hash, rol)
SELECT 'Administrador', 'admin@erp.local', 'scrypt:32768:8:1$initial-placeholder-hash$not-a-real-hash', 'admin'
WHERE NOT EXISTS (SELECT 1 FROM usuarios LIMIT 1);

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

"""
ERP - Tienda de Tecnologia
Modelos de datos (SQLAlchemy ORM).

Representan las 4 entidades del modelo de clases del ERP:
    Usuario, Producto, Factura, DetalleFactura

Cada modelo hereda de db.Model y mapea directamente a una tabla
de la base de datos PostgreSQL.
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Instancia global de SQLAlchemy
# Se inicializa con la app Flask en app/__init__.py
db = SQLAlchemy()


# ===========================================================================
# MODELO: Usuario
# ===========================================================================
class Usuario(UserMixin, db.Model):
    """
    Representa un usuario del sistema ERP.

    Atributos:
        id_usuario (PK) : Identificador unico autoincremental.
        nombre           : Nombre completo del usuario.
        email            : Correo electronico (unico, se usa para login).
        password_hash    : Contrasena hasheada (nunca texto plano, RNF03).
        rol              : Rol: 'admin', 'vendedor' o 'cliente'.
        telefono         : Numero de contacto (opcional).
        direccion        : Direccion de envio (opcional).
        ciudad           : Ciudad del usuario (opcional).
        imagen           : Nombre del archivo de foto de perfil (opcional).
        newsletter       : True si el usuario acepta recibir promociones.
        tema_preferido   : Tema de interfaz: 'auto', 'light' o 'dark'.
    """

    __tablename__ = 'usuarios'

    # --- Columnas ---
    id_usuario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), nullable=False)
    telefono = db.Column(db.String(20))
    direccion = db.Column(db.String(255))
    ciudad = db.Column(db.String(100))
    imagen = db.Column(db.String(255))
    newsletter = db.Column(db.Boolean, nullable=False, default=False)
    tema_preferido = db.Column(db.String(10), nullable=False, default='auto')
    activo = db.Column(db.Boolean, nullable=False, default=True)

    # --- Relaciones ---
    facturas = db.relationship('Factura', backref='usuario', lazy=True)
    carrito_items = db.relationship('CarritoItem', backref='usuario', lazy=True)
    favoritos = db.relationship('Favorito', backref='usuario', lazy=True)

    # === Metodos requeridos por Flask-Login ===

    def get_id(self):
        """Devuelve el identificador del usuario como string (Flask-Login)."""
        return str(self.id_usuario)

    # === Metodos del modelo de clases ===

    def set_password(self, password):
        """
        Establece la contrasena aplicando hash seguro mediante scrypt.
        La contrasena NUNCA se almacena en texto plano (RNF03).
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifica si la contrasena ingresada coincide con el hash almacenado."""
        return check_password_hash(self.password_hash, password)

    def get_rol(self):
        """Devuelve el rol del usuario ('admin', 'vendedor', 'cliente')."""
        return self.rol

    def get_email(self):
        """Devuelve el email del usuario."""
        return self.email

    def es_admin(self):
        """Retorna True si el usuario tiene rol de administrador."""
        return self.rol == 'admin'


# ===========================================================================
# MODELO: Producto
# ===========================================================================
class Producto(db.Model):
    """
    Representa un producto del inventario de la tienda de tecnologia.

    Atributos:
        id_producto (PK) : Identificador unico autoincremental.
        nombre            : Nombre comercial del producto.
        descripcion       : Descripcion detallada (opcional).
        precio            : Precio unitario de venta.
        stock             : Unidades disponibles en inventario.
        categoria         : Categoria (ej. 'Computadoras', 'Perifericos').
        imagen            : Nombre del archivo de imagen subido (opcional).
    """

    __tablename__ = 'productos'

    # --- Columnas ---
    id_producto = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text)
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    categoria = db.Column(db.String(100))
    imagen = db.Column(db.String(255))

    # --- Relaciones ---
    detalles = db.relationship('DetalleFactura', backref='producto', lazy=True)

    # === Metodos del modelo de clases ===

    def get_stock(self):
        """Devuelve la cantidad actual de unidades en stock."""
        return self.stock

    def get_precio(self):
        """Devuelve el precio unitario como float."""
        return float(self.precio)

    def actualizar_stock(self, cantidad):
        """
        Ajusta el stock en +cantidad o -cantidad unidades.

        Levanta ValueError si el stock resultante seria negativo
        (no hay suficiente inventario para la venta).
        """
        nuevo_stock = self.stock + cantidad
        if nuevo_stock < 0:
            raise ValueError(
                f'Stock insuficiente para "{self.nombre}". '
                f'Disponible: {self.stock}, solicitado: {-cantidad}'
            )
        self.stock = nuevo_stock

    def hay_stock_suficiente(self, cantidad):
        """Verifica si hay al menos 'cantidad' unidades disponibles."""
        return self.stock >= cantidad


# ===========================================================================
# MODELO: Factura
# ===========================================================================
class Factura(db.Model):
    """
    Representa la cabecera de una factura de venta.

    Atributos:
        id_factura (PK) : Identificador unico autoincremental.
        id_usuario (FK)  : Usuario asociado (cliente o vendedor).
        fecha            : Fecha y hora de emision (se asigna automaticamente).
        total            : Suma total calculada de todos los detalles.
        estado           : 'activa' (vigente) o 'anulada' (reversada, RF10).
        direccion_envio  : Direccion de entrega del pedido (opcional).
        ciudad_envio     : Ciudad de entrega del pedido (opcional).
        estado_pedido    : Avance del envio: 'pendiente', 'enviado' o 'entregado'.
    """

    __tablename__ = 'facturas'

    # --- Columnas ---
    id_factura = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(
        db.Integer,
        db.ForeignKey('usuarios.id_usuario'),
        nullable=False
    )
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    total = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    estado = db.Column(db.String(20), nullable=False, default='activa')
    direccion_envio = db.Column(db.Text)
    ciudad_envio = db.Column(db.String(100))
    telefono_contacto = db.Column(db.String(20))
    estado_pedido = db.Column(
        db.String(20), nullable=False, default='pendiente'
    )

    # --- Relaciones ---
    detalles = db.relationship(
        'DetalleFactura',
        backref='factura',
        lazy=True,
        cascade='all, delete-orphan'
    )

    # === Metodos del modelo de clases ===

    def get_total(self):
        """Devuelve el total de la factura como float."""
        return float(self.total)

    def calcular_total(self):
        """
        Recalcula el total de la factura sumando los subtotales
        de cada linea de detalle. Se invoca despues de agregar
        o quitar detalles.
        """
        self.total = sum(float(d.subtotal) for d in self.detalles)

    def anular(self):
        """
        Marca la factura como 'anulada'.
        La reversion de stock se maneja en la capa de negocio
        (invoices.py) para garantizar atomicidad de la operacion (RNF01).
        """
        if self.estado == 'anulada':
            raise ValueError('La factura ya se encuentra anulada.')
        self.estado = 'anulada'

    def esta_anulada(self):
        """Retorna True si la factura fue anulada."""
        return self.estado == 'anulada'


# ===========================================================================
# MODELO: DetalleFactura
# ===========================================================================
class DetalleFactura(db.Model):
    """
    Representa una linea de detalle dentro de una factura.

    Cada registro vincula un producto con su cantidad y precio al momento
    de la venta. El precio queda congelado aqui para garantizar
    trazabilidad historica (no cambia si luego se modifica el producto).

    Atributos:
        id_detalle (PK)  : Identificador unico autoincremental.
        id_factura (FK)   : Factura a la que pertenece esta linea.
        id_producto (FK)  : Producto vendido en esta linea.
        cantidad          : Unidades vendidas.
        precio_unitario   : Precio del producto al momento de la venta.
        subtotal          : cantidad * precio_unitario.
    """

    __tablename__ = 'detalle_factura'

    # --- Columnas ---
    id_detalle = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_factura = db.Column(
        db.Integer,
        db.ForeignKey('facturas.id_factura', ondelete='CASCADE'),
        nullable=False
    )
    id_producto = db.Column(
        db.Integer,
        db.ForeignKey('productos.id_producto'),
        nullable=False
    )
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(12, 2), nullable=False)

    # === Metodos del modelo de clases ===

    def get_subtotal(self):
        """Devuelve el subtotal de esta linea de detalle como float."""
        return float(self.subtotal)


# ===========================================================================
# MODELO: CarritoItem
# ===========================================================================
class CarritoItem(db.Model):
    """
    Representa un producto agregado al carrito de compras de un usuario.

    El carrito se persiste en la base de datos (no en la sesion) para que
    sobreviva al cierre de sesion y se sincronice entre dispositivos.

    Atributos:
        id_carrito (PK)  : Identificador unico autoincremental.
        id_usuario (FK)  : Usuario dueno del carrito.
        id_producto (FK) : Producto agregado.
        cantidad         : Unidades del producto en el carrito (>= 1).
    """

    __tablename__ = 'carrito_items'

    id_carrito = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(
        db.Integer,
        db.ForeignKey('usuarios.id_usuario'),
        nullable=False
    )
    id_producto = db.Column(
        db.Integer,
        db.ForeignKey('productos.id_producto'),
        nullable=False
    )
    cantidad = db.Column(db.Integer, nullable=False, default=1)

    # Un usuario no puede tener el mismo producto repetido en su carrito
    __table_args__ = (
        db.UniqueConstraint('id_usuario', 'id_producto', name='uq_carrito_usuario_producto'),
    )


# ===========================================================================
# MODELO: Favorito
# ===========================================================================
class Favorito(db.Model):
    """
    Representa un producto marcado como favorito por un usuario.

    Al igual que el carrito, se persiste en la base de datos para que
    no se pierda al cerrar la sesion.

    Atributos:
        id_favorito (PK) : Identificador unico autoincremental.
        id_usuario (FK)  : Usuario que marco el favorito.
        id_producto (FK) : Producto favorito.
    """

    __tablename__ = 'favoritos'

    id_favorito = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(
        db.Integer,
        db.ForeignKey('usuarios.id_usuario'),
        nullable=False
    )
    id_producto = db.Column(
        db.Integer,
        db.ForeignKey('productos.id_producto'),
        nullable=False
    )

    # Un usuario solo puede tener cada producto una vez en favoritos
    __table_args__ = (
        db.UniqueConstraint('id_usuario', 'id_producto', name='uq_favorito_usuario_producto'),
    )

"""
ERP - Tienda de Tecnologia
Blueprint: Gestion de Productos e Inventario (products).

RF05: Admin puede registrar, editar y eliminar productos (CRUD).
RF06: Consulta de stock disponible de un producto.

Rutas (requieren autenticacion):
    GET    /products/            -> Listado de productos
    GET    /products/<id>/stock  -> Consulta de stock (RF06)
    GET    /products/crear       -> Formulario de nuevo producto
    POST   /products/crear       -> Procesar creacion de producto
    GET    /products/<id>/editar -> Formulario de edicion
    POST   /products/<id>/editar -> Procesar edicion
    POST   /products/<id>/eliminar -> Eliminar producto
"""

from functools import wraps
import os

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user

from app.models import db, Producto
from app.utils import guardar_imagen, eliminar_imagen

products_bp = Blueprint('products', __name__, url_prefix='/products')


# ---------------------------------------------------------------------------
# Decorador: restringir acceso a administradores
# ---------------------------------------------------------------------------
def admin_requerido(f):
    """
    Decorador que verifica si el usuario actual es administrador.
    Si no lo es, redirige al catalogo con un mensaje de error.
    """
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.es_admin():
            flash('Acceso denegado. Se requiere rol de administrador.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)

    return decorated


# ---------------------------------------------------------------------------
# LISTADO DE PRODUCTOS - RF05
# ---------------------------------------------------------------------------
@products_bp.route('/')
@login_required
def listar():
    """
    Muestra la lista de todos los productos con opciones de gestion.
    Accesible para cualquier usuario autenticado (consulta).
    Solo admin puede ver botones de editar/eliminar.
    """
    productos = Producto.query.order_by(Producto.nombre).all()
    return render_template('products/list.html', productos=productos)


# ---------------------------------------------------------------------------
# CONSULTA DE STOCK - RF06
# ---------------------------------------------------------------------------
@products_bp.route('/<int:producto_id>/stock')
@login_required
def ver_stock(producto_id):
    """
    Muestra el detalle de stock de un producto especifico (RF06).
    """
    producto = Producto.query.get_or_404(producto_id)
    return render_template('products/stock.html', producto=producto)


# ---------------------------------------------------------------------------
# CREAR PRODUCTO - RF05
# ---------------------------------------------------------------------------
@products_bp.route('/crear', methods=['GET', 'POST'])
@admin_requerido
def crear():
    """
    GET:  Muestra formulario para registrar un nuevo producto.
    POST: Procesa el formulario y crea el producto en la base de datos.
    """
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        precio = request.form.get('precio', '').strip()
        stock = request.form.get('stock', '').strip()
        categoria = request.form.get('categoria', '').strip()
        quitar_imagen = request.form.get('quitar_imagen') == '1'

        # Validaciones
        errores = []

        if not nombre:
            errores.append('El nombre del producto es obligatorio.')

        try:
            precio_float = float(precio)
            if precio_float < 0:
                errores.append('El precio no puede ser negativo.')
        except ValueError:
            errores.append('El precio debe ser un numero valido.')

        try:
            stock_int = int(stock)
            if stock_int < 0:
                errores.append('El stock no puede ser negativo.')
        except ValueError:
            errores.append('El stock debe ser un numero entero valido.')

        # Validar imagen subida (si viene una)
        nueva_imagen = None
        if request.files.get('imagen') and request.files['imagen'].filename:
            try:
                nueva_imagen = guardar_imagen(request.files['imagen'])
            except ValueError as e:
                errores.append(str(e))

        if errores:
            for error in errores:
                flash(error, 'error')
            return render_template('products/create.html')

        # Crear producto
        nuevo = Producto(
            nombre=nombre,
            descripcion=descripcion,
            precio=precio_float,
            stock=stock_int,
            categoria=categoria,
            imagen=nueva_imagen
        )
        db.session.add(nuevo)
        db.session.commit()

        flash(f'Producto "{nombre}" creado exitosamente.', 'success')
        return redirect(url_for('products.listar'))

    return render_template('products/create.html')


# ---------------------------------------------------------------------------
# EDITAR PRODUCTO - RF05
# ---------------------------------------------------------------------------
@products_bp.route('/<int:producto_id>/editar', methods=['GET', 'POST'])
@admin_requerido
def editar(producto_id):
    """
    GET:  Muestra formulario pre-rellenado para editar un producto.
    POST: Procesa los cambios y actualiza el producto.
    """
    producto = Producto.query.get_or_404(producto_id)

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        precio = request.form.get('precio', '').strip()
        stock = request.form.get('stock', '').strip()
        categoria = request.form.get('categoria', '').strip()
        quitar_imagen = request.form.get('quitar_imagen') == '1'

        # Validaciones (mismas que en creacion)
        errores = []

        if not nombre:
            errores.append('El nombre del producto es obligatorio.')

        try:
            precio_float = float(precio)
            if precio_float < 0:
                errores.append('El precio no puede ser negativo.')
        except ValueError:
            errores.append('El precio debe ser un numero valido.')

        try:
            stock_int = int(stock)
            if stock_int < 0:
                errores.append('El stock no puede ser negativo.')
        except ValueError:
            errores.append('El stock debe ser un numero entero valido.')

        # Validar imagen subida (si viene una)
        nueva_imagen = None
        if request.files.get('imagen') and request.files['imagen'].filename:
            try:
                nueva_imagen = guardar_imagen(request.files['imagen'])
            except ValueError as e:
                errores.append(str(e))

        if errores:
            for error in errores:
                flash(error, 'error')
            return render_template('products/edit.html', producto=producto)

        # Actualizar campos
        producto.nombre = nombre
        producto.descripcion = descripcion
        producto.precio = precio_float
        producto.stock = stock_int
        producto.categoria = categoria

        # Manejar imagen: reemplazar, mantener o quitar
        if nueva_imagen:
            eliminar_imagen(producto.imagen)
            producto.imagen = nueva_imagen
        elif quitar_imagen:
            eliminar_imagen(producto.imagen)
            producto.imagen = None

        db.session.commit()

        flash(f'Producto "{nombre}" actualizado exitosamente.', 'success')
        return redirect(url_for('products.listar'))

    return render_template('products/edit.html', producto=producto)


# ---------------------------------------------------------------------------
# ELIMINAR PRODUCTO - RF05
# ---------------------------------------------------------------------------
@products_bp.route('/<int:producto_id>/eliminar', methods=['POST'])
@admin_requerido
def eliminar(producto_id):
    """
    Elimina un producto del inventario.

    Nota: si el producto tiene referencias en facturas existentes,
    la base de datos impedira su eliminacion por integridad referencial (RNF05).
    """
    producto = Producto.query.get_or_404(producto_id)

    try:
        db.session.delete(producto)
        db.session.commit()
        eliminar_imagen(producto.imagen)
        flash(f'Producto "{producto.nombre}" eliminado.', 'success')
    except Exception:
        db.session.rollback()
        flash(
            'No se puede eliminar el producto porque tiene facturas asociadas. '
            'Elimine primero las facturas o considere descontinuarlo en su lugar.',
            'error'
        )

    return redirect(url_for('products.listar'))

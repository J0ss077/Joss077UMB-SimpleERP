"""
ERP - Tienda de Tecnologia
Blueprint: Tienda del cliente (tienda).

Experiencia de compra para el rol cliente:
    - Carrito de compras en sesion (sin persistir en BD).
    - Favoritos en sesion.
    - Detalle de producto.
    - Confirmacion de pedido despues del checkout.

Rutas (requieren autenticacion):
    GET    /tienda/producto/<id>           -> Detalle de producto
    POST   /tienda/carrito/agregar         -> Agregar producto al carrito
    GET    /tienda/carrito                 -> Ver carrito
    POST   /tienda/carrito/actualizar      -> Actualizar cantidades
    POST   /tienda/carrito/eliminar        -> Quitar producto del carrito
    POST   /tienda/carrito/vaciar          -> Vaciar carrito
    POST   /tienda/carrito/checkout        -> Finalizar compra (transaccion ACID)
    GET    /tienda/pedido/<factura_id>     -> Confirmacion de pedido
    POST   /tienda/favoritos/toggle        -> Marcar/desmarcar favorito
    GET    /tienda/favoritos               -> Ver favoritos
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user

from app.models import db, Producto, Factura
from app.invoices import crear_factura_transaccional

tienda_bp = Blueprint('tienda', __name__, url_prefix='/tienda')


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------
def _es_cliente():
    """True si el usuario actual tiene rol 'cliente'."""
    return current_user.get_rol() == 'cliente'


def _leer_carrito():
    """Devuelve el carrito de sesion: {id_producto: cantidad}."""
    return dict(session.get('carrito', {}))


def _guardar_carrito(carrito):
    """Persiste el carrito en la sesion."""
    session['carrito'] = {int(k): v for k, v in carrito.items() if int(v) > 0}


def _cantidad_carrito():
    """Suma total de unidades en el carrito."""
    return sum(session.get('carrito', {}).values())


def _leer_favoritos():
    """Devuelve la lista de ids favoritos de la sesion."""
    return list(session.get('favoritos', []))


def _guardar_favoritos(favoritos):
    """Persiste los favoritos en la sesion."""
    session['favoritos'] = list(set(int(x) for x in favoritos))


def _exigir_cliente():
    """Bloquea el acceso a la tienda para roles que no son cliente."""
    if not _es_cliente():
        flash('La tienda con carrito es exclusiva para clientes.', 'error')
        return redirect(url_for('main.index'))


# ---------------------------------------------------------------------------
# DETALLE DE PRODUCTO
# ---------------------------------------------------------------------------
@tienda_bp.route('/producto/<int:producto_id>')
@login_required
def ver_producto(producto_id):
    """Muestra el detalle completo de un producto y permite agregarlo al carrito."""
    producto = Producto.query.get_or_404(producto_id)
    return render_template('producto_detalle.html', producto=producto)


# ---------------------------------------------------------------------------
# CARRITO DE COMPRAS
# ---------------------------------------------------------------------------
@tienda_bp.route('/carrito/agregar', methods=['POST'])
@login_required
def agregar_carrito():
    """Agrega un producto al carrito validando stock (solo clientes)."""
    if not _es_cliente():
        flash('La tienda con carrito es exclusiva para clientes.', 'error')
        return redirect(url_for('main.catalogo'))

    try:
        producto_id = int(request.form.get('producto_id', 0))
        cantidad = max(1, int(request.form.get('cantidad', 1) or 1))
    except ValueError:
        flash('Datos invalidos para agregar al carrito.', 'error')
        return redirect(url_for('main.catalogo'))

    producto = Producto.query.get_or_404(producto_id)

    if not producto.hay_stock_suficiente(cantidad):
        flash(f'Stock insuficiente para "{producto.nombre}". Disponible: {producto.stock}.', 'error')
        return redirect(request.referrer or url_for('main.catalogo'))

    carrito = _leer_carrito()
    carrito[producto_id] = carrito.get(producto_id, 0) + cantidad

    # No permitir superar el stock disponible
    if carrito[producto_id] > producto.stock:
        carrito[producto_id] = producto.stock

    _guardar_carrito(carrito)
    flash(f'"{producto.nombre}" agregado al carrito ({cantidad} unidad/es).', 'success')
    return redirect(request.referrer or url_for('main.catalogo'))


@tienda_bp.route('/carrito')
@login_required
def ver_carrito():
    """Muestra el contenido del carrito con subtotales y total."""
    carrito = _leer_carrito()

    items = []
    total = 0
    for producto_id, cantidad in carrito.items():
        producto = Producto.query.get(int(producto_id))
        if not producto:
            continue
        subtotal = producto.get_precio() * cantidad
        total += subtotal
        items.append({
            'producto': producto,
            'cantidad': cantidad,
            'subtotal': subtotal,
        })

    return render_template('carrito.html', items=items, total=total)


@tienda_bp.route('/carrito/actualizar', methods=['POST'])
@login_required
def actualizar_carrito():
    """Actualiza las cantidades del carrito desde el formulario."""
    if not _es_cliente():
        return redirect(url_for('main.index'))

    carrito = _leer_carrito()
    for key, value in request.form.items():
        if key.startswith('cantidad_'):
            try:
                producto_id = int(key.replace('cantidad_', ''))
                cantidad = max(0, int(value or 0))
                producto = Producto.query.get(producto_id)
                if producto:
                    cantidad = min(cantidad, producto.stock)
                if cantidad > 0:
                    carrito[producto_id] = cantidad
                else:
                    carrito.pop(producto_id, None)
            except ValueError:
                continue

    _guardar_carrito(carrito)
    flash('Carrito actualizado.', 'success')
    return redirect(url_for('tienda.ver_carrito'))


@tienda_bp.route('/carrito/eliminar', methods=['POST'])
@login_required
def eliminar_carrito():
    """Quita un producto del carrito."""
    if not _es_cliente():
        return redirect(url_for('main.index'))

    try:
        producto_id = int(request.form.get('producto_id', 0))
    except ValueError:
        producto_id = 0

    carrito = _leer_carrito()
    carrito.pop(producto_id, None)
    _guardar_carrito(carrito)
    flash('Producto eliminado del carrito.', 'success')
    return redirect(url_for('tienda.ver_carrito'))


@tienda_bp.route('/carrito/vaciar', methods=['POST'])
@login_required
def vaciar_carrito():
    """Vacia el carrito por completo."""
    if not _es_cliente():
        return redirect(url_for('main.index'))

    session['carrito'] = {}
    flash('Carrito vaciado.', 'info')
    return redirect(url_for('tienda.ver_carrito'))


@tienda_bp.route('/carrito/checkout', methods=['POST'])
@login_required
def checkout():
    """
    Finaliza la compra: crea la factura con transaccion ACID
    y vacia el carrito. Redirige a la confirmacion de pedido.
    """
    if not _es_cliente():
        flash('La tienda con carrito es exclusiva para clientes.', 'error')
        return redirect(url_for('main.index'))

    carrito = _leer_carrito()
    if not carrito:
        flash('Tu carrito esta vacio. Agrega productos antes de comprar.', 'error')
        return redirect(url_for('tienda.ver_carrito'))

    # Construir lineas de venta
    lineas_venta = []
    for producto_id, cantidad in carrito.items():
        producto = Producto.query.get(int(producto_id))
        if producto and cantidad > 0:
            lineas_venta.append((producto, cantidad))

    if not lineas_venta:
        flash('Tu carrito esta vacio. Agrega productos antes de comprar.', 'error')
        return redirect(url_for('tienda.ver_carrito'))

    # Transaccion ACID compartida con la facturacion directa
    factura, error = crear_factura_transaccional(current_user.id_usuario, lineas_venta)

    if error:
        flash(error, 'error')
        return redirect(url_for('tienda.ver_carrito'))

    session['carrito'] = {}
    flash(f'Compra realizada. Factura #{factura.id_factura} generada.', 'success')
    return redirect(url_for('tienda.pedido', factura_id=factura.id_factura))


# ---------------------------------------------------------------------------
# CONFIRMACION DE PEDIDO
# ---------------------------------------------------------------------------
@tienda_bp.route('/pedido/<int:factura_id>')
@login_required
def pedido(factura_id):
    """Confirmacion de compra con el resumen del pedido."""
    factura = Factura.query.get_or_404(factura_id)

    # Solo el dueno o el admin pueden ver la confirmacion
    if not current_user.es_admin() and factura.id_usuario != current_user.id_usuario:
        flash('No tienes permiso para ver este pedido.', 'error')
        return redirect(url_for('invoices.listar'))

    return render_template('pedido.html', factura=factura)


# ---------------------------------------------------------------------------
# FAVORITOS
# ---------------------------------------------------------------------------
@tienda_bp.route('/favoritos/toggle', methods=['POST'])
@login_required
def toggle_favorito():
    """Marca o desmarca un producto como favorito (solo clientes)."""
    if not _es_cliente():
        flash('Los favoritos son exclusivos para clientes.', 'error')
        return redirect(url_for('main.catalogo'))

    try:
        producto_id = int(request.form.get('producto_id', 0))
    except ValueError:
        producto_id = 0

    favoritos = _leer_favoritos()

    if producto_id in favoritos:
        favoritos.remove(producto_id)
        flash('Producto quitado de favoritos.', 'info')
    else:
        favoritos.append(producto_id)
        flash('Producto agregado a favoritos.', 'success')

    _guardar_favoritos(favoritos)
    return redirect(request.referrer or url_for('main.catalogo'))


@tienda_bp.route('/favoritos')
@login_required
def ver_favoritos():
    """Muestra los productos marcados como favoritos."""
    favoritos_ids = _leer_favoritos()

    productos = []
    for producto_id in favoritos_ids:
        producto = Producto.query.get(int(producto_id))
        if producto:
            productos.append(producto)

    return render_template('favoritos.html', productos=productos)

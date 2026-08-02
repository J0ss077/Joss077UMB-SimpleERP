"""
ERP - Tienda de Tecnologia
Blueprint: Tienda del cliente (tienda).

Experiencia de compra para el rol cliente:
    - Carrito de compras persistente en BD (sobrevive al cierre de sesion).
    - Favoritos persistentes en BD.
    - Detalle de producto.
    - Checkout en 2 pasos: confirmar envio + transaccion ACID.
    - Confirmacion de pedido despues del checkout.

Rutas (requieren autenticacion):
    GET    /tienda/producto/<id>           -> Detalle de producto
    POST   /tienda/carrito/agregar         -> Agregar producto al carrito
    GET    /tienda/carrito                 -> Ver carrito
    POST   /tienda/carrito/actualizar      -> Actualizar cantidades
    POST   /tienda/carrito/eliminar        -> Quitar producto del carrito
    POST   /tienda/carrito/vaciar          -> Vaciar carrito
    GET    /tienda/carrito/checkout        -> Confirmar envio (paso 1)
    POST   /tienda/carrito/checkout        -> Finalizar compra (transaccion ACID)
    GET    /tienda/pedido/<factura_id>     -> Confirmacion de pedido
    POST   /tienda/favoritos/toggle        -> Marcar/desmarcar favorito
    GET    /tienda/favoritos               -> Ver favoritos
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.models import db, Producto, Factura, CarritoItem, Favorito
from app.invoices import crear_factura_transaccional

tienda_bp = Blueprint('tienda', __name__, url_prefix='/tienda')


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------
def _es_cliente():
    """True si el usuario actual tiene rol 'cliente'."""
    return current_user.get_rol() == 'cliente'


def _leer_carrito():
    """
    Devuelve el carrito del usuario desde la BD: {id_producto: cantidad}.

    Compatible con la forma anterior del carrito de sesion.
    """
    items = CarritoItem.query.filter_by(id_usuario=current_user.id_usuario).all()
    return {item.id_producto: item.cantidad for item in items}


def _leer_favoritos():
    """Devuelve el conjunto de ids de productos favoritos del usuario."""
    filas = Favorito.query.filter_by(id_usuario=current_user.id_usuario).all()
    return {fila.id_producto for fila in filas}


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
    """Agrega un producto al carrito (BD) validando stock (solo clientes)."""
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

    item = CarritoItem.query.filter_by(
        id_usuario=current_user.id_usuario,
        id_producto=producto_id
    ).first()

    if item:
        # Sumar a lo que ya habia, sin superar el stock disponible
        item.cantidad = min(item.cantidad + cantidad, producto.stock)
    else:
        item = CarritoItem(
            id_usuario=current_user.id_usuario,
            id_producto=producto_id,
            cantidad=min(cantidad, producto.stock)
        )
        db.session.add(item)

    db.session.commit()
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
        producto = Producto.query.get(producto_id)
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

    for key, value in request.form.items():
        if key.startswith('cantidad_'):
            try:
                producto_id = int(key.replace('cantidad_', ''))
                cantidad = max(0, int(value or 0))
                producto = Producto.query.get(producto_id)
                if producto:
                    cantidad = min(cantidad, producto.stock)
                item = CarritoItem.query.filter_by(
                    id_usuario=current_user.id_usuario,
                    id_producto=producto_id
                ).first()
                if not item:
                    continue
                if cantidad > 0:
                    item.cantidad = cantidad
                else:
                    db.session.delete(item)
            except ValueError:
                continue

    db.session.commit()
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

    item = CarritoItem.query.filter_by(
        id_usuario=current_user.id_usuario,
        id_producto=producto_id
    ).first()
    if item:
        db.session.delete(item)
        db.session.commit()
        flash('Producto eliminado del carrito.', 'success')

    return redirect(url_for('tienda.ver_carrito'))


@tienda_bp.route('/carrito/vaciar', methods=['POST'])
@login_required
def vaciar_carrito():
    """Vacia el carrito por completo."""
    if not _es_cliente():
        return redirect(url_for('main.index'))

    CarritoItem.query.filter_by(id_usuario=current_user.id_usuario).delete()
    db.session.commit()
    flash('Carrito vaciado.', 'info')
    return redirect(url_for('tienda.ver_carrito'))


@tienda_bp.route('/carrito/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    """
    Finaliza la compra en 2 pasos:
        GET:  Muestra el formulario de confirmacion de envio (paso 1).
        POST: Crea la factura con transaccion ACID y vacia el carrito.
    """
    if not _es_cliente():
        flash('La tienda con carrito es exclusiva para clientes.', 'error')
        return redirect(url_for('main.index'))

    carrito = _leer_carrito()
    if not carrito:
        flash('Tu carrito esta vacio. Agrega productos antes de comprar.', 'error')
        return redirect(url_for('tienda.ver_carrito'))

    if request.method == 'GET':
        # Paso 1: confirmar datos de envio (pre-llenados desde el perfil)
        items = []
        total = 0
        for producto_id, cantidad in carrito.items():
            producto = Producto.query.get(producto_id)
            if not producto:
                continue
            subtotal = producto.get_precio() * cantidad
            total += subtotal
            items.append({
                'producto': producto,
                'cantidad': cantidad,
                'subtotal': subtotal,
            })

        return render_template(
            'checkout.html',
            direccion=current_user.direccion or '',
            ciudad=current_user.ciudad or '',
            telefono=current_user.telefono or '',
            items=items,
            total=total
        )

    # Paso 2: procesar la compra
    direccion = request.form.get('direccion', '').strip()
    ciudad = request.form.get('ciudad', '').strip()
    telefono = request.form.get('telefono', '').strip()

    if not direccion or not ciudad:
        flash('La direccion y la ciudad de envio son obligatorias.', 'error')
        items_previa = []
        total_previo = 0
        for producto_id, cantidad in carrito.items():
            producto = Producto.query.get(producto_id)
            if not producto:
                continue
            subtotal = producto.get_precio() * cantidad
            total_previo += subtotal
            items_previa.append({
                'producto': producto,
                'cantidad': cantidad,
                'subtotal': subtotal,
            })
        return render_template(
            'checkout.html',
            direccion=direccion,
            ciudad=ciudad,
            telefono=telefono,
            items=items_previa,
            total=total_previo
        )

    # Construir lineas de venta desde la BD
    lineas_venta = []
    for producto_id, cantidad in carrito.items():
        producto = Producto.query.get(producto_id)
        if producto and cantidad > 0:
            lineas_venta.append((producto, cantidad))

    if not lineas_venta:
        flash('Tu carrito esta vacio. Agrega productos antes de comprar.', 'error')
        return redirect(url_for('tienda.ver_carrito'))

    # Transaccion ACID compartida con la facturacion directa
    factura, error = crear_factura_transaccional(
        current_user.id_usuario,
        lineas_venta,
        direccion_envio=direccion,
        ciudad_envio=ciudad,
        telefono_contacto=telefono
    )

    if error:
        flash(error, 'error')
        return redirect(url_for('tienda.ver_carrito'))

    # Vaciar carrito en BD
    CarritoItem.query.filter_by(id_usuario=current_user.id_usuario).delete()
    db.session.commit()

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
# RECOMPRAR PEDIDO ANTERIOR
# ---------------------------------------------------------------------------
@tienda_bp.route('/recomprar/<int:factura_id>', methods=['POST'])
@login_required
def recomprar(factura_id):
    """
    Vuelve a agregar al carrito los productos de una factura anterior.

    Solo el dueno de la factura puede recomprar. Los productos sin stock
    disponible se omiten y se informa al usuario.
    """
    factura = Factura.query.get_or_404(factura_id)

    if factura.id_usuario != current_user.id_usuario:
        flash('No tienes permiso para reordenar este pedido.', 'error')
        return redirect(url_for('invoices.listar'))

    if factura.esta_anulada():
        flash('No puedes recomprar una factura anulada.', 'error')
        return redirect(url_for('invoices.listar'))

    agregados = 0
    omitidos = 0
    for detalle in factura.detalles:
        producto = detalle.producto
        if not producto or not producto.hay_stock_suficiente(1):
            omitidos += 1
            continue

        item = CarritoItem.query.filter_by(
            id_usuario=current_user.id_usuario,
            id_producto=producto.id_producto
        ).first()

        cantidad = min(detalle.cantidad, producto.stock)
        if item:
            item.cantidad = min(item.cantidad + cantidad, producto.stock)
        else:
            db.session.add(CarritoItem(
                id_usuario=current_user.id_usuario,
                id_producto=producto.id_producto,
                cantidad=cantidad
            ))
        agregados += 1

    db.session.commit()

    if agregados:
        flash(f'Productos de la factura #{factura_id} agregados al carrito.', 'success')
    if omitidos:
        flash(f'{omitidos} producto(s) sin stock fueron omitidos.', 'warning')
    if not agregados:
        flash('Ningun producto de esta factura tiene stock disponible.', 'error')

    return redirect(url_for('tienda.ver_carrito'))


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

    existente = Favorito.query.filter_by(
        id_usuario=current_user.id_usuario,
        id_producto=producto_id
    ).first()

    if existente:
        db.session.delete(existente)
        flash('Producto quitado de favoritos.', 'info')
    else:
        db.session.add(Favorito(
            id_usuario=current_user.id_usuario,
            id_producto=producto_id
        ))
        flash('Producto agregado a favoritos.', 'success')

    db.session.commit()
    return redirect(request.referrer or url_for('main.catalogo'))


@tienda_bp.route('/favoritos')
@login_required
def ver_favoritos():
    """Muestra los productos marcados como favoritos."""
    favoritos_ids = _leer_favoritos()

    productos = []
    for producto_id in favoritos_ids:
        producto = Producto.query.get(producto_id)
        if producto:
            productos.append(producto)

    return render_template('favoritos.html', productos=productos)

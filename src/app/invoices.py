"""
ERP - Tienda de Tecnologia
Blueprint: Facturacion (invoices).

Maneja la creacion y anulacion de facturas con transacciones ACID.

RF07: Generar factura con fecha, cliente, detalle y total.
RF08: Calcular automaticamente el total de la factura.
RF09: Descontar stock al confirmar factura.
RF10: Anular factura y revertir el stock descontado.
RNF01: Transaccion atomica (factura + descuento de stock juntos o ninguno).

Rutas (requieren autenticacion):
    GET    /invoices/              -> Historial de facturas (RF11)
    GET    /invoices/crear         -> Formulario para nueva factura
    POST   /invoices/crear         -> Procesar y crear factura (transaccion ACID)
    GET    /invoices/<id>          -> Ver detalle de factura
    POST   /invoices/<id>/anular   -> Anular factura y revertir stock (RF10)
"""

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import db, Producto, Factura, DetalleFactura, Usuario

invoices_bp = Blueprint('invoices', __name__, url_prefix='/invoices')


# ---------------------------------------------------------------------------
# LOGICA COMPARTIDA: TRANSACCION ACID (RNF01)
# ---------------------------------------------------------------------------
def crear_factura_transaccional(id_cliente, lineas_venta,
                                direccion_envio=None, ciudad_envio=None,
                                telefono_contacto=None):
    """
    Crea una factura con transaccion ACID (RNF01).

    Argumentos:
        id_cliente        : id_usuario asociado a la factura (cliente de la venta).
        lineas_venta      : lista de tuplas (producto, cantidad).
        direccion_envio   : direccion de entrega del pedido (opcional).
        ciudad_envio      : ciudad de entrega del pedido (opcional).
        telefono_contacto : telefono de contacto para el envio (opcional).

    Retorna:
        (factura, None)      en exito.
        (None, mensaje)      en error (stock insuficiente u otro fallo).
    """
    try:
        # Crear cabecera de factura
        factura = Factura(
            id_usuario=id_cliente,
            fecha=datetime.utcnow(),
            estado='activa',
            direccion_envio=direccion_envio,
            ciudad_envio=ciudad_envio,
            telefono_contacto=telefono_contacto
        )
        db.session.add(factura)
        db.session.flush()  # Obtener id_factura sin hacer commit aun

        # Procesar cada linea de detalle
        for producto, cantidad in lineas_venta:
            # Validar stock suficiente
            if not producto.hay_stock_suficiente(cantidad):
                raise ValueError(
                    f'Stock insuficiente para "{producto.nombre}". '
                    f'Disponible: {producto.stock}, solicitado: {cantidad}'
                )

            # Congelar precio actual del producto
            precio_unitario = producto.get_precio()
            subtotal = cantidad * precio_unitario

            # Crear linea de detalle
            detalle = DetalleFactura(
                id_factura=factura.id_factura,
                id_producto=producto.id_producto,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                subtotal=subtotal
            )
            db.session.add(detalle)

            # Descontar stock (RF09)
            producto.actualizar_stock(-cantidad)

        # Calcular total de la factura (RF08)
        factura.calcular_total()

        # --- Confirmar transaccion (COMMIT) ---
        db.session.commit()
        return factura, None

    except ValueError as e:
        # Error de negocio (ej. stock insuficiente)
        db.session.rollback()
        return None, str(e)

    except Exception as e:
        # Cualquier otro error: deshacer todo (ROLLBACK)
        db.session.rollback()
        return None, f'Error al crear la factura: {str(e)}'


# ---------------------------------------------------------------------------
# HISTORIAL DE FACTURAS - RF11
# ---------------------------------------------------------------------------
@invoices_bp.route('/')
@login_required
def listar():
    """
    Muestra el historial de facturas.

    - Admin y vendedor: ven todas las facturas del sistema con mini-metricas.
    - Cliente: ve las facturas donde el es el cliente asociado (RF11).
    """
    if current_user.es_admin() or current_user.get_rol() == 'vendedor':
        facturas = Factura.query.order_by(Factura.fecha.desc()).all()
        activas = [f for f in facturas if not f.esta_anulada()]
        metricas = {
            'total': len(facturas),
            'activas': len(activas),
            'monto_total': sum(f.get_total() for f in activas),
            'promedio': (sum(f.get_total() for f in activas) / len(activas))
                        if activas else 0,
            'pendientes': sum(1 for f in activas if f.estado_pedido == 'pendiente'),
        }
    else:
        facturas = (
            Factura.query
            .filter_by(id_usuario=current_user.id_usuario)
            .order_by(Factura.fecha.desc())
            .all()
        )
        metricas = None

    return render_template('invoices/list.html', facturas=facturas, metricas=metricas)


# ---------------------------------------------------------------------------
# CREAR FACTURA (TRANSACCION ACID) - RF07, RF08, RF09, RNF01
# ---------------------------------------------------------------------------
@invoices_bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear():
    """
    Crea una nueva factura de venta.

    Flujo:
        GET:  Muestra el formulario con la lista de productos disponibles.
              El usuario ingresa cantidades para los productos que desea vender.
        POST: Procesa la factura en una transaccion ACID:
              1. Validar stock suficiente para cada producto solicitado.
              2. Crear cabecera de factura.
              3. Crear lineas de detalle por cada producto seleccionado.
              4. Descontar stock de cada producto.
              5. Calcular total.
              6. Confirmar (commit) o deshacer (rollback) todo junto.
    """
    # Los clientes compran desde el carrito (tienda)
    if current_user.get_rol() == 'cliente':
        flash('Como cliente puedes comprar desde tu carrito.', 'info')
        return redirect(url_for('tienda.ver_carrito'))

    # Obtener clientes para selector (admin/vendedor pueden elegir)
    clientes = None
    if current_user.es_admin() or current_user.get_rol() == 'vendedor':
        clientes = Usuario.query.order_by(Usuario.nombre).all()

    if request.method == 'POST':
        # --- Paso 0: Obtener datos del formulario ---
        id_cliente = request.form.get('id_cliente', '').strip()

        # Determinar el cliente asociado a la factura
        if id_cliente and (current_user.es_admin() or current_user.get_rol() == 'vendedor'):
            try:
                id_cliente = int(id_cliente)
            except ValueError:
                flash('Debes seleccionar un cliente valido de la lista.', 'error')
                return redirect(url_for('invoices.crear'))
        else:
            id_cliente = current_user.id_usuario

        # --- Paso 1: Recolectar productos con cantidad > 0 ---
        lineas_venta = []  # Lista de tuplas: (producto, cantidad)

        for key, value in request.form.items():
            if key.startswith('cantidad_') and value.strip():
                try:
                    cantidad = int(value)
                    if cantidad > 0:
                        producto_id = int(key.replace('cantidad_', ''))
                        producto = Producto.query.get(producto_id)
                        if producto:
                            lineas_venta.append((producto, cantidad))
                except ValueError:
                    continue

        if not lineas_venta:
            flash('Debes seleccionar al menos un producto con cantidad mayor a cero.', 'error')
            return redirect(url_for('invoices.crear'))

        # --- Paso 2: Ejecutar transaccion ACID compartida ---
        factura, error = crear_factura_transaccional(id_cliente, lineas_venta)

        if error:
            flash(error, 'error')
            return redirect(url_for('invoices.crear'))

        flash(
            f'Factura #{factura.id_factura} creada exitosamente. '
            f'Total: ${factura.get_total():.2f}',
            'success'
        )
        return redirect(url_for('invoices.ver', factura_id=factura.id_factura))

    # GET: mostrar formulario con productos disponibles
    productos = Producto.query.filter(Producto.stock > 0).order_by(Producto.nombre).all()
    return render_template(
        'invoices/create.html',
        productos=productos,
        clientes=clientes
    )


# ---------------------------------------------------------------------------
# ESTADO DEL PEDIDO - RF12
# ---------------------------------------------------------------------------
@invoices_bp.route('/<int:factura_id>/estado', methods=['POST'])
@login_required
def cambiar_estado(factura_id):
    """
    Actualiza el estado del pedido de una factura (pendiente/enviado/entregado).

    Solo admin y vendedor pueden actualizar el estado.
    """
    if current_user.get_rol() not in ('admin', 'vendedor'):
        flash('Solo administrador o vendedor pueden actualizar el estado del pedido.', 'error')
        return redirect(url_for('invoices.listar'))

    factura = Factura.query.get_or_404(factura_id)

    if factura.esta_anulada():
        flash('No puedes cambiar el estado de una factura anulada.', 'error')
        return redirect(url_for('invoices.ver', factura_id=factura_id))

    nuevo_estado = request.form.get('estado', '').strip()
    if nuevo_estado not in ('pendiente', 'enviado', 'entregado'):
        flash('Estado invalido.', 'error')
        return redirect(url_for('invoices.ver', factura_id=factura_id))

    factura.estado_pedido = nuevo_estado
    db.session.commit()
    flash(
        f'Estado del pedido #{factura.id_factura} actualizado a "{nuevo_estado}".',
        'success'
    )
    return redirect(url_for('invoices.ver', factura_id=factura_id))


# ---------------------------------------------------------------------------
# VER DETALLE DE FACTURA - RF07
# ---------------------------------------------------------------------------
@invoices_bp.route('/<int:factura_id>')
@login_required
def ver(factura_id):
    """
    Muestra el detalle completo de una factura:
    cabecera + lineas de detalle + total (RF07).
    """
    factura = Factura.query.get_or_404(factura_id)

    # Verificar permisos: admin ve todo, otros solo sus facturas
    if not current_user.es_admin() and factura.id_usuario != current_user.id_usuario:
        flash('No tienes permiso para ver esta factura.', 'error')
        return redirect(url_for('invoices.listar'))

    return render_template('invoices/detail.html', factura=factura)


# ---------------------------------------------------------------------------
# ANULAR FACTURA - RF10
# ---------------------------------------------------------------------------
@invoices_bp.route('/<int:factura_id>/anular', methods=['POST'])
@login_required
def anular(factura_id):
    """
    Anula una factura y revierte el stock descontado.

    RF10: La anulacion restaura el inventario de cada producto.
    Toda la operacion es atomica: si algo falla, se deshace todo.

    Solo admin puede anular facturas.
    """
    if not current_user.es_admin():
        flash('Solo el administrador puede anular facturas.', 'error')
        return redirect(url_for('invoices.listar'))

    factura = Factura.query.get_or_404(factura_id)

    if factura.esta_anulada():
        flash('Esta factura ya fue anulada anteriormente.', 'error')
        return redirect(url_for('invoices.ver', factura_id=factura_id))

    try:
        # Revertir stock de cada producto en el detalle
        for detalle in factura.detalles:
            producto = Producto.query.get(detalle.id_producto)
            if producto:
                producto.actualizar_stock(detalle.cantidad)  # Devuelve stock

        # Marcar factura como anulada
        factura.anular()

        db.session.commit()
        flash(f'Factura #{factura.id_factura} anulada. Stock revertido.', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error al anular la factura: {str(e)}', 'error')

    return redirect(url_for('invoices.ver', factura_id=factura_id))

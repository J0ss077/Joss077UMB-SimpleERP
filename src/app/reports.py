"""
ERP - Tienda de Tecnologia
Blueprint: Reportes (reports).

Proporciona reportes basicos para el administrador.

RF12: Admin puede consultar reportes de ventas y stock bajo.

Rutas (solo admin):
    GET /reports/           -> Panel de reportes
    GET /reports/ventas     -> Reporte de ventas (total, facturas emitidas)
    GET /reports/stock-bajo -> Reporte de productos con stock bajo (< 5 unidades)
"""

from functools import wraps
from datetime import datetime
from io import StringIO
import csv
from flask import Blueprint, render_template, redirect, url_for, flash, request, Response
from flask_login import login_required, current_user
from app.models import db, Factura, Producto, DetalleFactura, Usuario
from sqlalchemy import func

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')


# ---------------------------------------------------------------------------
# Decorador local: restringir acceso a administrador
# ---------------------------------------------------------------------------
def admin_requerido(f):
    """Verifica que el usuario actual tenga rol de administrador."""
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.es_admin():
            flash('Acceso denegado. Se requiere rol de administrador.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)

    return decorated


# ---------------------------------------------------------------------------
# PANEL DE REPORTES
# ---------------------------------------------------------------------------
@reports_bp.route('/')
@admin_requerido
def index():
    """Muestra el panel principal de reportes con metricas resumidas."""
    total_productos = Producto.query.count()
    total_facturas = Factura.query.filter_by(estado='activa').count()
    productos_stock_bajo = Producto.query.filter(Producto.stock < 5).count()

    return render_template(
        'reports/index.html',
        total_productos=total_productos,
        total_facturas=total_facturas,
        productos_stock_bajo=productos_stock_bajo
    )


# ---------------------------------------------------------------------------
# HELPERS DE FECHAS
# ---------------------------------------------------------------------------
def _fechas_reporte():
    """
    Lee los parametros 'desde' y 'hasta' de la URL (formato YYYY-MM-DD).
    Devuelve (desde, hasta) como fechas datetime o None si no se indican.
    """
    desde = request.args.get('desde', '').strip()
    hasta = request.args.get('hasta', '').strip()

    try:
        desde_dt = datetime.strptime(desde, '%Y-%m-%d') if desde else None
    except ValueError:
        desde_dt = None
    try:
        hasta_dt = datetime.strptime(hasta, '%Y-%m-%d') if hasta else None
    except ValueError:
        hasta_dt = None

    return desde_dt, hasta_dt


def _filtrar_facturas(desde_dt, hasta_dt):
    """Consulta facturas activas con filtro opcional por rango de fechas."""
    consulta = Factura.query.filter_by(estado='activa')
    if desde_dt:
        consulta = consulta.filter(Factura.fecha >= desde_dt)
    if hasta_dt:
        consulta = consulta.filter(Factura.fecha <= hasta_dt.replace(hour=23, minute=59, second=59))
    return consulta.order_by(Factura.fecha.desc())


# ---------------------------------------------------------------------------
# REPORTE DE VENTAS - RF12
# ---------------------------------------------------------------------------
@reports_bp.route('/ventas')
@admin_requerido
def ventas():
    """
    Reporte de ventas con filtro por rango de fechas:
    total facturado, cantidad de facturas activas y desglose por factura.
    """
    desde_dt, hasta_dt = _fechas_reporte()
    consulta = _filtrar_facturas(desde_dt, hasta_dt)

    total_ventas = (
        db.session.query(func.sum(Factura.total))
        .filter(Factura.estado == 'activa')
        .filter(*([Factura.fecha >= desde_dt] if desde_dt else []))
        .filter(*([Factura.fecha <= hasta_dt.replace(hour=23, minute=59, second=59)] if hasta_dt else []))
        .scalar()
    ) or 0

    facturas = consulta.all()

    return render_template(
        'reports/sales.html',
        total_ventas=float(total_ventas),
        facturas=facturas,
        desde=request.args.get('desde', ''),
        hasta=request.args.get('hasta', '')
    )


# ---------------------------------------------------------------------------
# REPORTE DE VENTAS POR CATEGORIA
# ---------------------------------------------------------------------------
@reports_bp.route('/categorias')
@admin_requerido
def por_categoria():
    """Ventas y unidades vendidas agrupadas por categoria de producto."""
    desde_dt, hasta_dt = _fechas_reporte()

    consulta = (
        db.session.query(
            Producto.categoria,
            func.sum(DetalleFactura.cantidad),
            func.sum(DetalleFactura.subtotal)
        )
        .join(Producto, Producto.id_producto == DetalleFactura.id_producto)
        .join(Factura, Factura.id_factura == DetalleFactura.id_factura)
        .filter(Factura.estado == 'activa')
    )
    if desde_dt:
        consulta = consulta.filter(Factura.fecha >= desde_dt)
    if hasta_dt:
        consulta = consulta.filter(Factura.fecha <= hasta_dt.replace(hour=23, minute=59, second=59))

    filas = consulta.group_by(Producto.categoria).order_by(func.sum(DetalleFactura.subtotal).desc()).all()
    datos = [
        {'categoria': categoria or 'Sin categoria', 'unidades': int(unidades or 0), 'ventas': float(ventas or 0)}
        for categoria, unidades, ventas in filas
    ]

    return render_template(
        'reports/categorias.html',
        datos=datos,
        desde=request.args.get('desde', ''),
        hasta=request.args.get('hasta', '')
    )


# ---------------------------------------------------------------------------
# REPORTE TOP PRODUCTOS
# ---------------------------------------------------------------------------
@reports_bp.route('/top-productos')
@admin_requerido
def top_productos():
    """Top 5 productos mas vendidos por unidades y por ingresos."""
    desde_dt, hasta_dt = _fechas_reporte()

    consulta = (
        db.session.query(
            Producto,
            func.sum(DetalleFactura.cantidad),
            func.sum(DetalleFactura.subtotal)
        )
        .join(Producto, Producto.id_producto == DetalleFactura.id_producto)
        .join(Factura, Factura.id_factura == DetalleFactura.id_factura)
        .filter(Factura.estado == 'activa')
    )
    if desde_dt:
        consulta = consulta.filter(Factura.fecha >= desde_dt)
    if hasta_dt:
        consulta = consulta.filter(Factura.fecha <= hasta_dt.replace(hour=23, minute=59, second=59))

    por_unidades = (
        consulta.group_by(Producto.id_producto)
        .order_by(func.sum(DetalleFactura.cantidad).desc())
        .limit(5)
        .all()
    )
    por_ingresos = (
        consulta.group_by(Producto.id_producto)
        .order_by(func.sum(DetalleFactura.subtotal).desc())
        .limit(5)
        .all()
    )

    def _serializar(filas):
        return [
            {'producto': p, 'unidades': int(u or 0), 'ingresos': float(i or 0)}
            for p, u, i in filas
        ]

    return render_template(
        'reports/top.html',
        por_unidades=_serializar(por_unidades),
        por_ingresos=_serializar(por_ingresos),
        desde=request.args.get('desde', ''),
        hasta=request.args.get('hasta', '')
    )


# ---------------------------------------------------------------------------
# REPORTE DE VENTAS POR CLIENTE
# ---------------------------------------------------------------------------
@reports_bp.route('/clientes')
@admin_requerido
def por_cliente():
    """Ventas totales por cliente (usuario que compro)."""
    desde_dt, hasta_dt = _fechas_reporte()

    consulta = (
        db.session.query(
            Usuario,
            func.count(Factura.id_factura),
            func.sum(Factura.total)
        )
        .join(Factura, Factura.id_usuario == Usuario.id_usuario)
        .filter(Factura.estado == 'activa')
    )
    if desde_dt:
        consulta = consulta.filter(Factura.fecha >= desde_dt)
    if hasta_dt:
        consulta = consulta.filter(Factura.fecha <= hasta_dt.replace(hour=23, minute=59, second=59))

    filas = (
        consulta.group_by(Usuario.id_usuario)
        .order_by(func.sum(Factura.total).desc())
        .all()
    )
    datos = [
        {'usuario': u, 'facturas': int(n or 0), 'total': float(t or 0)}
        for u, n, t in filas
    ]

    return render_template(
        'reports/clientes.html',
        datos=datos,
        desde=request.args.get('desde', ''),
        hasta=request.args.get('hasta', '')
    )


# ---------------------------------------------------------------------------
# EXPORTAR VENTAS A CSV
# ---------------------------------------------------------------------------
@reports_bp.route('/ventas/csv')
@admin_requerido
def ventas_csv():
    """Exporta el reporte de ventas (filtro de fechas incluido) a CSV."""
    desde_dt, hasta_dt = _fechas_reporte()
    facturas = _filtrar_facturas(desde_dt, hasta_dt).all()

    buffer = StringIO()
    escritor = csv.writer(buffer)
    escritor.writerow([
        'id_factura', 'fecha', 'cliente', 'email', 'ciudad',
        'estado_pedido', 'total'
    ])
    for f in facturas:
        escritor.writerow([
            f.id_factura,
            f.fecha.strftime('%Y-%m-%d %H:%M:%S'),
            f.usuario.nombre,
            f.usuario.email,
            f.ciudad_envio or '',
            f.estado_pedido,
            f'{f.get_total():.2f}'
        ])

    nombre_archivo = 'ventas.csv'
    return Response(
        buffer.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={nombre_archivo}'}
    )


# ---------------------------------------------------------------------------
# REPORTE DE STOCK BAJO - RF12
# ---------------------------------------------------------------------------
@reports_bp.route('/stock-bajo')
@admin_requerido
def stock_bajo():
    """
    Reporte de stock bajo: lista productos cuyo stock esta por debajo
    del umbral definido (5 unidades por defecto).
    """
    umbral = 5
    productos = (
        Producto.query
        .filter(Producto.stock < umbral)
        .order_by(Producto.stock.asc())
        .all()
    )

    return render_template(
        'reports/low_stock.html',
        productos=productos,
        umbral=umbral
    )

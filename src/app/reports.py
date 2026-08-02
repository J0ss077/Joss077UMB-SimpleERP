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

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import db, Factura, Producto
from sqlalchemy import func

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')


# ---------------------------------------------------------------------------
# Decorador local: restringir acceso a administrador
# ---------------------------------------------------------------------------
def admin_requerido(f):
    """Verifica que el usuario actual tenga rol de administrador."""
    from functools import wraps
    from flask import redirect, url_for, flash

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
    # Metricas rapidas para el panel
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
# REPORTE DE VENTAS - RF12
# ---------------------------------------------------------------------------
@reports_bp.route('/ventas')
@admin_requerido
def ventas():
    """
    Reporte de ventas: muestra el total facturado, cantidad de facturas
    activas y desglose por factura.
    """
    # Suma total de todas las facturas activas
    total_ventas = (
        db.session.query(func.sum(Factura.total))
        .filter(Factura.estado == 'activa')
        .scalar()
    ) or 0

    # Total de facturas anuladas
    facturas_anuladas = Factura.query.filter_by(estado='anulada').count()

    # Facturas activas con detalle
    facturas = (
        Factura.query
        .filter_by(estado='activa')
        .order_by(Factura.fecha.desc())
        .all()
    )

    return render_template(
        'reports/sales.html',
        total_ventas=float(total_ventas),
        facturas_anuladas=facturas_anuladas,
        facturas=facturas
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

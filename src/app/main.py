"""
ERP - Tienda de Tecnologia
Blueprint: Pagina principal (main).

Rutas:
    GET /          -> Portal de inicio de la empresa (requiere sesion)
    GET /catalogo  -> Catalogo de productos con busqueda y filtro (RF03, RF04)
"""

from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.models import db, Producto

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """
    Portal de inicio de la empresa.

    Si no hay sesion activa, se redirige al login.
    Si hay sesion, se muestra el portal con:
        - Hero de bienvenida
        - Banner promocional
        - Features del sistema
        - Productos destacados
    """
    # Si no hay sesion activa, mostrar primero el login
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))

    # Productos destacados (los primeros 4 con mas stock)
    destacados = (
        Producto.query
        .order_by(Producto.stock.desc(), Producto.nombre)
        .limit(4)
        .all()
    )

    # Categorias disponibles (para la seccion de categorias del portal)
    categorias = [
        row[0] for row in
        Producto.query.with_entities(Producto.categoria).distinct().all()
        if row[0]
    ]

    return render_template(
        'home.html',
        destacados=destacados,
        categorias=categorias
    )


@main_bp.route('/catalogo')
@login_required
def catalogo():
    """
    Catalogo de productos con busqueda, filtro, orden y paginacion (RF03, RF04).

    Parametros de URL (opcionales):
        q (str):          Texto de busqueda (busca en nombre y descripcion).
        categoria (str):  Filtra productos de una categoria especifica.
        orden (str):      Orden: nombre, precio_asc, precio_desc, stock.
        pagina (int):     Numero de pagina (12 productos por pagina).
    """
    # Obtener parametros de busqueda desde la URL
    texto_busqueda = request.args.get('q', '').strip()
    categoria_filtro = request.args.get('categoria', '').strip()
    orden = request.args.get('orden', 'nombre').strip()

    try:
        pagina = max(1, int(request.args.get('pagina', 1)))
    except ValueError:
        pagina = 1

    # Consulta base: todos los productos
    consulta = Producto.query

    # Aplicar filtro por texto (busca en nombre y descripcion)
    if texto_busqueda:
        patron = f'%{texto_busqueda}%'
        consulta = consulta.filter(
            db.or_(
                Producto.nombre.ilike(patron),
                Producto.descripcion.ilike(patron)
            )
        )

    # Aplicar filtro por categoria
    if categoria_filtro:
        consulta = consulta.filter(Producto.categoria == categoria_filtro)

    # Aplicar ordenamiento
    ordenes_validos = {
        'nombre': (Producto.nombre, False),
        'precio_asc': (Producto.precio, False),
        'precio_desc': (Producto.precio, True),
        'stock': (Producto.stock, True),
    }
    if orden not in ordenes_validos:
        orden = 'nombre'
    columna_orden, descendente = ordenes_validos[orden]
    if descendente:
        consulta = consulta.order_by(columna_orden.desc())
    else:
        consulta = consulta.order_by(columna_orden.asc())

    # Paginacion: 12 productos por pagina
    paginacion = consulta.paginate(page=pagina, per_page=12, error_out=False)

    # Obtener lista unica de categorias para los botones de filtro
    categorias = [
        row[0] for row in
        Producto.query.with_entities(Producto.categoria).distinct().all()
        if row[0]
    ]

    return render_template(
        'index.html',
        productos=paginacion.items,
        paginacion=paginacion,
        categorias=categorias,
        texto_busqueda=texto_busqueda,
        categoria_filtro=categoria_filtro,
        orden=orden
    )

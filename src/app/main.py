"""
ERP - Tienda de Tecnologia
Blueprint: Pagina principal y catalogo publico (main).

Rutas publicas que no requieren autenticacion:
    GET /         -> Catalogo de productos con busqueda y filtro (RF03, RF04)
"""

from flask import Blueprint, render_template, request
from app.models import db, Producto

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """
    Pagina principal: catalogo publico de productos.

    RF03: Muestra nombre, precio, stock y categoria de cada producto.
    RF04: Permite buscar por texto y filtrar por categoria.

    Parametros de URL (opcionales):
        q (str):          Texto de busqueda (busca en nombre y descripcion).
        categoria (str):  Filtra productos de una categoria especifica.
    """
    # Obtener parametros de busqueda desde la URL
    texto_busqueda = request.args.get('q', '').strip()
    categoria_filtro = request.args.get('categoria', '').strip()

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

    # Ejecutar consulta
    productos = consulta.order_by(Producto.nombre).all()

    # Obtener lista unica de categorias para los botones de filtro
    categorias = [
        row[0] for row in
        Producto.query.with_entities(Producto.categoria).distinct().all()
    ]

    return render_template(
        'index.html',
        productos=productos,
        categorias=categorias,
        texto_busqueda=texto_busqueda,
        categoria_filtro=categoria_filtro
    )



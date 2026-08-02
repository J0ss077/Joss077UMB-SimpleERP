"""
ERP - Tienda de Tecnologia
Fabrica de aplicacion Flask (Application Factory Pattern).

Este patron permite crear la aplicacion en tiempo de ejecucion,
facilitando pruebas, configuracion multiple y extension futura.
"""

from flask import Flask, session
from flask_login import LoginManager

from app.config import Config
from app.models import db, Usuario


# Instancia global de Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor inicia sesion para acceder a esta pagina.'


@login_manager.user_loader
def load_user(user_id):
    """
    Callback de Flask-Login: carga un usuario desde la BD
    dado su identificador. Se invoca en cada request autenticado.
    """
    return Usuario.query.get(int(user_id))


def create_app(config_class=Config):
    """
    Fabrica de la aplicacion Flask.

    Pasos:
        1. Crear instancia Flask
        2. Cargar configuracion
        3. Inicializar extensiones (BD, Login)
        4. Registrar blueprints (modulos)
        5. Crear tablas si no existen
        6. Retornar app lista para ejecutar
    """
    # 1. Instancia Flask
    app = Flask(__name__)

    # 2. Cargar configuracion desde clase Config
    app.config.from_object(config_class)

    # 3. Inicializar extensiones
    db.init_app(app)
    login_manager.init_app(app)

    # 4. Registrar blueprints (modulos de la aplicacion)
    _registrar_blueprints(app)

    # 5. Crear tablas en la BD si no existen
    with app.app_context():
        db.create_all()

    # 6. Datos globales para todas las plantillas (carrito y favoritos)
    @app.context_processor
    def _contexto_global():
        return {
            'carrito_cantidad': sum(session.get('carrito', {}).values()),
            'favoritos_ids': set(session.get('favoritos', [])),
        }

    return app


def _registrar_blueprints(app):
    """
    Registra todos los blueprints (modulos) en la aplicacion.

    Cada blueprint representa un modulo funcional del ERP:
        - main:      Catalogo publico y pagina principal
        - auth:      Autenticacion (login, registro)
        - products:  Gestion de productos e inventario
        - invoices:  Facturacion y transacciones
        - reports:   Reportes administrativos
    """
    from app.main import main_bp
    from app.auth import auth_bp
    from app.products import products_bp
    from app.invoices import invoices_bp
    from app.reports import reports_bp
    from app.tienda import tienda_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(invoices_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(tienda_bp)

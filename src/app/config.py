"""
ERP - Tienda de Tecnologia
Configuracion centralizada de la aplicacion Flask.

Toda la configuracion se lee desde variables de entorno,
con valores por defecto para desarrollo local.
"""

import os


class Config:
    """Clase de configuracion principal."""

    # Clave secreta para sesiones y cookies
    SECRET_KEY = os.environ.get('SECRET_KEY', 'erp-clave-secreta-desarrollo')

    # URL de conexion a PostgreSQL
    # - En Docker: postgresql://erp_user:erp_password@db:5432/erp_db
    # - En local:  postgresql://erp_user:erp_password@localhost:5432/erp_db
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'postgresql://erp_user:erp_password@localhost:5432/erp_db'
    )

    # Desactivar seguimiento de modificaciones de SQLAlchemy (ahorra memoria)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Carpeta de imagenes subidas de los productos
    UPLOAD_FOLDER = os.environ.get(
        'UPLOAD_FOLDER',
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    )

    # Tamano maximo de archivo permitido (5 MB)
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

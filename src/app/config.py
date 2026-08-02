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

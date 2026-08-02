"""
ERP - Tienda de Tecnologia
Utilidades compartidas entre blueprints.
"""

import os
import uuid

from flask import current_app
from werkzeug.utils import secure_filename

# Extensiones de imagen permitidas en la subida
EXTENSIONES_PERMITIDAS = {'png', 'jpg', 'jpeg', 'webp', 'gif', 'svg'}


def guardar_imagen(archivo, prefijo='archivo'):
    """
    Valida y guarda una imagen en la carpeta de uploads.

    Devuelve el nombre del archivo guardado, o None si no se subio nada.
    Levanta ValueError si el archivo no es una imagen permitida.
    """
    if not archivo or not archivo.filename:
        return None

    extension = archivo.filename.rsplit('.', 1)[-1].lower() if '.' in archivo.filename else ''
    if extension not in EXTENSIONES_PERMITIDAS:
        raise ValueError('Formato de imagen no permitido. Usa PNG, JPG, JPEG, WEBP, GIF o SVG.')

    nombre_base = secure_filename(archivo.filename.rsplit('.', 1)[0])[:40] or prefijo
    nombre_archivo = f'{prefijo}-{uuid.uuid4().hex[:8]}-{nombre_base}.{extension}'

    carpeta = current_app.config['UPLOAD_FOLDER']
    os.makedirs(carpeta, exist_ok=True)
    archivo.save(os.path.join(carpeta, nombre_archivo))
    return nombre_archivo


def eliminar_imagen(nombre_archivo):
    """Elimina el archivo de imagen si existe en la carpeta de uploads."""
    if not nombre_archivo:
        return
    ruta = os.path.join(current_app.config['UPLOAD_FOLDER'], nombre_archivo)
    if os.path.isfile(ruta):
        os.remove(ruta)

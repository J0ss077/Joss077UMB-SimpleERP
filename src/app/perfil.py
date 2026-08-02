"""
ERP - Tienda de Tecnologia
Blueprint: Perfil de usuario (perfil).

Permite a cualquier usuario autenticado administrar su propia cuenta:
    - Datos personales (nombre, telefono, foto de perfil)
    - Datos de envio (direccion, ciudad)
    - Preferencias (tema claro/oscuro, newsletter)
    - Cambio de contrasena (con verificacion de la actual)
    - Resumen de actividad (facturas, total gastado, favoritos, ultimos pedidos)

Rutas (requieren autenticacion):
    GET/POST /perfil            -> Ver y editar perfil
    POST     /perfil/contrasena -> Cambiar contrasena
    POST     /perfil/tema       -> Guardar preferencia de tema (AJAX)
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from app.models import db, Factura, CarritoItem, Favorito
from app.utils import guardar_imagen, eliminar_imagen

perfil_bp = Blueprint('perfil', __name__, url_prefix='/perfil')

TEMAS_VALIDOS = {'auto', 'light', 'dark'}


# ---------------------------------------------------------------------------
# VER Y EDITAR PERFIL
# ---------------------------------------------------------------------------
@perfil_bp.route('/', methods=['GET', 'POST'])
@login_required
def ver():
    """
    GET:  Muestra el perfil con resumen de actividad e historial de pedidos.
    POST: Actualiza datos personales, datos de envio y preferencias.
    """
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        telefono = request.form.get('telefono', '').strip()
        direccion = request.form.get('direccion', '').strip()
        ciudad = request.form.get('ciudad', '').strip()
        tema = request.form.get('tema', 'auto')
        newsletter = request.form.get('newsletter') == '1'
        quitar_foto = request.form.get('quitar_foto') == '1'

        errores = []

        if not nombre:
            errores.append('El nombre es obligatorio.')
        elif len(nombre) > 100:
            errores.append('El nombre no puede superar los 100 caracteres.')

        if len(telefono) > 20:
            errores.append('El telefono no puede superar los 20 caracteres.')

        if len(ciudad) > 100:
            errores.append('La ciudad no puede superar los 100 caracteres.')

        if tema not in TEMAS_VALIDOS:
            errores.append('Tema de interfaz no valido.')

        nueva_foto = None
        if request.files.get('imagen') and request.files['imagen'].filename:
            try:
                nueva_foto = guardar_imagen(request.files['imagen'], prefijo='usuario')
            except ValueError as e:
                errores.append(str(e))

        if errores:
            for error in errores:
                flash(error, 'error')
            return redirect(url_for('perfil.ver'))

        # Aplicar cambios
        current_user.nombre = nombre
        current_user.telefono = telefono or None
        current_user.direccion = direccion or None
        current_user.ciudad = ciudad or None
        current_user.tema_preferido = tema
        current_user.newsletter = newsletter

        # Manejar foto de perfil: reemplazar, mantener o quitar
        if nueva_foto:
            eliminar_imagen(current_user.imagen)
            current_user.imagen = nueva_foto
        elif quitar_foto:
            eliminar_imagen(current_user.imagen)
            current_user.imagen = None

        db.session.commit()

        flash('Perfil actualizado exitosamente.', 'success')
        return redirect(url_for('perfil.ver'))

    return render_template('perfil.html', **_resumen_actividad())


# ---------------------------------------------------------------------------
# CAMBIAR CONTRASENA
# ---------------------------------------------------------------------------
@perfil_bp.route('/contrasena', methods=['POST'])
@login_required
def cambiar_contrasena():
    """
    Cambia la contrasena del usuario verificando primero la actual.
    """
    contrasena_actual = request.form.get('contrasena_actual', '')
    nueva = request.form.get('nueva_contrasena', '')
    confirmacion = request.form.get('confirmar_contrasena', '')

    errores = []

    if not current_user.check_password(contrasena_actual):
        errores.append('La contrasena actual no es correcta.')

    if len(nueva) < 4:
        errores.append('La nueva contrasena debe tener al menos 4 caracteres.')

    if nueva != confirmacion:
        errores.append('Las contrasenas no coinciden.')

    if errores:
        for error in errores:
            flash(error, 'error')
        return redirect(url_for('perfil.ver'))

    current_user.set_password(nueva)
    db.session.commit()

    flash('Contrasena actualizada exitosamente.', 'success')
    return redirect(url_for('perfil.ver'))


# ---------------------------------------------------------------------------
# GUARDAR PREFERENCIA DE TEMA (AJAX)
# ---------------------------------------------------------------------------
@perfil_bp.route('/tema', methods=['POST'])
@login_required
def guardar_tema():
    """
    Sincroniza el tema claro/oscuro elegido en el perfil del usuario.
    Se invoca via fetch desde el boton de tema en la navbar.
    """
    tema = request.form.get('tema', '')
    if tema not in TEMAS_VALIDOS:
        return jsonify({'ok': False, 'error': 'Tema no valido'}), 400

    current_user.tema_preferido = tema
    db.session.commit()
    return jsonify({'ok': True})


# ---------------------------------------------------------------------------
# Helper: resumen de actividad del usuario
# ---------------------------------------------------------------------------
def _resumen_actividad():
    """
    Calcula datos resumidos para mostrar en el perfil:
    facturas totales, total gastado, ultimos pedidos, favoritos y carrito.
    """
    facturas = (
        Factura.query
        .filter_by(id_usuario=current_user.id_usuario)
        .order_by(Factura.fecha.desc())
        .all()
    )

    facturas_activas = [f for f in facturas if not f.esta_anulada()]
    total_gastado = sum(f.get_total() for f in facturas_activas)

    carrito_count = db.session.query(
        db.func.coalesce(db.func.sum(CarritoItem.cantidad), 0)
    ).filter_by(id_usuario=current_user.id_usuario).scalar() or 0
    favoritos_count = Favorito.query.filter_by(
        id_usuario=current_user.id_usuario
    ).count()

    return {
        'total_facturas': len(facturas),
        'total_activas': len(facturas_activas),
        'total_gastado': total_gastado,
        'ultimas_facturas': facturas[:5],
        'favoritos_count': favoritos_count,
        'carrito_count': carrito_count,
    }

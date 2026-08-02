"""
ERP - Tienda de Tecnologia
Blueprint: Gestion de Usuarios (usuarios).

Administracion de cuentas del sistema, exclusivo para el rol admin:
    - Listado de usuarios con filtro por rol.
    - Creacion de cuentas con rol asignado.
    - Cambio de rol.
    - Reseteo de contrasena.
    - Bloqueo/desbloqueo de cuentas.

Rutas (solo admin):
    GET  /usuarios                     -> Listar usuarios
    GET  /usuarios/crear               -> Formulario de creacion
    POST /usuarios/crear               -> Crear usuario
    POST /usuarios/<id>/rol            -> Cambiar rol
    POST /usuarios/<id>/password       -> Resetear contrasena
    POST /usuarios/<id>/bloquear       -> Bloquear/desbloquear cuenta
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.models import db, Usuario

usuarios_bp = Blueprint('usuarios', __name__, url_prefix='/usuarios')


def _exigir_admin():
    """Devuelve True si el usuario actual es admin (acceso permitido)."""
    return current_user.es_admin()


# ---------------------------------------------------------------------------
# LISTADO DE USUARIOS
# ---------------------------------------------------------------------------
@usuarios_bp.route('/')
@login_required
def listar():
    """Lista todos los usuarios, con filtro opcional por rol (admin)."""
    if not _exigir_admin():
        flash('Solo el administrador puede gestionar usuarios.', 'error')
        return redirect(url_for('main.index'))

    rol = request.args.get('rol', '').strip()
    consulta = Usuario.query
    if rol in ('admin', 'vendedor', 'cliente'):
        consulta = consulta.filter_by(rol=rol)

    usuarios = consulta.order_by(Usuario.rol, Usuario.nombre).all()

    conteo = {
        'total': Usuario.query.count(),
        'admin': Usuario.query.filter_by(rol='admin').count(),
        'vendedor': Usuario.query.filter_by(rol='vendedor').count(),
        'cliente': Usuario.query.filter_by(rol='cliente').count(),
    }
    return render_template(
        'usuarios/list.html',
        usuarios=usuarios,
        conteo=conteo,
        rol_filtro=rol
    )


# ---------------------------------------------------------------------------
# CREAR USUARIO
# ---------------------------------------------------------------------------
@usuarios_bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear():
    """Crea un usuario con rol especifico (admin)."""
    if not _exigir_admin():
        flash('Solo el administrador puede gestionar usuarios.', 'error')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        rol = request.form.get('rol', 'cliente').strip()

        errores = []
        if not nombre or not email or not password:
            errores.append('Todos los campos son obligatorios.')
        if len(password) < 4:
            errores.append('La contrasena debe tener al menos 4 caracteres.')
        if rol not in ('admin', 'vendedor', 'cliente'):
            errores.append('Rol invalido.')
        if Usuario.query.filter_by(email=email).first():
            errores.append('Este email ya esta registrado.')

        if errores:
            for error in errores:
                flash(error, 'error')
            return render_template(
                'usuarios/create.html',
                nombre=nombre, email=email, rol=rol
            )

        usuario = Usuario(nombre=nombre, email=email, rol=rol)
        usuario.set_password(password)
        db.session.add(usuario)
        db.session.commit()
        flash(f'Usuario "{nombre}" creado con rol {rol}.', 'success')
        return redirect(url_for('usuarios.listar'))

    return render_template('usuarios/create.html')


# ---------------------------------------------------------------------------
# CAMBIAR ROL
# ---------------------------------------------------------------------------
@usuarios_bp.route('/<int:usuario_id>/rol', methods=['POST'])
@login_required
def cambiar_rol(usuario_id):
    """Cambia el rol de un usuario (admin)."""
    if not _exigir_admin():
        flash('Solo el administrador puede gestionar usuarios.', 'error')
        return redirect(url_for('main.index'))

    usuario = Usuario.query.get_or_404(usuario_id)
    nuevo_rol = request.form.get('rol', '').strip()

    if nuevo_rol not in ('admin', 'vendedor', 'cliente'):
        flash('Rol invalido.', 'error')
        return redirect(url_for('usuarios.listar'))

    # Evitar que un admin se quite el rol a si mismo y deje el sistema sin admins
    if usuario.id_usuario == current_user.id_usuario and nuevo_rol != 'admin':
        flash('No puedes cambiarte el rol a ti mismo.', 'error')
        return redirect(url_for('usuarios.listar'))

    usuario.rol = nuevo_rol
    db.session.commit()
    flash(f'Rol de "{usuario.nombre}" actualizado a {nuevo_rol}.', 'success')
    return redirect(url_for('usuarios.listar'))


# ---------------------------------------------------------------------------
# RESETEAR CONTRASENA
# ---------------------------------------------------------------------------
@usuarios_bp.route('/<int:usuario_id>/password', methods=['POST'])
@login_required
def resetear_password(usuario_id):
    """Resetea la contrasena de un usuario (admin)."""
    if not _exigir_admin():
        flash('Solo el administrador puede gestionar usuarios.', 'error')
        return redirect(url_for('main.index'))

    usuario = Usuario.query.get_or_404(usuario_id)
    password = request.form.get('password', '')

    if len(password) < 4:
        flash('La contrasena debe tener al menos 4 caracteres.', 'error')
        return redirect(url_for('usuarios.listar'))

    usuario.set_password(password)
    db.session.commit()
    flash(f'Contrasena de "{usuario.nombre}" actualizada.', 'success')
    return redirect(url_for('usuarios.listar'))


# ---------------------------------------------------------------------------
# BLOQUEAR / DESBLOQUEAR CUENTA
# ---------------------------------------------------------------------------
@usuarios_bp.route('/<int:usuario_id>/bloquear', methods=['POST'])
@login_required
def bloquear(usuario_id):
    """Bloquea o desbloquea la cuenta de un usuario (admin)."""
    if not _exigir_admin():
        flash('Solo el administrador puede gestionar usuarios.', 'error')
        return redirect(url_for('main.index'))

    usuario = Usuario.query.get_or_404(usuario_id)

    if usuario.id_usuario == current_user.id_usuario:
        flash('No puedes bloquear tu propia cuenta.', 'error')
        return redirect(url_for('usuarios.listar'))

    if not usuario.activo:
        usuario.activo = True
        flash(f'Cuenta de "{usuario.nombre}" desbloqueada.', 'success')
    else:
        usuario.activo = False
        flash(f'Cuenta de "{usuario.nombre}" bloqueada.', 'warning')

    db.session.commit()
    return redirect(url_for('usuarios.listar'))

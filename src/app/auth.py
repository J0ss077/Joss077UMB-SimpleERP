"""
ERP - Tienda de Tecnologia
Blueprint: Autenticacion (auth).

Maneja el registro e inicio de sesion de usuarios.
    RF01: Login obligatorio para acceder a modulos internos.
    RF02: Registro de nuevos usuarios con rol asignado.

Rutas:
    GET/POST /auth/login     -> Iniciar sesion
    GET/POST /auth/register  -> Registrar nuevo usuario
    GET      /auth/logout    -> Cerrar sesion
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, Usuario

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


# ---------------------------------------------------------------------------
# LOGIN - RF01
# ---------------------------------------------------------------------------
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Inicio de sesion de usuario.

    GET:  Muestra el formulario de login.
    POST: Valida credenciales e inicia sesion.
          - Si son correctas: redirige al catalogo.
          - Si son incorrectas: muestra mensaje de error.
    """
    # Si el usuario ya esta autenticado, redirigir al inicio
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        # Validar que los campos no esten vacios
        if not email or not password:
            flash('Por favor completa todos los campos.', 'error')
            return render_template('login.html')

        # Buscar usuario por email
        usuario = Usuario.query.filter_by(email=email).first()

        # Verificar credenciales
        if usuario is None or not usuario.check_password(password):
            flash('Email o contrasena incorrectos.', 'error')
            return render_template('login.html')

        # Iniciar sesion (Flask-Login crea la cookie de sesion)
        login_user(usuario)
        flash(f'Bienvenido/a, {usuario.nombre}!', 'success')
        return redirect(url_for('main.index'))

    return render_template('login.html')


# ---------------------------------------------------------------------------
# REGISTRO - RF02
# ---------------------------------------------------------------------------
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Registro de nuevo usuario en el sistema.

    GET:  Muestra el formulario de registro.
    POST: Crea el usuario con los datos proporcionados.
          - Por seguridad, el rol por defecto es 'cliente'.
          - Solo un admin puede asignar otros roles posteriormente.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')

        # --- Validaciones basicas ---
        errores = []

        if not nombre or not email or not password:
            errores.append('Todos los campos son obligatorios.')

        if password != password_confirm:
            errores.append('Las contrasenas no coinciden.')

        if len(password) < 4:
            errores.append('La contrasena debe tener al menos 4 caracteres.')

        # Verificar si el email ya esta registrado
        if Usuario.query.filter_by(email=email).first():
            errores.append('Este email ya esta registrado.')

        if errores:
            for error in errores:
                flash(error, 'error')
            return render_template('register.html')

        # --- Crear usuario ---
        # Por defecto se asigna rol 'cliente' (principio de minimo privilegio)
        nuevo_usuario = Usuario(
            nombre=nombre,
            email=email,
            rol='cliente'
        )
        nuevo_usuario.set_password(password)  # Aplica hash seguro (RNF03)

        db.session.add(nuevo_usuario)
        db.session.commit()

        flash('Registro exitoso. Ahora puedes iniciar sesion.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')


# ---------------------------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------------------------
@auth_bp.route('/logout')
@login_required
def logout():
    """Cierra la sesion del usuario actual."""
    logout_user()
    flash('Has cerrado sesion.', 'info')
    return redirect(url_for('main.index'))

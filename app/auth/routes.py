from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.auth import auth_bp
from app.models import User


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        error = None
        if not username or not email or not password:
            error = 'Todos los campos son obligatorios.'
        elif len(password) < 8:
            error = 'La contraseña debe tener al menos 8 caracteres.'
        elif password != confirm:
            error = 'Las contraseñas no coinciden.'
        elif User.query.filter_by(username=username).first():
            error = 'Ese nombre de usuario ya está en uso.'
        elif User.query.filter_by(email=email).first():
            error = 'Ya existe una cuenta con ese correo electrónico.'

        if error:
            flash(error, 'error')
            return render_template('auth/register.html', username=username, email=email)

        user = User(username=username, email=email, role='scouter')
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('¡Cuenta creada! Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash('Correo o contraseña incorrectos.', 'error')
            return render_template('auth/login.html', email=email)

        login_user(user, remember=remember)
        next_page = request.args.get('next')
        return redirect(next_page or url_for('main.index'))

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión correctamente.', 'success')
    return redirect(url_for('main.index'))

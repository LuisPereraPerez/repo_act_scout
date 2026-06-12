from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app import db
from app.main import main_bp
from app.models import Activity, Unit, Category


@main_bp.route('/')
def index():
    keyword = request.args.get('q', '').strip()
    unit_slug = request.args.get('unit', '').strip()
    category_slug = request.args.get('category', '').strip()
    environment = request.args.get('environment', '').strip()
    duration = request.args.get('duration', '').strip()

    query = Activity.query.filter_by(status='approved')

    if keyword:
        search = f'%{keyword}%'
        query = query.filter(
            db.or_(
                Activity.title.ilike(search),
                Activity.description.ilike(search)
            )
        )

    if unit_slug:
        query = query.join(Activity.units).filter(Unit.slug == unit_slug)

    if category_slug:
        query = query.join(Activity.categories).filter(Category.slug == category_slug)

    if environment:
        query = query.filter(Activity.environment == environment)

    if duration:
        query = query.filter(Activity.duration_range == duration)

    activities = query.order_by(Activity.created_at.desc()).all()
    units = Unit.query.order_by(Unit.name).all()
    categories = Category.query.order_by(Category.name).all()

    filters = {
        'q': keyword,
        'unit': unit_slug,
        'category': category_slug,
        'environment': environment,
        'duration': duration,
    }

    return render_template('main/index.html',
                           activities=activities,
                           units=units,
                           categories=categories,
                           filters=filters)


@main_bp.route('/actividad/<int:activity_id>')
def activity_detail(activity_id):
    activity = Activity.query.get_or_404(activity_id)

    if activity.status != 'approved':
        if not current_user.is_authenticated or (
            not current_user.is_admin() and current_user.id != activity.user_id
        ):
            abort(404)

    return render_template('main/activity_detail.html', activity=activity)


@main_bp.route('/subir', methods=['GET', 'POST'])
@login_required
def upload_activity():
    units = Unit.query.order_by(Unit.name).all()
    categories = Category.query.order_by(Category.name).all()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        objectives = request.form.get('objectives', '').strip()
        materials = request.form.get('materials', '').strip()
        environment = request.form.get('environment', '').strip()
        duration_range = request.form.get('duration_range', '').strip()
        unit_ids = request.form.getlist('units')
        category_ids = request.form.getlist('categories')

        error = None
        if not title:
            error = 'El título es obligatorio.'
        elif not description:
            error = 'La descripción es obligatoria.'
        elif not objectives:
            error = 'Los objetivos son obligatorios.'
        elif environment not in ('interior', 'exterior', 'indiferente'):
            error = 'Entorno no válido.'
        elif duration_range not in ('<30 min', '30-60 min', '+60 min'):
            error = 'Duración no válida.'
        elif not unit_ids:
            error = 'Selecciona al menos una sección.'
        elif not category_ids:
            error = 'Selecciona al menos una categoría.'

        if error:
            flash(error, 'error')
            return render_template('main/upload.html', units=units, categories=categories,
                                   form_data=request.form)

        selected_units = Unit.query.filter(Unit.id.in_(unit_ids)).all()
        selected_categories = Category.query.filter(Category.id.in_(category_ids)).all()

        activity = Activity(
            title=title,
            description=description,
            objectives=objectives,
            materials=materials,
            environment=environment,
            duration_range=duration_range,
            status='pending',
            user_id=current_user.id,
            units=selected_units,
            categories=selected_categories,
        )
        db.session.add(activity)
        db.session.commit()

        flash('¡Actividad enviada! Será revisada por un administrador antes de publicarse.', 'success')
        return redirect(url_for('main.index'))

    return render_template('main/upload.html', units=units, categories=categories, form_data={})

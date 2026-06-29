import os
import uuid
from flask import render_template, request, redirect, url_for, flash, abort, current_app, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db, allowed_file
from app.main import main_bp
from app.models import Activity, Unit, Category

ENVIRONMENTS = {
    'interior':          '🏠 Interior',
    'exterior':          '🌲 Exterior',
    'indiferente':       '↔️ Indiferente',
    'piscina':           '🏊 Piscina',
    'acampada':          '⛺ Acampada',
    'actividad_acuatica':'🏄 Actividad acuática',
    'montana':           '🏔️ Montaña',
    'entorno_urbano':    '🏙️ Entorno urbano',
}

ENVIRONMENTS_LIST = [(k, v) for k, v in ENVIRONMENTS.items()]

DURATIONS = [
    ('less_30m',      '⚡ Menos de 30 min'),
    ('30_60m',        '⏱ 30-60 min'),
    ('1_2h',          '🕐 1-2 h'),
    ('2_4h',          '🕑 2-4 h'),
    ('more_4h',       '🕓 +4 h'),
    ('multiple_days', '📅 Varios días'),
]

DURATIONS_DISPLAY = {
    'less_30m':      'Menos de 30 min',
    '30_60m':        '30-60 min',
    '1_2h':          '1-2 h',
    '2_4h':          '2-4 h',
    'more_4h':       '+4 h',
    'multiple_days': 'Varios días',
}


@main_bp.route('/')
def index():
    keyword      = request.args.get('q', '').strip()
    unit_slug    = request.args.get('unit', '').strip()
    cat_slug     = request.args.get('category', '').strip()
    duration     = request.args.get('duration', '').strip()
    has_file     = request.args.get('has_file', '').strip()
    part_min = request.args.get('part_min', '').strip()
    part_max = request.args.get('part_max', '').strip()
    entorno = request.args.get('entorno', '').strip()

    query = Activity.query.filter_by(status='approved')

    if keyword:
        s = f'%{keyword}%'
        query = query.filter(db.or_(
            Activity.title.ilike(s),
            Activity.description.ilike(s),
            Activity.objectives.ilike(s),
        ))

    if unit_slug:
        query = query.join(Activity.units).filter(Unit.slug == unit_slug)

    if cat_slug:
        query = query.join(Activity.categories).filter(Category.slug == cat_slug)
    
    if duration and duration in [d[0] for d in DURATIONS]:
        query = query.filter(Activity.duration_range == duration)
    
    if part_min and part_min.isdigit():
        query = query.filter(
            db.or_(Activity.max_participants.is_(None), Activity.max_participants >= int(part_min))
        )
    if part_max and part_max.isdigit():
        query = query.filter(
            db.or_(Activity.min_participants.is_(None), Activity.min_participants <= int(part_max))
        )
        
    if entorno and entorno in ENVIRONMENTS:
        query = query.filter(Activity.environment == entorno)

    if has_file == '1':
        query = query.filter(Activity.attachment_filename.isnot(None))

    activities = query.order_by(Activity.created_at.desc()).all()
    units      = Unit.query.order_by(Unit.order).all()
    categories = Category.query.order_by(Category.name).all()
    
    filters = dict(q=keyword, unit=unit_slug, category=cat_slug,
               entorno=entorno, duration=duration,
               has_file=has_file,
               part_min=part_min, part_max=part_max)

    return render_template('main/index.html',
                       activities=activities, units=units,
                       categories=categories, filters=filters,
                       environments=ENVIRONMENTS,
                       environments_list=ENVIRONMENTS_LIST,
                       durations=DURATIONS,
                       durations_display=DURATIONS_DISPLAY)


@main_bp.route('/actividad/<int:activity_id>')
def activity_detail(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    if activity.status != 'approved':
        if not current_user.is_authenticated or (
            not current_user.is_admin() and current_user.id != activity.user_id
        ):
            abort(404)
    return render_template('main/activity_detail.html',
                       activity=activity,
                       environments=ENVIRONMENTS,
                       durations_display=DURATIONS_DISPLAY)


@main_bp.route('/actividad/<int:activity_id>/descargar')
def download_attachment(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    if activity.status != 'approved':
        if not current_user.is_authenticated or (
            not current_user.is_admin() and current_user.id != activity.user_id
        ):
            abort(404)
    if not activity.attachment_filename:
        abort(404)
    return send_from_directory(
        current_app.config['UPLOAD_FOLDER'],
        activity.attachment_filename,
        as_attachment=True,
        download_name=activity.attachment_original_name,
    )


@main_bp.route('/subir', methods=['GET', 'POST'])
@login_required
def upload_activity():
    units      = Unit.query.order_by(Unit.order).all()
    categories = Category.query.order_by(Category.name).all()

    if request.method == 'POST':
        title          = request.form.get('title', '').strip()
        description    = request.form.get('description', '').strip()
        objectives     = request.form.get('objectives', '').strip()
        materials      = request.form.get('materials', '').strip()
        environment    = request.form.get('environment', '').strip()
        location_detail = request.form.get('location_detail', '').strip()
        duration_range = request.form.get('duration_range', '').strip()
        unit_ids       = request.form.getlist('units')
        category_ids   = request.form.getlist('categories')

        try:
            min_p   = int(request.form.get('min_participants', '')) if request.form.get('min_participants') else None
            max_p   = int(request.form.get('max_participants', '')) if request.form.get('max_participants') else None
        except ValueError:
            flash('Los valores numéricos no son válidos.', 'error')
            return render_template('main/upload.html', units=units, categories=categories,
                                form_data=request.form, environments=ENVIRONMENTS,
                                durations=DURATIONS, durations_display=DURATIONS_DISPLAY)

        error = None
        if not title:
            error = 'El título es obligatorio.'
        elif not description:
            error = 'La descripción es obligatoria.'
        elif not objectives:
            error = 'Los objetivos son obligatorios.'
        elif environment not in ENVIRONMENTS:
            error = 'Entorno no válido.'
        elif duration_range not in [d[0] for d in DURATIONS]:
            error = 'Duración no válida.'
        elif not unit_ids:
            error = 'Selecciona al menos una sección.'
        elif not category_ids:
            error = 'Selecciona al menos una categoría.'

        if error:
            flash(error, 'error')
            return render_template('main/upload.html', units=units, categories=categories,
                       form_data=request.form, environments=ENVIRONMENTS,
                       durations=DURATIONS, durations_display=DURATIONS_DISPLAY)

        saved_filename = None
        original_name  = None
        mime_type      = None

        uploaded_file = request.files.get('attachment')
        if uploaded_file and uploaded_file.filename:
            if not allowed_file(uploaded_file.filename):
                flash('Tipo de archivo no permitido. Sube PDF, Word, imagen, etc.', 'error')
                return render_template('main/upload.html', units=units, categories=categories,
                       form_data=request.form, environments=ENVIRONMENTS,
                       durations=DURATIONS, durations_display=DURATIONS_DISPLAY)

            original_name  = secure_filename(uploaded_file.filename)
            ext            = original_name.rsplit('.', 1)[1].lower()
            saved_filename = f"{uuid.uuid4().hex}.{ext}"
            mime_type      = uploaded_file.content_type
            upload_path    = os.path.join(current_app.config['UPLOAD_FOLDER'], saved_filename)
            uploaded_file.save(upload_path)

        selected_units      = Unit.query.filter(Unit.id.in_(unit_ids)).all()
        selected_categories = Category.query.filter(Category.id.in_(category_ids)).all()

        activity = Activity(
            title=title,
            description=description,
            objectives=objectives,
            materials=materials,
            environment=environment,
            location_detail=location_detail or None,
            duration_range=duration_range,
            min_participants=min_p,
            max_participants=max_p,
            attachment_filename=saved_filename,
            attachment_original_name=original_name,
            attachment_mime=mime_type,
            status='pending',
            user_id=current_user.id,
            units=selected_units,
            categories=selected_categories,
        )
        db.session.add(activity)
        db.session.commit()

        flash('¡Actividad enviada! Será revisada antes de publicarse.', 'success')
        return redirect(url_for('main.index'))

    return render_template('main/upload.html', units=units, categories=categories,
                       form_data=request.form, environments=ENVIRONMENTS,
                       durations=DURATIONS, durations_display=DURATIONS_DISPLAY)
    
@main_bp.route('/actividad/<int:activity_id>/borrar', methods=['POST'])
@login_required
def delete_activity(activity_id):
    activity = Activity.query.get_or_404(activity_id)

    if current_user.id != activity.user_id and current_user.role != 'admin':
        abort(403)

    is_admin = current_user.role == 'admin'
    db.session.delete(activity)
    db.session.commit()

    flash('La actividad ha sido eliminada correctamente.', 'success')

    if is_admin:
        return redirect(url_for('admin.panel'))
    return redirect(url_for('community.profile', username=current_user.username))

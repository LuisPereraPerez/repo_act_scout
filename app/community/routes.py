from flask import render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import login_required, current_user
from app import db
from app.community import community_bp
from app.models import User, Activity, CustomList, activity_likes


@community_bp.route('/perfil/<username>')
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    tab  = request.args.get('tab', 'actividades')

    uploaded = (
        user.activities
        .filter_by(status='approved')
        .order_by(Activity.created_at.desc())
        .all()
    )
    pending_count = (
        user.activities.filter_by(status='pending').count()
        if current_user.is_authenticated and (current_user.id == user.id or current_user.is_admin())
        else 0
    )

    liked = (
        user.liked_activities
        .filter_by(status='approved')
        .order_by(Activity.created_at.desc())
        .all()
    )

    lists_query = user.custom_lists
    if not (current_user.is_authenticated and current_user.id == user.id):
        lists_query = lists_query.filter_by(is_public=True)
    custom_lists = lists_query.order_by(CustomList.created_at.desc()).all()

    is_own = current_user.is_authenticated and current_user.id == user.id

    return render_template(
        'community/profile.html',
        profile_user=user,
        tab=tab,
        uploaded=uploaded,
        pending_count=pending_count,
        liked=liked,
        custom_lists=custom_lists,
        is_own=is_own,
    )


@community_bp.route('/perfil/<username>/editar', methods=['GET', 'POST'])
@login_required
def edit_profile(username):
    if current_user.username != username:
        abort(403)

    if request.method == 'POST':
        grupo = request.form.get('grupo_scout', '').strip()

        social = {}
        for network in ('instagram', 'tiktok', 'x'):
            value = request.form.get(network, '').strip().lstrip('@')
            if value:
                social[network] = value

        current_user.grupo_scout = grupo or None
        current_user.social_media = social if social else None
        db.session.commit()
        flash('Perfil actualizado correctamente.', 'success')
        return redirect(url_for('community.profile', username=current_user.username))

    return render_template('community/edit_profile.html', user=current_user)


@community_bp.route('/like/<int:activity_id>', methods=['POST'])
@login_required
def toggle_like(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    if activity.status != 'approved':
        abort(404)

    if current_user.has_liked(activity):
        current_user.liked_activities.remove(activity)
        liked = False
    else:
        current_user.liked_activities.append(activity)
        liked = True

    db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(liked=liked, count=activity.likes_count)

    next_url = request.form.get('next') or url_for('main.activity_detail', activity_id=activity_id)
    return redirect(next_url)


@community_bp.route('/listas/crear', methods=['POST'])
@login_required
def create_list():
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    is_public = request.form.get('is_public') == '1'

    if not name:
        flash('El nombre de la lista es obligatorio.', 'error')
        return redirect(url_for('community.profile', username=current_user.username, tab='listas'))

    new_list = CustomList(
        name=name,
        description=description or None,
        is_public=is_public,
        user_id=current_user.id,
    )
    db.session.add(new_list)
    db.session.commit()
    flash(f'Lista «{name}» creada correctamente.', 'success')
    return redirect(url_for('community.profile', username=current_user.username, tab='listas'))


@community_bp.route('/listas/<int:list_id>/eliminar', methods=['POST'])
@login_required
def delete_list(list_id):
    custom_list = CustomList.query.get_or_404(list_id)
    if custom_list.user_id != current_user.id:
        abort(403)
    db.session.delete(custom_list)
    db.session.commit()
    flash('Lista eliminada.', 'success')
    return redirect(url_for('community.profile', username=current_user.username, tab='listas'))


@community_bp.route('/listas/<int:list_id>/agregar', methods=['POST'])
@login_required
def add_to_list(list_id):
    custom_list = CustomList.query.get_or_404(list_id)
    if custom_list.user_id != current_user.id:
        abort(403)
    activity_id = request.form.get('activity_id', type=int)
    activity = Activity.query.get_or_404(activity_id)

    if activity not in custom_list.activities:
        custom_list.activities.append(activity)
        db.session.commit()
        flash(f'«{activity.title}» añadida a «{custom_list.name}».', 'success')
    else:
        flash('Esa actividad ya está en la lista.', 'warning')

    return redirect(request.form.get('next') or url_for('main.activity_detail', activity_id=activity_id))


@community_bp.route('/listas/<int:list_id>')
def view_list(list_id):
    custom_list = CustomList.query.get_or_404(list_id)
    if not custom_list.is_public:
        if not current_user.is_authenticated or current_user.id != custom_list.user_id:
            abort(404)
    activities = custom_list.activities.filter_by(status='approved').all()
    return render_template('community/list_detail.html', custom_list=custom_list, activities=activities)

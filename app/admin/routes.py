from functools import wraps
from flask import render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user
from app import db
from app.admin import admin_bp
from app.models import Activity, User


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/')
@login_required
@admin_required
def panel():
    pending = Activity.query.filter_by(status='pending').order_by(Activity.created_at.asc()).all()
    approved_count = Activity.query.filter_by(status='approved').count()
    users_count = User.query.filter_by(role='scouter').count()
    return render_template('admin/panel.html',
                           pending=pending,
                           approved_count=approved_count,
                           users_count=users_count)


@admin_bp.route('/aprobar/<int:activity_id>', methods=['POST'])
@login_required
@admin_required
def approve_activity(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    activity.status = 'approved'
    db.session.commit()
    flash(f'«{activity.title}» ha sido aprobada y ya es pública.', 'success')
    return redirect(url_for('admin.panel'))


@admin_bp.route('/rechazar/<int:activity_id>', methods=['POST'])
@login_required
@admin_required
def reject_activity(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    db.session.delete(activity)
    db.session.commit()
    flash(f'La actividad ha sido rechazada y eliminada.', 'success')
    return redirect(url_for('admin.panel'))

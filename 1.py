from app import create_app, db
from app.models import Activity

app = create_app()
migration_map = {
    '<30 min':   'menos de 30m',
    '30-60 min': '30-60m',
    '+60 min':   'more_4h',
    '1-2 h':     '1-2h',
    '2-4 h':     '2-4h',
    '+4 h':      'más de 4h',
    'Varios días': 'varios días',
}

with app.app_context():
    for old, new in migration_map.items():
        Activity.query.filter_by(duration_range=old).update({'duration_range': new})
    db.session.commit()
    print('Migración completada.')
import sqlite3
import os

DB_PATH = os.path.join('instance', 'scouts.db')

conn = sqlite3.connect(DB_PATH)
cur  = conn.cursor()

def get_columns(table):
    cur.execute(f"PRAGMA table_info({table})")
    return [row[1] for row in cur.fetchall()]

def get_tables():
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    return [row[0] for row in cur.fetchall()]

tables = get_tables()
print(f"Tablas existentes: {tables}\n")

# ── tabla unit ──────────────────────────────────────────────────────────────
unit_cols = get_columns('unit')
if '"order"' not in unit_cols and 'order' not in unit_cols:
    cur.execute('ALTER TABLE unit ADD COLUMN "order" INTEGER NOT NULL DEFAULT 99')
    print('unit."order" añadida')
else:
    print('unit."order" ya existe')

ORDER_MAP = {
    'Castores': 1, 'Manada': 2, 'Lobatos': 2,
    'Tropa Scout': 3, 'Scouts': 3,
    'Escultas': 4, 'Clan Rover': 5, 'Rovers': 5,
}
cur.execute('SELECT id, name FROM unit')
for uid, name in cur.fetchall():
    order = ORDER_MAP.get(name, 99)
    cur.execute('UPDATE unit SET "order" = ? WHERE id = ?', (order, uid))
    print(f'  unit "{name}" → order={order}')

# ── tabla user ──────────────────────────────────────────────────────────────
user_cols = get_columns('user')
for col, definition in [
    ('grupo_scout', 'VARCHAR(120)'),
    ('instagram',   'VARCHAR(80)'),
]:
    if col not in user_cols:
        cur.execute(f'ALTER TABLE "user" ADD COLUMN {col} {definition}')
        print(f'user.{col} añadida')
    else:
        print(f'user.{col} ya existe')

# ── tabla activity ───────────────────────────────────────────────────────────
if 'activity' in tables:
    act_cols = get_columns('activity')
    for col, definition in [
        ('location_detail',         'VARCHAR(120)'),
        ('min_participants',        'INTEGER'),
        ('max_participants',        'INTEGER'),
        ('age_min',                 'INTEGER'),
        ('age_max',                 'INTEGER'),
        ('attachment_filename',     'VARCHAR(260)'),
        ('attachment_original_name','VARCHAR(260)'),
        ('attachment_mime',         'VARCHAR(100)'),
    ]:
        if col not in act_cols:
            cur.execute(f'ALTER TABLE activity ADD COLUMN {col} {definition}')
            print(f'activity.{col} añadida')
        else:
            print(f'activity.{col} ya existe')

# ── tablas nuevas (likes, listas) ────────────────────────────────────────────
if 'activity_likes' not in tables:
    cur.execute('''
        CREATE TABLE activity_likes (
            user_id     INTEGER NOT NULL REFERENCES user(id),
            activity_id INTEGER NOT NULL REFERENCES activity(id),
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, activity_id)
        )
    ''')
    print('Tabla activity_likes creada')
else:
    print('activity_likes ya existe')

if 'custom_list' not in tables:
    cur.execute('''
        CREATE TABLE custom_list (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        VARCHAR(120) NOT NULL,
            description VARCHAR(300),
            is_public   BOOLEAN NOT NULL DEFAULT 0,
            created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            user_id     INTEGER NOT NULL REFERENCES user(id)
        )
    ''')
    print('Tabla custom_list creada')
else:
    print('custom_list ya existe')

if 'list_activities' not in tables:
    cur.execute('''
        CREATE TABLE list_activities (
            list_id     INTEGER NOT NULL REFERENCES custom_list(id),
            activity_id INTEGER NOT NULL REFERENCES activity(id),
            added_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (list_id, activity_id)
        )
    ''')
    print('Tabla list_activities creada')
else:
    print('list_activities ya existe')

conn.commit()
conn.close()
print('\n✅ Migración completada. Ahora ejecuta: python run.py')

import sqlite3
import json
import os

DB_PATH = os.path.join('instance', 'scouts.db')

conn = sqlite3.connect(DB_PATH)
cur  = conn.cursor()

def get_columns(table):
    cur.execute(f"PRAGMA table_info({table})")
    return [row[1] for row in cur.fetchall()]

user_cols = get_columns('user')

if 'social_media' not in user_cols:
    cur.execute('ALTER TABLE "user" ADD COLUMN social_media TEXT')
    print('user.social_media añadida')
else:
    print('user.social_media ya existe')

if 'instagram' in user_cols:
    cur.execute('SELECT id, instagram FROM "user" WHERE instagram IS NOT NULL AND instagram != ""')
    rows = cur.fetchall()
    migrated = 0
    for uid, ig in rows:
        cur.execute('SELECT social_media FROM "user" WHERE id = ?', (uid,))
        existing_raw = cur.fetchone()[0]
        existing = json.loads(existing_raw) if existing_raw else {}
        if 'instagram' not in existing:
            existing['instagram'] = ig
            cur.execute('UPDATE "user" SET social_media = ? WHERE id = ?',
                        (json.dumps(existing), uid))
            migrated += 1
    if migrated:
        print(f'Migrados {migrated} usuario(s): instagram → social_media')
    else:
        print('No hay datos de instagram que migrar')
else:
    print('Columna instagram no existe, nada que migrar')

conn.commit()
conn.close()
print('\n✅ Migración completada. Ahora ejecuta: python run.py')

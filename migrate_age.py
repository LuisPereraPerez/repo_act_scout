import sqlite3, os
conn = sqlite3.connect(os.path.join('instance', 'scouts.db'))
cur  = conn.cursor()

cols = [r[1] for r in cur.execute("PRAGMA table_info(activity)").fetchall()]
print("Columnas actuales:", cols)

if 'age_min' in cols and 'min_age' not in cols:
    cur.execute('ALTER TABLE activity ADD COLUMN min_age INTEGER')
    cur.execute('ALTER TABLE activity ADD COLUMN max_age INTEGER')
    cur.execute('UPDATE activity SET min_age = age_min, max_age = age_max')
    conn.commit()
    print('Migración completada: age_min → min_age, age_max → max_age')
else:
    print('Nada que migrar.')

conn.close()
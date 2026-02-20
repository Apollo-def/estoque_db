import sqlite3, os, json

base = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.normpath(os.path.join(base, '..', 'instance', 'central.db'))
print('Central DB:', db_path)
if not os.path.exists(db_path):
    print('Arquivo central.db não encontrado')
    raise SystemExit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("SELECT id,nome,email,tipo,unidades_acesso,ativo FROM usuarios WHERE tipo='admin'")
rows = cur.fetchall()
if not rows:
    print('Nenhum admin encontrado')
else:
    for r in rows:
        d = dict(r)
        try:
            if d.get('unidades_acesso'):
                d['unidades_acesso'] = json.loads(d['unidades_acesso'])
        except Exception:
            pass
        print(d)
conn.close()

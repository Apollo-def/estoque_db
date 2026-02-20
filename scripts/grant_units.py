import sqlite3, sys, os, json

if len(sys.argv) < 2:
    print('Uso: python grant_units.py <email> [unit1,unit2,...|all]')
    sys.exit(1)

email = sys.argv[1]
units_arg = sys.argv[2] if len(sys.argv) > 2 else 'all'

base = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.normpath(os.path.join(base, '..', 'instance', 'central.db'))

if not os.path.exists(db_path):
    print('Banco central não encontrado:', db_path)
    sys.exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# obter unidades disponíveis
cur.execute("SELECT id FROM unidades")
rows = cur.fetchall()
available = [r['id'] for r in rows]
if not available:
    print('Não há unidades cadastradas no banco central.')
    conn.close()
    sys.exit(1)

if units_arg == 'all':
    selected = available
else:
    selected = [u.strip() for u in units_arg.split(',') if u.strip()]
    # validar
    invalid = [u for u in selected if u not in available]
    if invalid:
        print('Unidades inválidas:', invalid)
        print('Unidades válidas são:', available)
        conn.close()
        sys.exit(1)

# Atualizar usuário
cur.execute('SELECT id,nome,email,unidades_acesso FROM usuarios WHERE email=?', (email,))
user = cur.fetchone()
if not user:
    print('Usuário não encontrado:', email)
    conn.close()
    sys.exit(1)

unidades_json = json.dumps(selected)
cur.execute('UPDATE usuarios SET unidades_acesso=? WHERE email=?', (unidades_json, email))
conn.commit()
print(f'Atualizado usuário {email} com unidades: {selected}')
conn.close()

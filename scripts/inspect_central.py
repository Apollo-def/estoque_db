import sqlite3, sys, os, json

email = sys.argv[1] if len(sys.argv) > 1 else None
base = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.normpath(os.path.join(base, '..', 'instance', 'central.db'))
print('Central DB path:', db_path)
if not os.path.exists(db_path):
    print('Arquivo do banco central não encontrado:', db_path)
    sys.exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print('\n--- UNIDADES ---')
try:
    # Descobrir colunas disponíveis dinamicamente (compatível com versões antigas)
    cur.execute("PRAGMA table_info('unidades')")
    cols = [c[1] for c in cur.fetchall()]
    if not cols:
        print('Tabela unidades não encontrada')
    else:
        sel = ','.join(cols)
        cur.execute(f'SELECT {sel} FROM unidades')
        rows = cur.fetchall()
        if rows:
            for r in rows:
                print(dict(r))
        else:
            print('Nenhuma unidade encontrada')
except Exception as e:
    print('Erro lendo unidades:', e)

if email:
    print(f"\n--- USUARIO: {email} ---")
    try:
        cur.execute('SELECT id,nome,email,tipo,unidades_acesso,ativo FROM usuarios WHERE email=?',(email,))
        rows = cur.fetchall()
        if rows:
            for r in rows:
                d = dict(r)
                # tentar decodificar unidades_acesso se for JSON
                try:
                    if d.get('unidades_acesso'):
                        d['unidades_acesso'] = json.loads(d['unidades_acesso'])
                except Exception:
                    pass
                print(d)
        else:
            print('Nenhum usuário com esse email')
    except Exception as e:
        print('Erro lendo usuario:', e)

conn.close()

import sqlite3, os, json

base = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.normpath(os.path.join(base, '..', 'instance', 'central.db'))

if not os.path.exists(db_path):
    print('Banco central não encontrado:', db_path)
    exit(1)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Buscar todos os usuários
cur.execute('SELECT id, nome, email, unidades_acesso FROM usuarios')
rows = cur.fetchall()

for row in rows:
    user_id, nome, email, unidades_acesso = row
    print(f'Processando {email}: {unidades_acesso}')

    if unidades_acesso is None or unidades_acesso.strip() == '':
        # Se vazio, definir como lista vazia
        new_value = '[]'
    else:
        # Tentar parsear e re-serializar como JSON válido
        try:
            # Tentar JSON
            parsed = json.loads(unidades_acesso)
            new_value = json.dumps(parsed)
        except:
            try:
                # Tentar ast.literal_eval
                import ast
                parsed = ast.literal_eval(unidades_acesso)
                if isinstance(parsed, list):
                    new_value = json.dumps(parsed)
                else:
                    new_value = '[]'
            except:
                # Se falhar, definir como lista vazia
                new_value = '[]'

    print(f'  -> {new_value}')
    cur.execute('UPDATE usuarios SET unidades_acesso = ? WHERE id = ?', (new_value, user_id))

conn.commit()
conn.close()
print('Normalização concluída!')

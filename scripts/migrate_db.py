import sqlite3, os

base = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.normpath(os.path.join(base, '..', 'instance', 'central.db'))

if not os.path.exists(db_path):
    print('Banco central não encontrado:', db_path)
    exit(1)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Verificar se a coluna 'pode_cadastrar' existe
cur.execute("PRAGMA table_info(usuarios)")
cols = [c[1] for c in cur.fetchall()]

if 'pode_cadastrar' not in cols:
    print('Adicionando coluna pode_cadastrar à tabela usuarios...')
    cur.execute("ALTER TABLE usuarios ADD COLUMN pode_cadastrar INTEGER DEFAULT 1")
    conn.commit()
    print('Coluna adicionada com sucesso.')
else:
    print('Coluna pode_cadastrar já existe.')

conn.close()
print('Migração concluída.')

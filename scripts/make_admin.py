import sqlite3, os, sys
from werkzeug.security import generate_password_hash

# Uso: python make_admin.py <email> <senha>
# Se não passar email/senha, usa valores padrão (mostrados abaixo).

email = sys.argv[1] if len(sys.argv) > 1 else 'admin@exemplo.com'
password = sys.argv[2] if len(sys.argv) > 2 else 'Admin@1234'

base = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.normpath(os.path.join(base, '..', 'instance', 'central.db'))

if not os.path.exists(db_path):
    print('Banco central não encontrado:', db_path)
    sys.exit(1)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Criar usuário se não existir, ou atualizar senha/tipo
senha_hash = generate_password_hash(password)

# Verifica se já existe
cur.execute('SELECT id FROM usuarios WHERE email=?', (email,))
row = cur.fetchone()
if row:
    cur.execute('UPDATE usuarios SET nome=?, senha=?, tipo=?, ativo=1 WHERE email=?', ("Administrador", senha_hash, 'admin', email))
    print('Usuário existente atualizado como admin:', email)
else:
    cur.execute('INSERT INTO usuarios (nome,email,senha,tipo,unidades_acesso,ativo) VALUES (?,?,?,?,?,?)', (
        'Administrador', email, senha_hash, 'admin', '[]', 1
    ))
    print('Usuário admin criado:', email)

conn.commit()
conn.close()
print('\nCredenciais:')
print('Email:', email)
print('Senha:', password)
print('\nRecomendo alterar a senha depois do primeiro login.')

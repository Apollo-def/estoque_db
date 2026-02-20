# Configuração de Bancos de Dados Multi-Tenant
import os
import sqlite3

# Configurações dos bancos de dados por unidade (in-memory defaults)
DATABASES = {
}

# Banco de dados central (autenticação e gestão de usuários)
CENTRAL_DB = {
    'database': 'central.db',
    'type': 'sqlite'
}


def _central_db_path():
    base = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base, 'instance', CENTRAL_DB['database'])


def get_database_config(unit_id):
    """Retorna configuração do banco de dados para uma unidade.

    Procura primeiro em `DATABASES` (configuração em memória). Se não achar,
    tenta ler a tabela `unidades` do banco central e montar a configuração.
    """
    # Checar o dict estático primeiro
    if unit_id in DATABASES:
        return DATABASES[unit_id]

    # Tentar ler do banco central (persistido)
    central_path = _central_db_path()
    if not os.path.exists(central_path):
        return None

    conn = sqlite3.connect(central_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        cur.execute('SELECT * FROM unidades WHERE id = ?', (unit_id,))
        row = cur.fetchone()
        if not row:
            return None

        # Construir configuração com fallback para colunas ausentes
        name = row['nome'] if 'nome' in row.keys() else unit_id
        description = row['descricao'] if 'descricao' in row.keys() else ''
        database_file = None
        db_type = 'sqlite'

        if 'database' in row.keys() and row['database']:
            database_file = row['database']
        else:
            database_file = f"{unit_id}.db"

        if 'type' in row.keys() and row['type']:
            db_type = row['type']

        return {
            'name': name,
            'database': database_file,
            'host': 'localhost',
            'type': db_type,
            'description': description
        }
    finally:
        conn.close()


def get_all_units():
    """Retorna todas as unidades disponíveis (merge entre defaults e central DB)."""
    units = dict(DATABASES)

    central_path = _central_db_path()
    if not os.path.exists(central_path):
        return units

    conn = sqlite3.connect(central_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        cur.execute('SELECT * FROM unidades')
        rows = cur.fetchall()
        for row in rows:
            uid = row['id']
            if uid in units:
                continue
            name = row['nome'] if 'nome' in row.keys() else uid
            description = row['descricao'] if 'descricao' in row.keys() else ''
            database_file = row['database'] if 'database' in row.keys() and row['database'] else f"{uid}.db"
            db_type = row['type'] if 'type' in row.keys() and row['type'] else 'sqlite'
            units[uid] = {
                'name': name,
                'database': database_file,
                'host': 'localhost',
                'type': db_type,
                'description': description
            }
        return units
    finally:
        conn.close()


def get_database_path(unit_id):
    """Retorna o caminho completo do arquivo de banco da unidade (relativo a `instance/`)."""
    config = get_database_config(unit_id)
    if config and config.get('database'):
        base = os.path.abspath(os.path.dirname(__file__))
        return os.path.join(base, 'instance', config['database'])
    return None

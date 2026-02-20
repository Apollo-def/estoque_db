# Gerenciador de Conexões Multi-Tenant
import sqlite3
import os
from flask import g
from database_config import get_database_path, CENTRAL_DB


class DatabaseManager:
    def __init__(self):
        # cache de conexões ativas por chave (unit_id ou '__central__')
        self.connections = {}
    
    def _full_path(self, db_path):
        # Retorna caminho absoluto relativo ao diretório do projeto
        base = os.path.abspath(os.path.dirname(__file__))
        return os.path.join(base, db_path)

    def get_connection(self, unit_id=None, use_cache=True):
        """Obtém conexão com o banco de dados.

        - unit_id: id da unidade; se None retorna o banco central
        - use_cache: se True, reutiliza conexões já abertas
        """
        key = unit_id or '__central__'

        # Retornar conexão em cache se possível
        if use_cache and key in self.connections:
            try:
                # Checagem rápida
                self.connections[key].execute('SELECT 1')
                return self.connections[key]
            except Exception:
                # Conexão inválida: fechar e remover do cache
                try:
                    self.connections[key].close()
                except Exception:
                    pass
                del self.connections[key]

        # Determinar caminho do arquivo de banco
        if unit_id is None:
            db_path = os.path.join('instance', CENTRAL_DB['database'])
        else:
            db_path = get_database_path(unit_id)

        if not db_path:
            raise ValueError(f"Banco de dados não encontrado para unidade: {unit_id}")

        # Criar diretório instance se não existir
        instance_dir = os.path.dirname(self._full_path('instance/placeholder'))
        os.makedirs(instance_dir, exist_ok=True)

        # Conectar ao sqlite (check_same_thread=False para uso em multi-threads leves)
        conn = sqlite3.connect(self._full_path(db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row  # Permite acesso por nome da coluna

        if use_cache:
            self.connections[key] = conn

        return conn

    def init_database(self, unit_id=None):
        """Inicializa estrutura do banco de dados"""
        conn = self.get_connection(unit_id)
        cursor = conn.cursor()
        
        if unit_id is None:
            # Tabelas do banco central
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    senha TEXT NOT NULL,
                    tipo TEXT DEFAULT 'user',
                    unidades_acesso TEXT, -- JSON com unidades que o usuário pode acessar
                    ativo INTEGER DEFAULT 1,
                    pode_cadastrar INTEGER DEFAULT 1,
                    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Criar índices para melhor performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_usuarios_ativo ON usuarios(ativo)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_usuarios_tipo ON usuarios(tipo)')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS unidades (
                    id TEXT PRIMARY KEY,
                    nome TEXT NOT NULL,
                    descricao TEXT,
                    ativa INTEGER DEFAULT 1,
                    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Criar índices para melhor performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_unidades_ativa ON unidades(ativa)')
            
            # Inserir unidades padrão (se existirem em DATABASES)
            from database_config import DATABASES
            for unit_id, config in DATABASES.items():
                cursor.execute('''
                    INSERT OR IGNORE INTO unidades (id, nome, descricao, database, type)
                    VALUES (?, ?, ?, ?, ?)
                ''', (unit_id, config['name'], config['description'], config.get('database'), config.get('type', 'sqlite')))
        
        else:
            # Tabelas do banco da unidade (estoque)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS produtos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    descricao TEXT,
                    quantidade INTEGER DEFAULT 0,
                    categoria TEXT,
                    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
                    data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP,
                    usuario_id INTEGER,
                    codigo_barras TEXT,
                    unidade_medida TEXT DEFAULT 'un',
                    estoque_minimo INTEGER DEFAULT 5,
                    ativo INTEGER DEFAULT 1
                )
            ''')
            
            # Criar índices para melhor performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_produtos_nome ON produtos(nome)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_produtos_categoria ON produtos(categoria)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_produtos_ativo ON produtos(ativo)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_produtos_estoque_minimo ON produtos(estoque_minimo)')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS movimentacoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    produto_id INTEGER NOT NULL,
                    tipo TEXT NOT NULL, -- 'entrada' ou 'saida'
                    quantidade INTEGER NOT NULL,
                    usuario_responsavel_id INTEGER NOT NULL,
                    origem TEXT,
                    destino TEXT,
                    nota_fiscal TEXT,
                    ordem_servico TEXT,
                    motivo TEXT,
                    data_movimentacao DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Criar índices para melhor performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_movimentacoes_produto_id ON movimentacoes(produto_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_movimentacoes_tipo ON movimentacoes(tipo)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_movimentacoes_data ON movimentacoes(data_movimentacao)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_movimentacoes_usuario ON movimentacoes(usuario_responsavel_id)')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS setores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    descricao TEXT,
                    responsavel TEXT,
                    ativo INTEGER DEFAULT 1
                )
            ''')
            
            # Criar índices para melhor performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_setores_nome ON setores(nome)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_setores_ativo ON setores(ativo)')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS fornecedores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    cnpj TEXT,
                    telefone TEXT,
                    email TEXT,
                    endereco TEXT,
                    ativo INTEGER DEFAULT 1
                )
            ''')
            
            # Criar índices para melhor performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_fornecedores_nome ON fornecedores(nome)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_fornecedores_cnpj ON fornecedores(cnpj)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_fornecedores_ativo ON fornecedores(ativo)')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS categorias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    descricao TEXT,
                    ativo INTEGER DEFAULT 1
                )
            ''')
            
            # Criar índices para melhor performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_categorias_nome ON categorias(nome)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_categorias_ativo ON categorias(ativo)')
        
        conn.commit()
        conn.close()
    
    def close_connection(self, unit_id=None):
        """Fecha conexão com o banco de dados"""
        key = unit_id or '__central__'
        if key in self.connections:
            try:
                self.connections[key].close()
            except Exception:
                pass
            del self.connections[key]

    def close_all(self):
        """Fecha todas as conexões em cache"""
        for k in list(self.connections.keys()):
            try:
                self.connections[k].close()
            except Exception:
                pass
            del self.connections[k]

# Instância global do gerenciador
db_manager = DatabaseManager()

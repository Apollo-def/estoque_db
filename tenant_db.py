"""Gerenciamento de conexões por tenant.

Estratégia híbrida:
- Para tenants com type == 'sqlite' delega para `database_manager.db_manager` (retorna sqlite3.Connection)
- Para outros tipos constrói um engine SQLAlchemy e cacheia engines/sessions
"""
import os
from sqlalchemy import create_engine, text
from database_config import get_database_config
from database_manager import db_manager

# Cache de engines para tenants non-sqlite
_engines = {}


class DBAdapter:
    """Adaptador que unifica interface entre sqlite3.Connection e SQLAlchemy Connection.

    Methods used by the app: execute(sql, params), fetchall(), fetchone(), commit(), rollback(), close().
    """
    def __init__(self, conn, is_sqlite=True, sa_connection=None, sa_transaction=None):
        self.is_sqlite = is_sqlite
        if is_sqlite:
            self.conn = conn
            self.cur = None
            self.sa_connection = None
            self.sa_transaction = None
        else:
            # sa_connection is a SQLAlchemy Connection; sa_transaction is begun Transaction
            self.conn = None
            self.sa_connection = sa_connection
            self.sa_transaction = sa_transaction

    def execute(self, sql, params=None):
        if self.is_sqlite:
            cur = self.conn.execute(sql, params or [])
            self.cur = cur
            return cur
        else:
            # Use text() for safety
            if params is None:
                result = self.sa_connection.execute(text(sql))
            else:
                # If params is a list/tuple, pass as positional parameters
                try:
                    result = self.sa_connection.execute(text(sql), params)
                except Exception:
                    # fallback: try named params
                    result = self.sa_connection.execute(text(sql), **(params or {}))
            self.cur = result
            return result

    def fetchall(self):
        if self.cur is None:
            return []
        return self.cur.fetchall()

    def fetchone(self):
        if self.cur is None:
            return None
        return self.cur.fetchone()

    def commit(self):
        if self.is_sqlite:
            return self.conn.commit()
        else:
            if self.sa_transaction is not None:
                return self.sa_transaction.commit()

    def rollback(self):
        if self.is_sqlite:
            try:
                return self.conn.rollback()
            except Exception:
                pass
        else:
            if self.sa_transaction is not None:
                try:
                    return self.sa_transaction.rollback()
                except Exception:
                    pass

    def close(self):
        if self.is_sqlite:
            try:
                self.conn.close()
            except Exception:
                pass
        else:
            try:
                if self.sa_transaction is not None:
                    self.sa_transaction.close()
                if self.sa_connection is not None:
                    self.sa_connection.close()
            except Exception:
                pass


def get_engine_for_unit(unit_id):
    cfg = get_database_config(unit_id)
    if not cfg:
        raise ValueError(f'Unidade não encontrada: {unit_id}')

    uri = cfg.get('sqlalchemy_uri')
    if not uri:
        if cfg.get('type') == 'sqlite':
            return None
        user = cfg.get('user')
        password = cfg.get('password')
        host = cfg.get('host', 'localhost')
        database = cfg.get('database')
        if not database:
            raise ValueError('Configuração de DB incompleta para unidade: %s' % unit_id)
        uri = f"postgresql://{user}:{password}@{host}/{database}"

    if unit_id not in _engines:
        engine = create_engine(uri, pool_size=5, max_overflow=10, pool_pre_ping=True)
        _engines[unit_id] = engine
    return _engines[unit_id]


def get_db_adapter(unit_id):
    """Retorna um DBAdapter para a unidade.

    - Para sqlite: retorna DBAdapter(is_sqlite=True) com sqlite3.Connection
    - Para outros: cria engine se necessário, abre conexão e inicia transação
    """
    cfg = get_database_config(unit_id)
    if not cfg:
        raise ValueError(f'Unidade não encontrada: {unit_id}')

    if cfg.get('type') == 'sqlite':
        conn = db_manager.get_connection(unit_id)
        return DBAdapter(conn, is_sqlite=True)

    engine = get_engine_for_unit(unit_id)
    sa_conn = engine.connect()
    trans = sa_conn.begin()
    return DBAdapter(None, is_sqlite=False, sa_connection=sa_conn, sa_transaction=trans)

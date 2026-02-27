# Modelos SQLAlchemy
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import json
import ast

db = SQLAlchemy()

# Máximo de tentativas antes de bloquear a conta
MAX_TENTATIVAS_LOGIN = 5
# Duração do bloqueio em minutos
BLOQUEIO_MINUTOS = 15


class Usuario(db.Model):
    """Modelo de Usuário (banco central)"""
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.String(20), default='user')
    unidades_acesso = db.Column(db.Text)
    pode_cadastrar = db.Column(db.Integer, default=1)
    permissoes_menu = db.Column(db.Text)
    ativo = db.Column(db.Integer, default=1)
    data_criacao = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    # Proteção contra brute force
    tentativas_login = db.Column(db.Integer, default=0)
    bloqueado_ate = db.Column(db.DateTime, nullable=True)
    
    def get_unidades_acesso(self):
        if not self.unidades_acesso or not self.unidades_acesso.strip():
            return []
        try:
            return json.loads(self.unidades_acesso)
        except Exception:
            try:
                val = ast.literal_eval(self.unidades_acesso)
                if isinstance(val, list):
                    return val
                return json.loads(self.unidades_acesso.replace("'", '"'))
            except Exception:
                try:
                    s = self.unidades_acesso.replace("'", '"')
                    return json.loads(s)
                except Exception:
                    return []
    
    def pode_acessar_unidade(self, unit_id):
        unidades = self.get_unidades_acesso()
        return unit_id in unidades or self.tipo == 'admin'
    
    def is_admin(self):
        return self.tipo == 'admin'

    def esta_bloqueado(self):
        """Verifica se o usuário está com login bloqueado por excesso de tentativas"""
        if self.bloqueado_ate and datetime.now(timezone.utc) < self.bloqueado_ate.replace(tzinfo=timezone.utc):
            return True
        return False

    def registrar_tentativa_falha(self):
        """Incrementa contador; bloqueia após MAX_TENTATIVAS_LOGIN falhas"""
        from datetime import timedelta
        self.tentativas_login = (self.tentativas_login or 0) + 1
        if self.tentativas_login >= MAX_TENTATIVAS_LOGIN:
            self.bloqueado_ate = datetime.now(timezone.utc) + timedelta(minutes=BLOQUEIO_MINUTOS)

    def resetar_tentativas(self):
        """Reseta o contador após login bem-sucedido"""
        self.tentativas_login = 0
        self.bloqueado_ate = None

    def __repr__(self):
        return f'<Usuario {self.nome}>'


class Unidade(db.Model):
    """Modelo de Unidade (banco central)"""
    __tablename__ = 'unidades'
    id = db.Column(db.String(50), primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    database = db.Column(db.String(200))
    type = db.Column(db.String(50))
    ativa = db.Column(db.Integer, default=1)
    data_criacao = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f'<Unidade {self.nome}>'

# Modelos SQLAlchemy
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import json
import ast

db = SQLAlchemy()


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

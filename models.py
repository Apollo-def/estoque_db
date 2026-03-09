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
    matricula = db.Column(db.String(50), unique=True, nullable=True)
    senha = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.String(20), default='user')
    unidades_acesso = db.Column(db.Text)
    pode_cadastrar = db.Column(db.Integer, default=1)
    permissoes_menu = db.Column(db.Text)
    ativo = db.Column(db.Integer, default=1)
    data_criacao = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    ultimo_login = db.Column(db.DateTime, nullable=True)
    # Proteção contra brute force
    tentativas_login = db.Column(db.Integer, default=0)
    bloqueado_ate = db.Column(db.DateTime, nullable=True)
    
    def get_unidades_acesso(self):
        """Lê a coluna unidades_acesso (JSON) e retorna uma lista de IDs."""
        if not self.unidades_acesso or not self.unidades_acesso.strip():
            return []
        try:
            # A fonte de dados deve garantir que o formato é sempre um JSON válido.
            return json.loads(self.unidades_acesso)
        except json.JSONDecodeError:
            return [] # Retorna lista vazia se o JSON for inválido
    
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


class Sugestao(db.Model):
    """Modelo de Sugestões para o Admin"""
    __tablename__ = 'sugestoes'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='Pendente', nullable=False) # Pendente, Em Análise, Concluída
    resposta_admin = db.Column(db.Text, nullable=True)
    data_criacao = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    data_resposta = db.Column(db.DateTime, nullable=True)

    usuario = db.relationship('Usuario', backref=db.backref('sugestoes', lazy=True))

    def __repr__(self):
        return f'<Sugestao {self.id} - {self.titulo}>'


class Notificacao(db.Model):
    """Modelo para notificações do sistema"""
    __tablename__ = 'notificacoes'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    mensagem = db.Column(db.String(255), nullable=False)
    link = db.Column(db.String(255))
    lida = db.Column(db.Boolean, default=False, nullable=False)
    data_criacao = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    usuario = db.relationship('Usuario', backref=db.backref('notificacoes', lazy='dynamic'))

    def __repr__(self):
        return f'<Notificacao {self.id} para {self.usuario_id}>'

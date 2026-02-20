"""
Configurações da aplicação.
Carrega as configurações do ambiente (.env) e define configurações padrão.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Caminho base do projeto
BASE_DIR = Path(__file__).resolve().parent

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv(BASE_DIR / '.env')

class Config:
    """Configurações base da aplicação."""
    # Configurações gerais
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'production')
    DEBUG = os.getenv('FLASK_DEBUG', '0').lower() in ['1', 'true', 'yes']
    
    # Configurações de segurança
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = os.getenv('SESSION_COOKIE_HTTPONLY', 'True').lower() == 'true'
    SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
    PERMANENT_SESSION_LIFETIME = int(os.getenv('PERMANENT_SESSION_LIFETIME', 3600))  # segundos
    
    # Configurações do banco de dados
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
    if not SQLALCHEMY_DATABASE_URI:
        # Se não estiver definido, monta a partir das variáveis individuais
        DB_ENGINE = os.getenv('DB_ENGINE', 'sqlite')
        if DB_ENGINE == 'sqlite':
            db_path = os.path.join(BASE_DIR, 'instance', os.getenv('DB_NAME', 'central.db'))
            SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
        else:
            # Para MySQL, PostgreSQL, etc.
            DB_USER = os.getenv('DB_USER', '')
            DB_PASSWORD = os.getenv('DB_PASSWORD', '')
            DB_HOST = os.getenv('DB_HOST', 'localhost')
            DB_PORT = os.getenv('DB_PORT', '')
            DB_NAME = os.getenv('DB_NAME', 'central')
            
            if DB_ENGINE == 'mysql':
                SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
            elif DB_ENGINE == 'postgresql':
                SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS', 'False').lower() == 'true'
    SQLALCHEMY_ECHO = os.getenv('SQLALCHEMY_ECHO', 'False').lower() == 'true'
    
    # Configurações de upload
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    UPLOAD_FOLDER = os.path.join(BASE_DIR, os.getenv('UPLOAD_FOLDER', 'uploads'))
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
    
    # Configurações de e-mail
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'localhost')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 25))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'False').lower() == 'true'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', None)
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', None)
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@example.com')
    
    # Configurações de log
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.path.join(BASE_DIR, os.getenv('LOG_FILE', 'app.log'))
    
    # Configurações de cache
    CACHE_TYPE = os.getenv('CACHE_TYPE', 'simple')
    CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_DEFAULT_TIMEOUT', 300))
    
    # Configurações de rate limiting
    RATELIMIT_DEFAULT = os.getenv('RATELIMIT_DEFAULT', '200 per day;50 per hour')
    RATELIMIT_STORAGE_URI = os.getenv('RATELIMIT_STORAGE_URI', 'memory://')
    
    @staticmethod
    def init_app(app):
        """Inicialização da aplicação."""
        # Criar pastas necessárias
        for folder in ['instance', app.config['UPLOAD_FOLDER']]:
            os.makedirs(folder, exist_ok=True)


class DevelopmentConfig(Config):
    """Configurações para ambiente de desenvolvimento."""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    
    # Desativa o cache em desenvolvimento
    CACHE_TYPE = 'null'


class TestingConfig(Config):
    """Configurações para testes."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    
    # Desativa o cache em testes
    CACHE_TYPE = 'null'


class ProductionConfig(Config):
    """Configurações para produção."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    
    # Configurações recomendadas para produção
    SQLALCHEMY_POOL_RECYCLE = 280
    SQLALCHEMY_POOL_TIMEOUT = 20
    SQLALCHEMY_POOL_SIZE = 5
    SQLALCHEMY_MAX_OVERFLOW = 10


# Mapeamento de ambientes
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """
    Retorna a configuração apropriada para o ambiente atual.
    
    Returns:
        Config: Uma classe de configuração baseada no ambiente.
    """
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])

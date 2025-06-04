"""
Configurações da aplicação.
Este módulo contém as configurações para diferentes ambientes (desenvolvimento, teste, produção).
"""
import os
from datetime import timedelta

class Config:
    """Configuração base para todos os ambientes."""
    
    # Configurações gerais
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'chave-secreta-padrao-deve-ser-alterada-em-producao'
    APP_NAME = 'Sistema de Ordens de Serviço'
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'admin@exemplo.com'
    
    # Configurações do SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'max_overflow': 5,
        'pool_size': 10
    }
    
    # Configurações de upload
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    
    # Configurações de sessão
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    SESSION_TYPE = 'filesystem'
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Configurações de segurança
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hora
    
    # Configurações de email
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') or True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@exemplo.com'
    
    # Configurações de logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs', 'app.log')
    
    # Configurações de paginação
    ITEMS_PER_PAGE = 10
    
    # Configurações de cache
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Configurações de rate limiting
    RATELIMIT_DEFAULT = "100/hour"
    RATELIMIT_STORAGE_URL = "memory://"
    
    # Configurações de compressão
    COMPRESS_MIMETYPES = [
        'text/html',
        'text/css',
        'text/xml',
        'application/json',
        'application/javascript'
    ]
    COMPRESS_LEVEL = 6
    COMPRESS_MIN_SIZE = 500
    
    @staticmethod
    def init_app(app):
        """Inicialização da aplicação com configurações base."""
        # Criar diretório de uploads se não existir
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        
        # Criar diretório de logs se não existir
        log_dir = os.path.dirname(Config.LOG_FILE)
        os.makedirs(log_dir, exist_ok=True)


class DevelopmentConfig(Config):
    """Configuração para ambiente de desenvolvimento."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dev.db')
    
    # Desativar algumas configurações de segurança em desenvolvimento
    SESSION_COOKIE_SECURE = False
    
    # Configurações de logging para desenvolvimento
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        import logging
        from logging.handlers import RotatingFileHandler
        
        # Configurar logging para arquivo e console
        handler = RotatingFileHandler(Config.LOG_FILE, maxBytes=10000000, backupCount=5)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        handler.setLevel(logging.INFO)
        
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Aplicação iniciada em modo de desenvolvimento')


class TestingConfig(Config):
    """Configuração para ambiente de testes."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or 'sqlite://'
    WTF_CSRF_ENABLED = False
    
    # Desativar rate limiting em testes
    RATELIMIT_ENABLED = False
    
    # Configurações de sessão para testes
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Configuração para ambiente de produção."""
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://user:password@localhost/sistema_os'
    
    # Configurações de segurança para produção
    WTF_CSRF_CHECK_DEFAULT = True
    
    # Configurações de logging para produção
    @staticmethod
    def init_app(app):
        Config.init_app(app)
        import logging
        from logging.handlers import RotatingFileHandler
        
        # Configurar logging para arquivo
        handler = RotatingFileHandler(Config.LOG_FILE, maxBytes=10000000, backupCount=10)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        handler.setLevel(logging.INFO)
        
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Aplicação iniciada em modo de produção')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

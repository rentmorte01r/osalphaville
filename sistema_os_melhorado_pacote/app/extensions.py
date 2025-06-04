"""
Extensões Flask utilizadas na aplicação.
Este módulo inicializa e configura todas as extensões Flask utilizadas no sistema.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from flask_compress import Compress
from flask_cors import CORS

# Inicialização das extensões
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
mail = Mail()
limiter = Limiter(key_func=get_remote_address)
cache = Cache()
compress = Compress()
cors = CORS()

def init_extensions(app):
    """
    Inicializa todas as extensões Flask com a aplicação.
    
    Args:
        app: Instância da aplicação Flask
    """
    # Configuração do SQLAlchemy
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Configuração do Login Manager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'info'
    
    # Proteção CSRF
    csrf.init_app(app)
    
    # Configuração do Flask-Mail
    mail.init_app(app)
    
    # Configuração do Rate Limiter
    limiter.init_app(app)
    
    # Configuração do Cache
    cache_config = {
        'CACHE_TYPE': 'SimpleCache',
        'CACHE_DEFAULT_TIMEOUT': 300
    }
    app.config.from_mapping(cache_config)
    cache.init_app(app)
    
    # Compressão de respostas
    compress.init_app(app)
    
    # Configuração do CORS
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    
    # Configuração de cabeçalhos de segurança
    @app.after_request
    def add_security_headers(response):
        from app.utils.security import set_secure_headers
        return set_secure_headers(response)
    
    # Configuração de logs de atividade
    @app.before_request
    def log_request_info():
        import logging
        from flask import request
        from flask_login import current_user
        
        logger = logging.getLogger('request_logger')
        
        # Registra informações básicas da requisição
        user_id = current_user.id if current_user.is_authenticated else 'Anônimo'
        logger.info(f"Requisição: {request.method} {request.path} | Usuário: {user_id} | IP: {request.remote_addr}")
    
    # Configuração de tratamento de erros
    register_error_handlers(app)

def register_error_handlers(app):
    """
    Registra handlers para erros HTTP comuns.
    
    Args:
        app: Instância da aplicação Flask
    """
    @app.errorhandler(400)
    def bad_request_error(error):
        from flask import render_template
        return render_template('errors/error.html', code=400, 
                              title='Requisição Inválida',
                              message='A requisição enviada contém erros ou está mal formatada.'), 400
    
    @app.errorhandler(401)
    def unauthorized_error(error):
        from flask import render_template
        return render_template('errors/error.html', code=401, 
                              title='Não Autorizado',
                              message='Você precisa fazer login para acessar esta página.'), 401
    
    @app.errorhandler(403)
    def forbidden_error(error):
        from flask import render_template
        return render_template('errors/error.html', code=403, 
                              title='Acesso Negado',
                              message='Você não tem permissão para acessar esta página.'), 403
    
    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template
        return render_template('errors/error.html', code=404, 
                              title='Página Não Encontrada',
                              message='A página que você está procurando não existe ou foi movida.'), 404
    
    @app.errorhandler(429)
    def too_many_requests_error(error):
        from flask import render_template
        return render_template('errors/error.html', code=429, 
                              title='Muitas Requisições',
                              message='Você enviou muitas requisições. Por favor, aguarde um momento e tente novamente.'), 429
    
    @app.errorhandler(500)
    def internal_server_error(error):
        from flask import render_template
        return render_template('errors/error.html', code=500, 
                              title='Erro Interno do Servidor',
                              message='Ocorreu um erro interno no servidor. Nossa equipe foi notificada.'), 500

"""
Inicialização da aplicação Flask.
Este módulo configura a aplicação Flask, registra os blueprints e inicializa as extensões.
"""
import os
from flask import Flask
from app.extensions import db, migrate, login_manager, csrf, bcrypt, limiter
from app.config import config


def create_app(config_name=None):
    """
    Cria e configura a aplicação Flask.
    
    Args:
        config_name (str): Nome da configuração a ser usada (development, production, testing)
        
    Returns:
        Flask: Aplicação Flask configurada
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Inicializa extensões
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    bcrypt.init_app(app)
    limiter.init_app(app)
    
    # Configura login_manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'warning'
    
    # Registra blueprints
    from app.auth import auth_bp
    from app.admin import admin_bp
    from app.ordens import ordens_bp
    from app.dashboard import dashboard_bp
    from app.api import api_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(ordens_bp, url_prefix='/ordens')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Registra handlers de erro
    register_error_handlers(app)
    
    # Cria diretório de uploads se não existir
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    return app


def register_error_handlers(app):
    """
    Registra handlers para erros HTTP.
    
    Args:
        app (Flask): Aplicação Flask
    """
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

# Importação necessária para o handler de erro
from flask import render_template

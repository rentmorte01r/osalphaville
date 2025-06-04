"""
Decoradores personalizados para a aplicação.
Este módulo contém decoradores para controle de acesso, logging e outras funcionalidades.
"""
from functools import wraps
from flask import redirect, url_for, flash, request, abort, current_app
from flask_login import current_user
import time
import logging
from app.models.activity_log import ActivityLog
from app.extensions import db

logger = logging.getLogger(__name__)

def admin_required(func):
    """
    Decorador que verifica se o usuário atual é um administrador.
    Redireciona para a página de login se o usuário não estiver autenticado
    ou para a página de erro se não for administrador.
    
    Args:
        func: Função a ser decorada
        
    Returns:
        function: Função decorada com verificação de administrador
    """
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Você precisa fazer login para acessar esta página.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        if not current_user.is_admin:
            flash('Você não tem permissão para acessar esta página.', 'danger')
            abort(403)
            
        return func(*args, **kwargs)
    
    return decorated_view

def permission_required(permission):
    """
    Decorador que verifica se o usuário atual tem uma permissão específica.
    
    Args:
        permission (str): Nome da permissão necessária
        
    Returns:
        function: Decorador que verifica a permissão
    """
    def decorator(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Você precisa fazer login para acessar esta página.', 'warning')
                return redirect(url_for('auth.login', next=request.url))
            
            if not current_user.has_permission(permission):
                flash('Você não tem permissão para acessar esta funcionalidade.', 'danger')
                abort(403)
                
            return func(*args, **kwargs)
        
        return decorated_view
    
    return decorator

def condominio_access_required(func):
    """
    Decorador que verifica se o usuário atual tem acesso ao condomínio especificado.
    Usado para rotas que recebem um ID de condomínio como parâmetro.
    
    Args:
        func: Função a ser decorada
        
    Returns:
        function: Função decorada com verificação de acesso ao condomínio
    """
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Você precisa fazer login para acessar esta página.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        condominio_id = kwargs.get('condominio_id')
        if condominio_id and not current_user.is_admin:
            if not current_user.has_condominio_access(condominio_id):
                flash('Você não tem acesso a este condomínio.', 'danger')
                abort(403)
                
        return func(*args, **kwargs)
    
    return decorated_view

def ordem_access_required(func):
    """
    Decorador que verifica se o usuário atual tem acesso à ordem de serviço especificada.
    Usado para rotas que recebem um ID de ordem como parâmetro.
    
    Args:
        func: Função a ser decorada
        
    Returns:
        function: Função decorada com verificação de acesso à ordem
    """
    @wraps(func)
    def decorated_view(*args, **kwargs):
        from app.models.ordem import Ordem
        
        if not current_user.is_authenticated:
            flash('Você precisa fazer login para acessar esta página.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        ordem_id = kwargs.get('id')
        if ordem_id:
            ordem = Ordem.query.get_or_404(ordem_id)
            
            if not current_user.is_admin and not current_user.has_condominio_access(ordem.condominio_id):
                flash('Você não tem acesso a esta ordem de serviço.', 'danger')
                abort(403)
                
        return func(*args, **kwargs)
    
    return decorated_view

def log_activity(action):
    """
    Decorador que registra a atividade do usuário.
    
    Args:
        action (str): Descrição da ação realizada
        
    Returns:
        function: Decorador que registra a atividade
    """
    def decorator(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Registra a atividade no banco de dados
            try:
                if current_user.is_authenticated:
                    user_id = current_user.id
                    username = current_user.name
                else:
                    user_id = None
                    username = 'Anônimo'
                
                # Detalhes da ação
                details = f"{action} - {request.method} {request.path}"
                if kwargs:
                    details += f" - Parâmetros: {kwargs}"
                
                # Registra no banco de dados
                log = ActivityLog(
                    user_id=user_id,
                    action=action,
                    details=details,
                    ip_address=request.remote_addr,
                    execution_time=execution_time
                )
                db.session.add(log)
                db.session.commit()
                
                # Registra no log do sistema
                logger.info(
                    f"Atividade: {action} | Usuário: {username} | "
                    f"IP: {request.remote_addr} | Tempo: {execution_time:.4f}s"
                )
                
            except Exception as e:
                logger.error(f"Erro ao registrar atividade: {str(e)}")
                db.session.rollback()
            
            return result
        
        return decorated_view
    
    return decorator

def cache_control(max_age=0, private=True, no_store=False, must_revalidate=True):
    """
    Decorador que define cabeçalhos de controle de cache para uma rota.
    
    Args:
        max_age (int): Tempo máximo de cache em segundos
        private (bool): Se o cache deve ser privado
        no_store (bool): Se o conteúdo não deve ser armazenado em cache
        must_revalidate (bool): Se o cache deve ser revalidado
        
    Returns:
        function: Decorador que define cabeçalhos de cache
    """
    def decorator(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            response = func(*args, **kwargs)
            
            cache_parts = []
            
            if private:
                cache_parts.append('private')
            else:
                cache_parts.append('public')
                
            if no_store:
                cache_parts.append('no-store')
                
            if must_revalidate:
                cache_parts.append('must-revalidate')
                
            cache_parts.append(f'max-age={max_age}')
            
            response.headers['Cache-Control'] = ', '.join(cache_parts)
            
            return response
        
        return decorated_view
    
    return decorator

def rate_limit(limit=100, per=60, scope_func=None):
    """
    Decorador para limitar a taxa de requisições.
    
    Args:
        limit (int): Número máximo de requisições
        per (int): Período em segundos
        scope_func (callable, optional): Função para determinar o escopo do limite
        
    Returns:
        function: Decorador que limita a taxa de requisições
    """
    def decorator(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            from app.extensions import limiter
            
            if scope_func:
                key = scope_func()
            else:
                key = request.remote_addr
                
            # Verifica se o limite foi excedido
            if limiter.is_rate_limited(key, limit, per):
                logger.warning(f"Taxa de requisições excedida para {key}")
                abort(429, description="Muitas requisições. Por favor, tente novamente mais tarde.")
                
            # Incrementa o contador
            limiter.increment(key)
            
            return func(*args, **kwargs)
        
        return decorated_view
    
    return decorator

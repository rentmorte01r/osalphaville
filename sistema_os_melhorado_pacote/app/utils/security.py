"""
Utilitários de segurança para a aplicação.
Este módulo contém funções e classes para garantir a segurança da aplicação.
"""
import os
import re
import secrets
import hashlib
from functools import wraps
from flask import request, abort, current_app, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

# Lista de extensões de arquivo permitidas para upload
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx'}

def generate_csrf_token():
    """
    Gera um token CSRF seguro.
    
    Returns:
        str: Token CSRF gerado
    """
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']

def validate_csrf_token(token):
    """
    Valida um token CSRF.
    
    Args:
        token (str): Token CSRF a ser validado
        
    Returns:
        bool: True se o token for válido, False caso contrário
    """
    session_token = session.get('_csrf_token', None)
    if not session_token or not token:
        return False
    return secrets.compare_digest(session_token, token)

def csrf_protect(func):
    """
    Decorador para proteger rotas contra ataques CSRF.
    
    Args:
        func: Função a ser decorada
        
    Returns:
        function: Função decorada com proteção CSRF
    """
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            token = request.form.get('csrf_token')
            if not token or not validate_csrf_token(token):
                abort(403, description="CSRF token inválido ou ausente")
        return func(*args, **kwargs)
    return decorated_function

def allowed_file(filename, allowed_extensions=None):
    """
    Verifica se um arquivo tem uma extensão permitida.
    
    Args:
        filename (str): Nome do arquivo a ser verificado
        allowed_extensions (set, optional): Conjunto de extensões permitidas. 
                                           Se None, usa ALLOWED_IMAGE_EXTENSIONS.
    
    Returns:
        bool: True se o arquivo tiver uma extensão permitida, False caso contrário
    """
    if allowed_extensions is None:
        allowed_extensions = ALLOWED_IMAGE_EXTENSIONS
        
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def secure_upload_filename(filename):
    """
    Gera um nome de arquivo seguro para upload.
    
    Args:
        filename (str): Nome original do arquivo
        
    Returns:
        str: Nome de arquivo seguro com timestamp
    """
    # Primeiro, usa o secure_filename do Werkzeug para limpar o nome
    secure_name = secure_filename(filename)
    
    # Adiciona um hash aleatório para evitar colisões
    name, ext = os.path.splitext(secure_name)
    random_hex = secrets.token_hex(8)
    
    return f"{name}_{random_hex}{ext}"

def sanitize_input(text):
    """
    Sanitiza entrada de texto para prevenir XSS.
    
    Args:
        text (str): Texto a ser sanitizado
        
    Returns:
        str: Texto sanitizado
    """
    if not text:
        return ""
        
    # Remove tags HTML
    text = re.sub(r'<[^>]*>', '', text)
    
    # Escapa caracteres especiais
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&#x27;')
    
    return text

def hash_password(password):
    """
    Gera um hash seguro para senha.
    
    Args:
        password (str): Senha em texto plano
        
    Returns:
        str: Hash da senha
    """
    return generate_password_hash(password, method='pbkdf2:sha256:150000')

def verify_password(password_hash, password):
    """
    Verifica se uma senha corresponde ao hash armazenado.
    
    Args:
        password_hash (str): Hash da senha armazenada
        password (str): Senha em texto plano a ser verificada
        
    Returns:
        bool: True se a senha for válida, False caso contrário
    """
    return check_password_hash(password_hash, password)

def set_secure_headers(response):
    """
    Define cabeçalhos de segurança para respostas HTTP.
    
    Args:
        response: Objeto de resposta Flask
        
    Returns:
        response: Objeto de resposta com cabeçalhos de segurança
    """
    # Proteção contra clickjacking
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    
    # Proteção XSS
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Previne MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # Content Security Policy
    csp = "default-src 'self'; " \
          "script-src 'self' https://cdn.jsdelivr.net https://code.jquery.com 'unsafe-inline'; " \
          "style-src 'self' https://cdn.jsdelivr.net https://fonts.googleapis.com 'unsafe-inline'; " \
          "font-src 'self' https://cdn.jsdelivr.net https://fonts.gstatic.com https://cdnjs.cloudflare.com; " \
          "img-src 'self' data:; " \
          "connect-src 'self'"
    response.headers['Content-Security-Policy'] = csp
    
    # Referrer Policy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    return response

def validate_password_strength(password):
    """
    Valida a força de uma senha.
    
    Args:
        password (str): Senha a ser validada
        
    Returns:
        tuple: (bool, str) - (é válida, mensagem de erro)
    """
    if len(password) < 8:
        return False, "A senha deve ter pelo menos 8 caracteres."
    
    if not re.search(r'[A-Z]', password):
        return False, "A senha deve conter pelo menos uma letra maiúscula."
    
    if not re.search(r'[a-z]', password):
        return False, "A senha deve conter pelo menos uma letra minúscula."
    
    if not re.search(r'[0-9]', password):
        return False, "A senha deve conter pelo menos um número."
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "A senha deve conter pelo menos um caractere especial."
    
    return True, "Senha válida."

def generate_api_key():
    """
    Gera uma chave de API segura.
    
    Returns:
        str: Chave de API gerada
    """
    return secrets.token_urlsafe(32)

def hash_api_key(api_key):
    """
    Gera um hash para uma chave de API.
    
    Args:
        api_key (str): Chave de API
        
    Returns:
        str: Hash da chave de API
    """
    return hashlib.sha256(api_key.encode()).hexdigest()

def verify_api_key(stored_hash, api_key):
    """
    Verifica se uma chave de API corresponde ao hash armazenado.
    
    Args:
        stored_hash (str): Hash da chave de API armazenada
        api_key (str): Chave de API a ser verificada
        
    Returns:
        bool: True se a chave de API for válida, False caso contrário
    """
    api_hash = hash_api_key(api_key)
    return secrets.compare_digest(stored_hash, api_hash)

"""
Blueprint de autenticação.
Este módulo gerencia as rotas e funcionalidades relacionadas à autenticação de usuários.
"""
from flask import Blueprint

auth_bp = Blueprint('auth', __name__, template_folder='templates')

from app.auth import routes

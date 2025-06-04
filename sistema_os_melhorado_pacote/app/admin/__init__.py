"""
Blueprint de administração.
Este módulo gerencia as rotas e funcionalidades relacionadas à administração do sistema.
"""
from flask import Blueprint

admin_bp = Blueprint('admin', __name__, template_folder='templates')

from app.admin import routes

"""
Blueprint de ordens de serviço.
Este módulo gerencia as rotas e funcionalidades relacionadas às ordens de serviço.
"""
from flask import Blueprint

ordens_bp = Blueprint('ordens', __name__, template_folder='templates')

from app.ordens import routes

"""
Blueprint de dashboard.
Este módulo gerencia as rotas e funcionalidades relacionadas ao dashboard e visualizações estatísticas.
"""
from flask import Blueprint

dashboard_bp = Blueprint('dashboard', __name__, template_folder='templates')

from app.dashboard import routes

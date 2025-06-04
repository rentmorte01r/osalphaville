"""
Blueprint de API.
Este módulo gerencia as rotas e funcionalidades relacionadas à API REST.
"""
from flask import Blueprint

api_bp = Blueprint('api', __name__)

from app.api import routes

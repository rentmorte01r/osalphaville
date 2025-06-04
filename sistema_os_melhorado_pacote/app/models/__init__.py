"""
Inicialização dos modelos de dados.
Este módulo importa todos os modelos para facilitar o acesso.
"""
from app.models.user import User, Role, ActivityLog, PasswordReset, UserCondominio, UserRole
from app.models.condominio import Condominio, Administradora, Area, Fornecedor
from app.models.ordem import OrdemServico, OrdemStatusLog, OrdemComentario, OrdemArquivo

"""
Script para criar e gerenciar migrações do banco de dados.
Este script configura o ambiente para as migrações do Flask-Migrate.
"""
from flask import Flask
from app import create_app, db
from app.models import User, Role, Condominio, Administradora, OrdemServico

# Criar aplicação com configuração de desenvolvimento
app = create_app('development')

# Definir contexto da aplicação
with app.app_context():
    # Importar todos os modelos para que o Alembic possa detectá-los
    from app.models import *

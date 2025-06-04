"""
Rotas de autenticação.
Este módulo implementa as rotas relacionadas à autenticação de usuários.
"""
from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import uuid

from app.auth import auth_bp
from app.auth.forms import LoginForm, RegisterForm, PasswordResetRequestForm, PasswordResetForm
from app.models import User, Condominio, UserCondominio, Role, PasswordReset
from app.extensions import db
from app.utils.email import send_welcome_email, send_password_reset_email
from app.utils.decorators import log_activity

# Timezone para datas
FORTALEZA_TZ = ZoneInfo('America/Fortaleza')


@auth_bp.route('/login', methods=['GET', 'POST'])
@log_activity('login_attempt')
def login():
    """Rota para login de usuários."""
    if current_user.is_authenticated:
        return redirect(url_for('ordens.painel'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        
        if user and user.check_password(form.password.data):
            if user.is_pending:
                flash('Sua conta está pendente de aprovação pelo administrador.', 'warning')
                return redirect(url_for('auth.login'))
            
            if not user.is_active:
                flash('Esta conta está desativada. Entre em contato com o administrador.', 'danger')
                return redirect(url_for('auth.login'))
            
            login_user(user, remember=form.remember_me.data)
            user.update_last_login()
            
            # Registrar atividade de login bem-sucedido
            from app.models import ActivityLog
            log = ActivityLog(
                user_id=user.id,
                activity_type='login_success',
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
            db.session.add(log)
            db.session.commit()
            
            flash('Login realizado com sucesso!', 'success')
            
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('ordens.painel')
            
            return redirect(next_page)
        
        flash('Email ou senha inválidos.', 'danger')
    
    return render_template('auth/login.html', title='Login', form=form)


@auth_bp.route('/logout')
@login_required
@log_activity('logout')
def logout():
    """Rota para logout de usuários."""
    logout_user()
    flash('Você saiu do sistema com sucesso.', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Rota para registro de novos usuários."""
    if current_user.is_authenticated:
        return redirect(url_for('ordens.painel'))
    
    form = RegisterForm()
    
    # Carregar condominios para o select
    form.condominio_id.choices = [(c.id, c.nome) for c in Condominio.query.filter_by(ativo=True).all()]
    
    if form.validate_on_submit():
        # Verificar se o email já existe
        if User.query.filter_by(email=form.email.data.lower()).first():
            flash('Este email já está em uso. Por favor, use outro email.', 'danger')
            return render_template('auth/register.html', title='Registro', form=form)
        
        # Criar novo usuário
        user = User(
            name=form.name.data,
            email=form.email.data.lower(),
            is_pending=True,
            is_admin=False
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.flush()  # Obter ID do usuário sem commit
        
        # Associar usuário ao condomínio selecionado
        user_condominio = UserCondominio(
            user_id=user.id,
            condominio_id=form.condominio_id.data
        )
        db.session.add(user_condominio)
        
        # Associar usuário ao papel padrão (se existir)
        default_role = Role.query.filter_by(name='Usuario').first()
        if default_role:
            from app.models import UserRole
            user_role = UserRole(user_id=user.id, role_id=default_role.id)
            db.session.add(user_role)
        
        db.session.commit()
        
        # Enviar email para administrador sobre novo registro
        admin_emails = [u.email for u in User.query.filter_by(is_admin=True).all()]
        for email in admin_emails:
            send_welcome_email(
                user_name=user.name,
                user_email=email,
                is_admin_notification=True,
                new_user_name=user.name,
                new_user_email=user.email
            )
        
        flash('Registro realizado com sucesso! Aguarde a aprovação do administrador.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', title='Registro', form=form)


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password_request():
    """Rota para solicitar redefinição de senha."""
    if current_user.is_authenticated:
        return redirect(url_for('ordens.painel'))
    
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        
        if user:
            # Gerar token único
            token = str(uuid.uuid4())
            
            # Criar registro de redefinição de senha
            reset = PasswordReset(
                user_id=user.id,
                token=token,
                expires_at=datetime.now(FORTALEZA_TZ) + timedelta(hours=24)
            )
            db.session.add(reset)
            db.session.commit()
            
            # Construir link de redefinição
            reset_link = url_for('auth.reset_password', token=token, _external=True)
            
            # Enviar email
            send_password_reset_email(
                user_name=user.name,
                user_email=user.email,
                reset_link=reset_link
            )
        
        # Sempre mostrar a mesma mensagem para evitar enumeração de usuários
        flash('Se o email estiver cadastrado, você receberá instruções para redefinir sua senha.', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password_request.html', title='Redefinir Senha', form=form)


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Rota para redefinir senha com token."""
    if current_user.is_authenticated:
        return redirect(url_for('ordens.painel'))
    
    # Verificar token
    reset = PasswordReset.query.filter_by(token=token, used=False).first()
    
    if not reset or reset.is_expired():
        flash('O link de redefinição de senha é inválido ou expirou.', 'danger')
        return redirect(url_for('auth.login'))
    
    form = PasswordResetForm()
    if form.validate_on_submit():
        user = User.query.get(reset.user_id)
        
        if user:
            user.set_password(form.password.data)
            reset.used = True
            db.session.commit()
            
            flash('Sua senha foi redefinida com sucesso!', 'success')
            return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', title='Redefinir Senha', form=form)


@auth_bp.route('/profile')
@login_required
def profile():
    """Rota para visualizar perfil do usuário."""
    return render_template('auth/profile.html', title='Meu Perfil')

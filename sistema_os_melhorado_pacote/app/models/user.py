"""
Módulo de modelos para usuários e autenticação.
Este módulo define os modelos relacionados a usuários, permissões e autenticação.
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, bcrypt

# Timezone para datas
FORTALEZA_TZ = ZoneInfo('America/Fortaleza')

# Tabelas de associação
class UserCondominio(db.Model):
    """Associação entre usuários e condomínios."""
    __tablename__ = 'user_condominio'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    condominio_id = db.Column(db.Integer, db.ForeignKey('condominios.id'), primary_key=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(FORTALEZA_TZ))


class UserRole(db.Model):
    """Associação entre usuários e roles."""
    __tablename__ = 'user_role'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), primary_key=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(FORTALEZA_TZ))


class User(db.Model, UserMixin):
    """Modelo de usuário do sistema."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_pending = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(FORTALEZA_TZ))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(FORTALEZA_TZ), 
                           onupdate=lambda: datetime.now(FORTALEZA_TZ))
    
    # Relacionamentos
    condominios = db.relationship('Condominio', secondary='user_condominio', 
                                 back_populates='users', lazy='joined')
    roles = db.relationship('Role', secondary='user_role', 
                           back_populates='users', lazy='joined')
    ordens = db.relationship('OrdemServico', back_populates='user', 
                            foreign_keys='OrdemServico.user_id', lazy='dynamic')
    ordens_criadas = db.relationship('OrdemServico', back_populates='criador', 
                                    foreign_keys='OrdemServico.criador_id', lazy='dynamic')
    activity_logs = db.relationship('ActivityLog', back_populates='user', lazy='dynamic',
                                   cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        """
        Inicializa um novo usuário.
        Se a senha for fornecida em texto plano, converte para hash.
        """
        if 'password' in kwargs and kwargs['password']:
            kwargs['password'] = bcrypt.generate_password_hash(kwargs['password']).decode('utf-8')
        super(User, self).__init__(**kwargs)
    
    def set_password(self, password):
        """Define a senha do usuário, convertendo para hash."""
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        """Verifica se a senha fornecida corresponde à senha do usuário."""
        return bcrypt.check_password_hash(self.password, password)
    
    def has_permission(self, permission):
        """Verifica se o usuário tem a permissão especificada."""
        if self.is_admin:
            return True
        return any(role.has_permission(permission) for role in self.roles)
    
    def update_last_login(self):
        """Atualiza a data do último login."""
        self.last_login = datetime.now(FORTALEZA_TZ)
        db.session.commit()
    
    def __repr__(self):
        return f'<User {self.name}>'


class Role(db.Model):
    """Modelo de papel/função de usuário com permissões associadas."""
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.String(255))
    permissions = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(FORTALEZA_TZ))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(FORTALEZA_TZ), 
                           onupdate=lambda: datetime.now(FORTALEZA_TZ))
    
    # Relacionamentos
    users = db.relationship('User', secondary='user_role', back_populates='roles')
    
    def has_permission(self, permission):
        """Verifica se o papel tem a permissão especificada."""
        if not self.permissions:
            return False
        return permission in self.permissions.split(',')
    
    def add_permission(self, permission):
        """Adiciona uma permissão ao papel."""
        if not self.permissions:
            self.permissions = permission
            return
        
        permissions = self.permissions.split(',')
        if permission not in permissions:
            permissions.append(permission)
            self.permissions = ','.join(permissions)
    
    def remove_permission(self, permission):
        """Remove uma permissão do papel."""
        if not self.permissions:
            return
        
        permissions = self.permissions.split(',')
        if permission in permissions:
            permissions.remove(permission)
            self.permissions = ','.join(permissions)
    
    def __repr__(self):
        return f'<Role {self.name}>'


class ActivityLog(db.Model):
    """Modelo para registro de atividades dos usuários."""
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(FORTALEZA_TZ))
    
    # Relacionamentos
    user = db.relationship('User', back_populates='activity_logs')
    
    def __repr__(self):
        return f'<ActivityLog {self.activity_type} by {self.user_id}>'


class PasswordReset(db.Model):
    """Modelo para tokens de redefinição de senha."""
    __tablename__ = 'password_resets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(100), nullable=False, unique=True, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(FORTALEZA_TZ))
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    
    # Relacionamentos
    user = db.relationship('User')
    
    def is_expired(self):
        """Verifica se o token expirou."""
        return datetime.now(FORTALEZA_TZ) > self.expires_at
    
    def __repr__(self):
        return f'<PasswordReset for user_id={self.user_id}>'

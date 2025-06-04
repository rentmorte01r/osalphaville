"""
Módulo de modelos para condomínios e administradoras.
Este módulo define os modelos relacionados a condomínios e administradoras.
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from app.extensions import db

# Timezone para datas
FORTALEZA_TZ = ZoneInfo('America/Fortaleza')


class Administradora(db.Model):
    """Modelo de administradora de condomínios."""
    __tablename__ = 'administradoras'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False, index=True)
    cnpj = db.Column(db.String(18), unique=True)
    email = db.Column(db.String(120))
    telefone = db.Column(db.String(20))
    endereco = db.Column(db.String(255))
    logo = db.Column(db.String(255))
    ativa = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(FORTALEZA_TZ))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(FORTALEZA_TZ), 
                           onupdate=lambda: datetime.now(FORTALEZA_TZ))
    
    # Relacionamentos
    condominios = db.relationship('Condominio', back_populates='administradora', 
                                 lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Administradora {self.nome}>'


class Condominio(db.Model):
    """Modelo de condomínio."""
    __tablename__ = 'condominios'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False, index=True)
    endereco = db.Column(db.String(255))
    cep = db.Column(db.String(10))
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(2))
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    administradora_id = db.Column(db.Integer, db.ForeignKey('administradoras.id'), nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(FORTALEZA_TZ))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(FORTALEZA_TZ), 
                           onupdate=lambda: datetime.now(FORTALEZA_TZ))
    
    # Relacionamentos
    administradora = db.relationship('Administradora', back_populates='condominios')
    ordens = db.relationship('OrdemServico', back_populates='condominio', 
                            lazy='dynamic', cascade='all, delete-orphan')
    users = db.relationship('User', secondary='user_condominio', back_populates='condominios')
    
    def __repr__(self):
        return f'<Condominio {self.nome}>'


class Area(db.Model):
    """Modelo de área do condomínio."""
    __tablename__ = 'areas'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    condominio_id = db.Column(db.Integer, db.ForeignKey('condominios.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(FORTALEZA_TZ))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(FORTALEZA_TZ), 
                           onupdate=lambda: datetime.now(FORTALEZA_TZ))
    
    # Relacionamentos
    condominio = db.relationship('Condominio')
    ordens = db.relationship('OrdemServico', back_populates='area', lazy='dynamic')
    
    def __repr__(self):
        return f'<Area {self.nome} do {self.condominio.nome}>'


class Fornecedor(db.Model):
    """Modelo de fornecedor de serviços."""
    __tablename__ = 'fornecedores'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False, index=True)
    cnpj_cpf = db.Column(db.String(18), unique=True)
    email = db.Column(db.String(120))
    telefone = db.Column(db.String(20))
    endereco = db.Column(db.String(255))
    tipo_servico = db.Column(db.String(100))
    observacoes = db.Column(db.Text)
    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(FORTALEZA_TZ))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(FORTALEZA_TZ), 
                           onupdate=lambda: datetime.now(FORTALEZA_TZ))
    
    # Relacionamentos
    ordens = db.relationship('OrdemServico', back_populates='fornecedor', lazy='dynamic')
    
    def __repr__(self):
        return f'<Fornecedor {self.nome}>'

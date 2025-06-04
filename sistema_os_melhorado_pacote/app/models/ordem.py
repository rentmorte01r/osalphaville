"""
Módulo de modelos para ordens de serviço.
Este módulo define os modelos relacionados a ordens de serviço e seus status.
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from app.extensions import db

# Timezone para datas
FORTALEZA_TZ = ZoneInfo('America/Fortaleza')


class OrdemServico(db.Model):
    """Modelo de ordem de serviço."""
    __tablename__ = 'ordens_servico'
    
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), unique=True, index=True)
    condominio_id = db.Column(db.Integer, db.ForeignKey('condominios.id'), nullable=False)
    area_id = db.Column(db.Integer, db.ForeignKey('areas.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    criador_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('fornecedores.id'))
    
    titulo = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    prioridade = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Aberta', index=True)
    tipo = db.Column(db.String(50), default='Manutenção')
    
    observacoes = db.Column(db.Text)
    valor_estimado = db.Column(db.Numeric(10, 2))
    valor_final = db.Column(db.Numeric(10, 2))
    
    foto_inicial = db.Column(db.String(255))
    foto_andamento = db.Column(db.String(255))
    foto_final = db.Column(db.String(255))
    cotacao = db.Column(db.String(255))
    
    data_criacao = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(FORTALEZA_TZ), index=True)
    data_inicio = db.Column(db.DateTime)
    data_previsao = db.Column(db.DateTime)
    data_conclusao = db.Column(db.DateTime, index=True)
    
    # Relacionamentos
    condominio = db.relationship('Condominio', back_populates='ordens')
    area = db.relationship('Area', back_populates='ordens')
    user = db.relationship('User', back_populates='ordens', foreign_keys=[user_id])
    criador = db.relationship('User', back_populates='ordens_criadas', foreign_keys=[criador_id])
    fornecedor = db.relationship('Fornecedor', back_populates='ordens')
    status_logs = db.relationship('OrdemStatusLog', back_populates='ordem', cascade='all, delete-orphan', order_by='desc(OrdemStatusLog.data_mudanca)')
    comentarios = db.relationship('OrdemComentario', back_populates='ordem', cascade='all, delete-orphan', order_by='desc(OrdemComentario.data_criacao)')
    arquivos = db.relationship('OrdemArquivo', back_populates='ordem', cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        """
        Inicializa uma nova ordem de serviço.
        Gera automaticamente um número único para a ordem.
        """
        super(OrdemServico, self).__init__(**kwargs)
        if not self.numero:
            # Gerar número único no formato OS-ANO-SEQUENCIAL
            ano = datetime.now(FORTALEZA_TZ).year
            ultimo = OrdemServico.query.filter(
                OrdemServico.numero.like(f'OS-{ano}-%')
            ).order_by(OrdemServico.id.desc()).first()
            
            if ultimo:
                ultimo_num = int(ultimo.numero.split('-')[-1])
                self.numero = f'OS-{ano}-{ultimo_num + 1:04d}'
            else:
                self.numero = f'OS-{ano}-0001'
    
    def atualizar_status(self, novo_status, usuario_id, observacao=None):
        """
        Atualiza o status da ordem e cria um registro de log.
        
        Args:
            novo_status (str): Novo status da ordem
            usuario_id (int): ID do usuário que está alterando o status
            observacao (str, optional): Observação sobre a mudança de status
        """
        if self.status != novo_status:
            # Registrar log de mudança de status
            log = OrdemStatusLog(
                ordem_id=self.id,
                status_anterior=self.status,
                status_novo=novo_status,
                usuario_id=usuario_id,
                observacao=observacao
            )
            db.session.add(log)
            
            # Atualizar status da ordem
            self.status = novo_status
            
            # Atualizar datas conforme o status
            now = datetime.now(FORTALEZA_TZ)
            if novo_status == 'Em Andamento' and not self.data_inicio:
                self.data_inicio = now
            elif novo_status == 'Concluída' and not self.data_conclusao:
                self.data_conclusao = now
    
    def adicionar_comentario(self, usuario_id, texto):
        """
        Adiciona um comentário à ordem.
        
        Args:
            usuario_id (int): ID do usuário que está comentando
            texto (str): Texto do comentário
        """
        comentario = OrdemComentario(
            ordem_id=self.id,
            usuario_id=usuario_id,
            texto=texto
        )
        db.session.add(comentario)
        return comentario
    
    def adicionar_arquivo(self, nome, caminho, tipo, usuario_id):
        """
        Adiciona um arquivo à ordem.
        
        Args:
            nome (str): Nome original do arquivo
            caminho (str): Caminho do arquivo no sistema
            tipo (str): Tipo do arquivo (foto_inicial, foto_andamento, etc.)
            usuario_id (int): ID do usuário que está adicionando o arquivo
        """
        arquivo = OrdemArquivo(
            ordem_id=self.id,
            nome=nome,
            caminho=caminho,
            tipo=tipo,
            usuario_id=usuario_id
        )
        db.session.add(arquivo)
        return arquivo
    
    def __repr__(self):
        return f'<OrdemServico {self.numero}>'


class OrdemStatusLog(db.Model):
    """Modelo de log de mudanças de status de uma ordem de serviço."""
    __tablename__ = 'ordem_status_log'
    
    id = db.Column(db.Integer, primary_key=True)
    ordem_id = db.Column(db.Integer, db.ForeignKey('ordens_servico.id'), nullable=False)
    status_anterior = db.Column(db.String(50), nullable=False)
    status_novo = db.Column(db.String(50), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    observacao = db.Column(db.Text)
    data_mudanca = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(FORTALEZA_TZ))
    
    # Relacionamentos
    ordem = db.relationship('OrdemServico', back_populates='status_logs')
    usuario = db.relationship('User')
    
    def __repr__(self):
        return f'<OrdemStatusLog {self.id}: {self.status_anterior} -> {self.status_novo}>'


class OrdemComentario(db.Model):
    """Modelo de comentário em uma ordem de serviço."""
    __tablename__ = 'ordem_comentarios'
    
    id = db.Column(db.Integer, primary_key=True)
    ordem_id = db.Column(db.Integer, db.ForeignKey('ordens_servico.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    texto = db.Column(db.Text, nullable=False)
    data_criacao = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(FORTALEZA_TZ))
    
    # Relacionamentos
    ordem = db.relationship('OrdemServico', back_populates='comentarios')
    usuario = db.relationship('User')
    
    def __repr__(self):
        return f'<OrdemComentario {self.id}>'


class OrdemArquivo(db.Model):
    """Modelo de arquivo anexado a uma ordem de serviço."""
    __tablename__ = 'ordem_arquivos'
    
    id = db.Column(db.Integer, primary_key=True)
    ordem_id = db.Column(db.Integer, db.ForeignKey('ordens_servico.id'), nullable=False)
    nome = db.Column(db.String(255), nullable=False)
    caminho = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.String(50))  # foto_inicial, foto_andamento, foto_final, cotacao, outro
    tamanho = db.Column(db.Integer)  # tamanho em bytes
    mime_type = db.Column(db.String(100))
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    data_upload = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(FORTALEZA_TZ))
    
    # Relacionamentos
    ordem = db.relationship('OrdemServico', back_populates='arquivos')
    usuario = db.relationship('User')
    
    def __repr__(self):
        return f'<OrdemArquivo {self.nome}>'

"""
Formulários para administração.
Este módulo define os formulários relacionados à administração do sistema.
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms import TextAreaField, SelectMultipleField, DecimalField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional
from app.models import User, Role, Condominio, Administradora


class AdministradoraForm(FlaskForm):
    """Formulário para administradoras."""
    nome = StringField('Nome', validators=[DataRequired(), Length(min=3, max=255)])
    cnpj = StringField('CNPJ', validators=[Length(max=18)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    telefone = StringField('Telefone', validators=[Length(max=20)])
    endereco = StringField('Endereço', validators=[Length(max=255)])
    logo = FileField('Logo', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Apenas imagens são permitidas!')
    ])
    ativa = BooleanField('Ativa')
    submit = SubmitField('Salvar')


class CondominioForm(FlaskForm):
    """Formulário para condomínios."""
    nome = StringField('Nome', validators=[DataRequired(), Length(min=3, max=255)])
    endereco = StringField('Endereço', validators=[Length(max=255)])
    cep = StringField('CEP', validators=[Length(max=10)])
    cidade = StringField('Cidade', validators=[Length(max=100)])
    estado = SelectField('Estado', choices=[
        ('', 'Selecione...'),
        ('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'), ('AM', 'Amazonas'),
        ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'),
        ('GO', 'Goiás'), ('MA', 'Maranhão'), ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'),
        ('MG', 'Minas Gerais'), ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'),
        ('PE', 'Pernambuco'), ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'),
        ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'), ('SC', 'Santa Catarina'),
        ('SP', 'São Paulo'), ('SE', 'Sergipe'), ('TO', 'Tocantins')
    ])
    telefone = StringField('Telefone', validators=[Length(max=20)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    administradora_id = SelectField('Administradora', coerce=int, validators=[DataRequired()])
    ativo = BooleanField('Ativo')
    submit = SubmitField('Salvar')


class UserForm(FlaskForm):
    """Formulário para usuários."""
    name = StringField('Nome', validators=[DataRequired(), Length(min=3, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Senha', validators=[
        Optional(),
        Length(min=8, message='A senha deve ter pelo menos 8 caracteres.')
    ])
    password2 = PasswordField('Confirmar Senha', validators=[
        EqualTo('password', message='As senhas devem ser iguais.')
    ])
    is_admin = BooleanField('Administrador')
    is_active = BooleanField('Ativo', default=True)
    condominios = SelectMultipleField('Condomínios', coerce=int)
    roles = SelectMultipleField('Papéis', coerce=int)
    submit = SubmitField('Salvar')
    
    def validate_email(self, email):
        """Valida se o email já está em uso por outro usuário."""
        user = User.query.filter_by(email=email.data.lower()).first()
        if user and (not hasattr(self, 'user_id') or user.id != self.user_id):
            raise ValidationError('Este email já está em uso. Por favor, use outro email.')


class RoleForm(FlaskForm):
    """Formulário para papéis (roles)."""
    name = StringField('Nome', validators=[DataRequired(), Length(min=3, max=50)])
    description = StringField('Descrição', validators=[Length(max=255)])
    permissions = SelectMultipleField('Permissões', choices=[
        ('create_order', 'Criar Ordem'),
        ('edit_order', 'Editar Ordem'),
        ('delete_order', 'Excluir Ordem'),
        ('view_order', 'Visualizar Ordem'),
        ('assign_order', 'Atribuir Ordem'),
        ('complete_order', 'Concluir Ordem'),
        ('view_reports', 'Visualizar Relatórios'),
        ('manage_users', 'Gerenciar Usuários'),
        ('manage_condominios', 'Gerenciar Condomínios'),
        ('manage_fornecedores', 'Gerenciar Fornecedores')
    ])
    submit = SubmitField('Salvar')
    
    def validate_name(self, name):
        """Valida se o nome do papel já existe."""
        role = Role.query.filter_by(name=name.data).first()
        if role and (not hasattr(self, 'role_id') or role.id != self.role_id):
            raise ValidationError('Este nome de papel já existe. Por favor, use outro nome.')


class AreaForm(FlaskForm):
    """Formulário para áreas de condomínio."""
    nome = StringField('Nome', validators=[DataRequired(), Length(min=3, max=100)])
    descricao = TextAreaField('Descrição')
    condominio_id = SelectField('Condomínio', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Salvar')


class FornecedorForm(FlaskForm):
    """Formulário para fornecedores."""
    nome = StringField('Nome', validators=[DataRequired(), Length(min=3, max=255)])
    cnpj_cpf = StringField('CNPJ/CPF', validators=[Length(max=18)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    telefone = StringField('Telefone', validators=[Length(max=20)])
    endereco = StringField('Endereço', validators=[Length(max=255)])
    tipo_servico = StringField('Tipo de Serviço', validators=[Length(max=100)])
    observacoes = TextAreaField('Observações')
    ativo = BooleanField('Ativo', default=True)
    submit = SubmitField('Salvar')


class ApproveUserForm(FlaskForm):
    """Formulário para aprovar usuários pendentes."""
    roles = SelectMultipleField('Papéis', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Aprovar Usuário')

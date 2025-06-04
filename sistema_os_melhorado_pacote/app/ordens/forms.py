"""
Formulários para ordens de serviço.
Este módulo define os formulários relacionados às ordens de serviço.
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, SubmitField, DecimalField, DateField
from wtforms import BooleanField, HiddenField, SelectMultipleField
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from datetime import date


class OrdemForm(FlaskForm):
    """Formulário para criação de ordem de serviço."""
    titulo = StringField('Título', validators=[DataRequired(), Length(min=3, max=100)])
    descricao = TextAreaField('Descrição', validators=[DataRequired()])
    prioridade = SelectField('Prioridade', choices=[
        ('Alta', 'Alta'),
        ('Normal', 'Normal'),
        ('Baixa', 'Baixa')
    ], validators=[DataRequired()])
    tipo = SelectField('Tipo', choices=[
        ('Manutenção', 'Manutenção'),
        ('Reparo', 'Reparo'),
        ('Instalação', 'Instalação'),
        ('Limpeza', 'Limpeza'),
        ('Outro', 'Outro')
    ], validators=[DataRequired()])
    condominio_id = SelectField('Condomínio', coerce=int, validators=[DataRequired()])
    area_id = SelectField('Área', coerce=int, validators=[Optional()])
    fornecedor_id = SelectField('Fornecedor', coerce=int, validators=[Optional()])
    observacoes = TextAreaField('Observações')
    valor_estimado = DecimalField('Valor Estimado (R$)', validators=[Optional()], places=2)
    data_previsao = DateField('Data Prevista', validators=[Optional()])
    foto_inicial = FileField('Foto Inicial', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Apenas imagens são permitidas!')
    ])
    cotacao = FileField('Cotação', validators=[
        FileAllowed(['pdf', 'jpg', 'png', 'jpeg'], 'Apenas PDF ou imagens são permitidos!')
    ])
    submit = SubmitField('Salvar')


class OrdemEditForm(FlaskForm):
    """Formulário para edição de ordem de serviço."""
    titulo = StringField('Título', validators=[DataRequired(), Length(min=3, max=100)])
    descricao = TextAreaField('Descrição', validators=[DataRequired()])
    prioridade = SelectField('Prioridade', choices=[
        ('Alta', 'Alta'),
        ('Normal', 'Normal'),
        ('Baixa', 'Baixa')
    ], validators=[DataRequired()])
    tipo = SelectField('Tipo', choices=[
        ('Manutenção', 'Manutenção'),
        ('Reparo', 'Reparo'),
        ('Instalação', 'Instalação'),
        ('Limpeza', 'Limpeza'),
        ('Outro', 'Outro')
    ], validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('Aberta', 'Aberta'),
        ('Em Andamento', 'Em Andamento'),
        ('Aguardando Aprovação', 'Aguardando Aprovação'),
        ('Aguardando Material', 'Aguardando Material'),
        ('Concluída', 'Concluída'),
        ('Cancelada', 'Cancelada')
    ], validators=[DataRequired()])
    condominio_id = SelectField('Condomínio', coerce=int, validators=[DataRequired()])
    area_id = SelectField('Área', coerce=int, validators=[Optional()])
    fornecedor_id = SelectField('Fornecedor', coerce=int, validators=[Optional()])
    user_id = SelectField('Responsável', coerce=int, validators=[Optional()])
    observacoes = TextAreaField('Observações')
    valor_estimado = DecimalField('Valor Estimado (R$)', validators=[Optional()], places=2)
    valor_final = DecimalField('Valor Final (R$)', validators=[Optional()], places=2)
    data_previsao = DateField('Data Prevista', validators=[Optional()])
    foto_inicial = FileField('Foto Inicial', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Apenas imagens são permitidas!')
    ])
    foto_andamento = FileField('Foto Andamento', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Apenas imagens são permitidas!')
    ])
    foto_final = FileField('Foto Final', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Apenas imagens são permitidas!')
    ])
    cotacao = FileField('Cotação', validators=[
        FileAllowed(['pdf', 'jpg', 'png', 'jpeg'], 'Apenas PDF ou imagens são permitidos!')
    ])
    submit = SubmitField('Salvar')


class OrdemComentarioForm(FlaskForm):
    """Formulário para comentários em ordens de serviço."""
    texto = TextAreaField('Comentário', validators=[DataRequired()])
    submit = SubmitField('Adicionar Comentário')


class OrdemFiltroForm(FlaskForm):
    """Formulário para filtrar ordens de serviço."""
    condominio_id = SelectField('Condomínio', coerce=int)
    status = SelectField('Status', choices=[
        ('Todos', 'Todos'),
        ('Aberta', 'Aberta'),
        ('Em Andamento', 'Em Andamento'),
        ('Aguardando Aprovação', 'Aguardando Aprovação'),
        ('Aguardando Material', 'Aguardando Material'),
        ('Concluída', 'Concluída'),
        ('Cancelada', 'Cancelada')
    ])
    prioridade = SelectField('Prioridade', choices=[
        ('Todas', 'Todas'),
        ('Alta', 'Alta'),
        ('Normal', 'Normal'),
        ('Baixa', 'Baixa')
    ])
    data_inicial = DateField('Data Inicial', validators=[Optional()])
    data_final = DateField('Data Final', validators=[Optional()])
    submit = SubmitField('Filtrar')

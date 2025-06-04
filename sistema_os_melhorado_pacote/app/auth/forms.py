"""
Formulários para autenticação.
Este módulo define os formulários relacionados à autenticação de usuários.
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models import User


class LoginForm(FlaskForm):
    """Formulário de login."""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember_me = BooleanField('Lembrar-me')
    submit = SubmitField('Entrar')


class RegisterForm(FlaskForm):
    """Formulário de registro de novos usuários."""
    name = StringField('Nome Completo', validators=[DataRequired(), Length(min=3, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[
        DataRequired(),
        Length(min=8, message='A senha deve ter pelo menos 8 caracteres.')
    ])
    password2 = PasswordField('Confirmar Senha', validators=[
        DataRequired(),
        EqualTo('password', message='As senhas devem ser iguais.')
    ])
    condominio_id = SelectField('Condomínio', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Registrar')
    
    def validate_email(self, email):
        """Valida se o email já está em uso."""
        user = User.query.filter_by(email=email.data.lower()).first()
        if user:
            raise ValidationError('Este email já está em uso. Por favor, use outro email.')


class PasswordResetRequestForm(FlaskForm):
    """Formulário para solicitar redefinição de senha."""
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Solicitar Redefinição de Senha')


class PasswordResetForm(FlaskForm):
    """Formulário para redefinir senha."""
    password = PasswordField('Nova Senha', validators=[
        DataRequired(),
        Length(min=8, message='A senha deve ter pelo menos 8 caracteres.')
    ])
    password2 = PasswordField('Confirmar Nova Senha', validators=[
        DataRequired(),
        EqualTo('password', message='As senhas devem ser iguais.')
    ])
    submit = SubmitField('Redefinir Senha')


class ChangePasswordForm(FlaskForm):
    """Formulário para alterar senha."""
    current_password = PasswordField('Senha Atual', validators=[DataRequired()])
    password = PasswordField('Nova Senha', validators=[
        DataRequired(),
        Length(min=8, message='A senha deve ter pelo menos 8 caracteres.')
    ])
    password2 = PasswordField('Confirmar Nova Senha', validators=[
        DataRequired(),
        EqualTo('password', message='As senhas devem ser iguais.')
    ])
    submit = SubmitField('Alterar Senha')

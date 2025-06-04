"""
Testes unitários para o módulo de autenticação.
Este arquivo contém testes para as funcionalidades de login, registro e redefinição de senha.
"""
import unittest
from flask import url_for
from app import create_app, db
from app.models.user import User
from app.models.condominio import Condominio
from app.models.role import Role

class AuthTestCase(unittest.TestCase):
    """Testes para o módulo de autenticação."""
    
    def setUp(self):
        """Configuração inicial para cada teste."""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client(use_cookies=True)
        
        # Criar dados de teste
        self._create_test_data()
    
    def tearDown(self):
        """Limpeza após cada teste."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def _create_test_data(self):
        """Cria dados de teste para os testes de autenticação."""
        # Criar condomínio de teste
        condominio = Condominio(nome='Condomínio Teste', endereco='Rua Teste, 123')
        db.session.add(condominio)
        
        # Criar papel de administrador
        admin_role = Role(name='Admin', description='Administrador do sistema')
        db.session.add(admin_role)
        
        # Criar papel de usuário
        user_role = Role(name='User', description='Usuário comum')
        db.session.add(user_role)
        
        # Criar usuário de teste
        user = User(
            name='Usuário Teste',
            email='teste@exemplo.com',
            password='Senha@123',
            is_active=True,
            is_admin=False
        )
        user.condominios.append(condominio)
        user.roles.append(user_role)
        db.session.add(user)
        
        # Criar usuário administrador
        admin = User(
            name='Admin Teste',
            email='admin@exemplo.com',
            password='Admin@123',
            is_active=True,
            is_admin=True
        )
        admin.roles.append(admin_role)
        db.session.add(admin)
        
        db.session.commit()
    
    def test_login_page(self):
        """Testa se a página de login é carregada corretamente."""
        response = self.client.get('/auth/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)
    
    def test_login_success(self):
        """Testa login bem-sucedido."""
        response = self.client.post('/auth/login', data={
            'email': 'teste@exemplo.com',
            'password': 'Senha@123',
            'remember_me': False
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login realizado com sucesso', response.data)
        self.assertIn(b'Painel de Controle', response.data)
    
    def test_login_invalid_credentials(self):
        """Testa login com credenciais inválidas."""
        response = self.client.post('/auth/login', data={
            'email': 'teste@exemplo.com',
            'password': 'senha_errada',
            'remember_me': False
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Email ou senha incorretos', response.data)
    
    def test_login_inactive_user(self):
        """Testa login com usuário inativo."""
        # Desativar o usuário de teste
        user = User.query.filter_by(email='teste@exemplo.com').first()
        user.is_active = False
        db.session.commit()
        
        response = self.client.post('/auth/login', data={
            'email': 'teste@exemplo.com',
            'password': 'Senha@123',
            'remember_me': False
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Conta inativa', response.data)
    
    def test_logout(self):
        """Testa o processo de logout."""
        # Primeiro fazer login
        self.client.post('/auth/login', data={
            'email': 'teste@exemplo.com',
            'password': 'Senha@123',
            'remember_me': False
        })
        
        # Depois fazer logout
        response = self.client.get('/auth/logout', follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Logout realizado com sucesso', response.data)
        self.assertIn(b'Login', response.data)
    
    def test_register_page(self):
        """Testa se a página de registro é carregada corretamente."""
        response = self.client.get('/auth/register')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Registro de Novo Usu', response.data)  # "Usuário" com acento
    
    def test_register_success(self):
        """Testa registro bem-sucedido."""
        condominio = Condominio.query.first()
        
        response = self.client.post('/auth/register', data={
            'name': 'Novo Usuário',
            'email': 'novo@exemplo.com',
            'password': 'Novo@123',
            'password2': 'Novo@123',
            'condominio_id': condominio.id
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Registro realizado com sucesso', response.data)
        
        # Verificar se o usuário foi criado no banco
        user = User.query.filter_by(email='novo@exemplo.com').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.name, 'Novo Usuário')
        self.assertFalse(user.is_active)  # Usuário deve estar inativo até aprovação
    
    def test_register_duplicate_email(self):
        """Testa registro com email duplicado."""
        condominio = Condominio.query.first()
        
        response = self.client.post('/auth/register', data={
            'name': 'Usuário Duplicado',
            'email': 'teste@exemplo.com',  # Email já existente
            'password': 'Senha@123',
            'password2': 'Senha@123',
            'condominio_id': condominio.id
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Email j', response.data)  # "já" com acento
    
    def test_register_password_mismatch(self):
        """Testa registro com senhas diferentes."""
        condominio = Condominio.query.first()
        
        response = self.client.post('/auth/register', data={
            'name': 'Usuário Teste',
            'email': 'novo2@exemplo.com',
            'password': 'Senha@123',
            'password2': 'Senha@456',  # Senha diferente
            'condominio_id': condominio.id
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'As senhas devem ser iguais', response.data)
    
    def test_reset_password_request(self):
        """Testa solicitação de redefinição de senha."""
        response = self.client.post('/auth/reset_password_request', data={
            'email': 'teste@exemplo.com'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Um email foi enviado com instru', response.data)  # "instruções" com acento
    
    def test_admin_access(self):
        """Testa acesso a área administrativa."""
        # Login como administrador
        self.client.post('/auth/login', data={
            'email': 'admin@exemplo.com',
            'password': 'Admin@123',
            'remember_me': False
        })
        
        # Acessar área administrativa
        response = self.client.get('/admin/dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Painel Administrativo', response.data)
    
    def test_non_admin_access_denied(self):
        """Testa acesso negado a área administrativa para usuários comuns."""
        # Login como usuário comum
        self.client.post('/auth/login', data={
            'email': 'teste@exemplo.com',
            'password': 'Senha@123',
            'remember_me': False
        })
        
        # Tentar acessar área administrativa
        response = self.client.get('/admin/dashboard', follow_redirects=True)
        self.assertEqual(response.status_code, 403)
        self.assertIn(b'Acesso Negado', response.data)


if __name__ == '__main__':
    unittest.main()

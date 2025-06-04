"""
Testes unitários para o módulo de ordens de serviço.
Este arquivo contém testes para as funcionalidades de criação, edição, listagem e detalhes de ordens.
"""
import unittest
import os
from io import BytesIO
from flask import url_for
from app import create_app, db
from app.models.user import User
from app.models.condominio import Condominio
from app.models.ordem import Ordem, OrdemStatus
from app.models.area import Area
from app.models.fornecedor import Fornecedor

class OrdensTestCase(unittest.TestCase):
    """Testes para o módulo de ordens de serviço."""
    
    def setUp(self):
        """Configuração inicial para cada teste."""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client(use_cookies=True)
        
        # Criar dados de teste
        self._create_test_data()
        
        # Login como usuário de teste
        self._login_test_user()
    
    def tearDown(self):
        """Limpeza após cada teste."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def _create_test_data(self):
        """Cria dados de teste para os testes de ordens."""
        # Criar condomínio de teste
        self.condominio = Condominio(nome='Condomínio Teste', endereco='Rua Teste, 123')
        db.session.add(self.condominio)
        
        # Criar área de teste
        self.area = Area(nome='Área Teste', condominio=self.condominio)
        db.session.add(self.area)
        
        # Criar fornecedor de teste
        self.fornecedor = Fornecedor(
            nome='Fornecedor Teste',
            telefone='(11) 99999-9999',
            email='fornecedor@exemplo.com'
        )
        db.session.add(self.fornecedor)
        
        # Criar usuário de teste
        self.user = User(
            name='Usuário Teste',
            email='teste@exemplo.com',
            password='Senha@123',
            is_active=True,
            is_admin=False
        )
        self.user.condominios.append(self.condominio)
        db.session.add(self.user)
        
        # Criar usuário administrador
        self.admin = User(
            name='Admin Teste',
            email='admin@exemplo.com',
            password='Admin@123',
            is_active=True,
            is_admin=True
        )
        db.session.add(self.admin)
        
        # Criar ordem de teste
        self.ordem = Ordem(
            titulo='Ordem de Teste',
            descricao='Descrição da ordem de teste',
            status='Aberta',
            prioridade='Normal',
            tipo='Manutenção',
            condominio=self.condominio,
            area=self.area,
            user=self.user,
            fornecedor=self.fornecedor
        )
        db.session.add(self.ordem)
        
        db.session.commit()
    
    def _login_test_user(self):
        """Faz login com o usuário de teste."""
        self.client.post('/auth/login', data={
            'email': 'teste@exemplo.com',
            'password': 'Senha@123',
            'remember_me': False
        })
    
    def _login_admin_user(self):
        """Faz login com o usuário administrador."""
        self.client.post('/auth/login', data={
            'email': 'admin@exemplo.com',
            'password': 'Admin@123',
            'remember_me': False
        })
    
    def test_painel_page(self):
        """Testa se a página do painel é carregada corretamente."""
        response = self.client.get('/ordens/painel')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Painel de Controle', response.data)
    
    def test_listar_ordens(self):
        """Testa se a página de listagem de ordens é carregada corretamente."""
        response = self.client.get('/ordens/listar')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Ordens de Servi', response.data)  # "Serviço" com acento
        self.assertIn(b'Ordem de Teste', response.data)
    
    def test_detalhe_ordem(self):
        """Testa se a página de detalhes de uma ordem é carregada corretamente."""
        response = self.client.get(f'/ordens/detalhe/{self.ordem.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Ordem de Teste', response.data)
        self.assertIn(b'Descri', response.data)  # "Descrição" com acento
    
    def test_nova_ordem_page(self):
        """Testa se a página de nova ordem é carregada corretamente."""
        response = self.client.get('/ordens/nova')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Nova Ordem de Servi', response.data)  # "Serviço" com acento
    
    def test_criar_ordem(self):
        """Testa a criação de uma nova ordem."""
        # Criar uma imagem de teste
        test_image = BytesIO(b'test image content')
        
        response = self.client.post('/ordens/nova', data={
            'titulo': 'Nova Ordem',
            'descricao': 'Descrição da nova ordem',
            'condominio_id': self.condominio.id,
            'area_id': self.area.id,
            'prioridade': 'Alta',
            'tipo': 'Reparo',
            'foto_inicial': (test_image, 'test.jpg'),
            'observacoes': 'Observações de teste'
        }, follow_redirects=True, content_type='multipart/form-data')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Ordem de servi', response.data)  # "serviço" com acento
        self.assertIn(b'Nova Ordem', response.data)
        
        # Verificar se a ordem foi criada no banco
        ordem = Ordem.query.filter_by(titulo='Nova Ordem').first()
        self.assertIsNotNone(ordem)
        self.assertEqual(ordem.descricao, 'Descrição da nova ordem')
        self.assertEqual(ordem.prioridade, 'Alta')
    
    def test_editar_ordem_page(self):
        """Testa se a página de edição de ordem é carregada corretamente."""
        response = self.client.get(f'/ordens/editar/{self.ordem.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Editar Ordem', response.data)
        self.assertIn(b'Ordem de Teste', response.data)
    
    def test_editar_ordem(self):
        """Testa a edição de uma ordem existente."""
        response = self.client.post(f'/ordens/editar/{self.ordem.id}', data={
            'titulo': 'Ordem Atualizada',
            'descricao': 'Descrição atualizada',
            'condominio_id': self.condominio.id,
            'area_id': self.area.id,
            'prioridade': 'Alta',
            'tipo': 'Reparo',
            'status': 'Em Andamento',
            'observacoes': 'Observações atualizadas'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Ordem atualizada com sucesso', response.data)
        self.assertIn(b'Ordem Atualizada', response.data)
        
        # Verificar se a ordem foi atualizada no banco
        ordem = Ordem.query.get(self.ordem.id)
        self.assertEqual(ordem.titulo, 'Ordem Atualizada')
        self.assertEqual(ordem.descricao, 'Descrição atualizada')
        self.assertEqual(ordem.status, 'Em Andamento')
    
    def test_atualizar_status(self):
        """Testa a atualização de status de uma ordem."""
        response = self.client.post(f'/ordens/atualizar_status/{self.ordem.id}', data={
            'status': 'Concluída',
            'observacao': 'Ordem concluída com sucesso'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Status atualizado com sucesso', response.data)
        
        # Verificar se o status foi atualizado no banco
        ordem = Ordem.query.get(self.ordem.id)
        self.assertEqual(ordem.status, 'Concluída')
        
        # Verificar se o log de status foi criado
        self.assertTrue(len(ordem.status_logs) > 0)
        self.assertEqual(ordem.status_logs[-1].status_novo, 'Concluída')
        self.assertEqual(ordem.status_logs[-1].observacao, 'Ordem concluída com sucesso')
    
    def test_adicionar_comentario(self):
        """Testa a adição de um comentário a uma ordem."""
        response = self.client.post(f'/ordens/detalhe/{self.ordem.id}', data={
            'texto': 'Comentário de teste'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Coment', response.data)  # "Comentário" com acento
        self.assertIn(b'Coment', response.data)  # "Comentário" com acento
        
        # Verificar se o comentário foi adicionado no banco
        ordem = Ordem.query.get(self.ordem.id)
        self.assertTrue(len(ordem.comentarios) > 0)
        self.assertEqual(ordem.comentarios[-1].texto, 'Comentário de teste')
    
    def test_excluir_ordem(self):
        """Testa a exclusão de uma ordem."""
        # Login como administrador para ter permissão de exclusão
        self._login_admin_user()
        
        response = self.client.get(f'/ordens/excluir/{self.ordem.id}', follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Ordem exclu', response.data)  # "excluída" com acento
        
        # Verificar se a ordem foi excluída do banco
        ordem = Ordem.query.get(self.ordem.id)
        self.assertIsNone(ordem)
    
    def test_ordens_concluidas(self):
        """Testa a página de ordens concluídas."""
        # Atualizar status da ordem para concluída
        self.ordem.status = 'Concluída'
        db.session.commit()
        
        response = self.client.get('/ordens/concluidas')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Ordens Conclu', response.data)  # "Concluídas" com acento
        self.assertIn(b'Ordem de Teste', response.data)
    
    def test_filtrar_ordens(self):
        """Testa a filtragem de ordens."""
        response = self.client.get('/ordens/listar?status=Aberta')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Ordem de Teste', response.data)
        
        # Testar filtro que não deve retornar resultados
        response = self.client.get('/ordens/listar?status=Cancelada')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'Ordem de Teste', response.data)
        self.assertIn(b'Nenhuma ordem de servi', response.data)  # "serviço" com acento


if __name__ == '__main__':
    unittest.main()

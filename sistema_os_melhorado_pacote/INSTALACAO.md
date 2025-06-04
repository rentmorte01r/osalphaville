# Guia de Instalação e Uso do Sistema de Ordens de Serviço

## Instruções para Instalação no PyCharm

### 1. Configuração Inicial

1. **Criar um novo projeto no PyCharm**:
   - Abra o PyCharm
   - Selecione "Create New Project"
   - Escolha um local para o projeto
   - Selecione "Python" como tipo de projeto
   - Crie um ambiente virtual (recomendado)

2. **Copiar os arquivos do sistema**:
   - Copie todos os arquivos e pastas do pacote fornecido para a pasta do seu projeto
   - Certifique-se de manter a estrutura de diretórios intacta

### 2. Configuração do Ambiente

1. **Instalar dependências**:
   - Abra o terminal do PyCharm (Alt+F12)
   - Ative o ambiente virtual (se estiver usando)
   - Execute: `pip install -r requirements.txt`

2. **Configurar variáveis de ambiente**:
   - Crie um arquivo `.env` na raiz do projeto (se não existir)
   - Adicione as seguintes variáveis:
     ```
     FLASK_APP=run.py
     FLASK_ENV=development
     SECRET_KEY=sua-chave-secreta-aqui
     DATABASE_URL=sqlite:///app.db
     ```
   - Para usar MySQL em produção, configure:
     ```
     DATABASE_URL=mysql+pymysql://usuario:senha@localhost/sistema_os
     ```

### 3. Inicialização do Banco de Dados

1. **Executar migrações**:
   - No terminal do PyCharm, execute:
     ```
     flask db init
     flask db migrate -m "Migração inicial"
     flask db upgrade
     ```

2. **Criar usuário administrador inicial** (opcional):
   - Execute o script de inicialização:
     ```
     flask shell
     ```
   - No shell, execute:
     ```python
     from app.models.user import User
     from app.models.role import Role
     from app import db
     
     # Criar papel de administrador
     admin_role = Role(name='Admin', description='Administrador do sistema')
     db.session.add(admin_role)
     
     # Criar usuário administrador
     admin = User(
         name='Administrador',
         email='admin@exemplo.com',
         password='Admin@123',
         is_active=True,
         is_admin=True
     )
     admin.roles.append(admin_role)
     db.session.add(admin)
     db.session.commit()
     
     print("Usuário administrador criado com sucesso!")
     exit()
     ```

### 4. Executando a Aplicação

1. **Configurar a execução no PyCharm**:
   - Clique em "Add Configuration" no canto superior direito
   - Clique no "+" e selecione "Python"
   - Configure:
     - Script path: Selecione o arquivo `run.py`
     - Working directory: Diretório raiz do projeto
     - Environment variables: `FLASK_ENV=development;FLASK_DEBUG=True`

2. **Iniciar o servidor**:
   - Clique no botão "Run" (ícone de play verde)
   - O servidor será iniciado em `http://localhost:5000`

3. **Acessar a aplicação**:
   - Abra seu navegador e acesse `http://localhost:5000`
   - Faça login com as credenciais do administrador:
     - Email: `admin@exemplo.com`
     - Senha: `Admin@123`

## Uso do Sistema

### Módulos Principais

1. **Autenticação**:
   - Login/Logout
   - Registro de novos usuários
   - Recuperação de senha
   - Perfil de usuário

2. **Ordens de Serviço**:
   - Painel principal
   - Criação de novas ordens
   - Visualização e edição de ordens
   - Atualização de status
   - Adição de comentários e anexos

3. **Dashboard e Relatórios**:
   - Visualização de estatísticas
   - Geração de relatórios personalizados
   - Exportação em PDF e Excel

4. **Administração**:
   - Gerenciamento de usuários
   - Gerenciamento de condomínios
   - Gerenciamento de áreas
   - Gerenciamento de fornecedores
   - Logs de atividade

### Fluxo de Trabalho Típico

1. **Administrador**:
   - Cadastra condomínios, áreas e fornecedores
   - Aprova novos usuários
   - Atribui papéis e permissões
   - Monitora atividades e gera relatórios

2. **Usuário**:
   - Cria novas ordens de serviço
   - Acompanha o status das ordens
   - Adiciona comentários e anexos
   - Atualiza o status das ordens
   - Visualiza dashboard e relatórios

## Solução de Problemas Comuns

### Erro de Conexão com Banco de Dados

- Verifique se as credenciais no arquivo `.env` estão corretas
- Certifique-se de que o servidor de banco de dados está em execução
- Verifique se o banco de dados especificado existe

### Erro ao Fazer Upload de Arquivos

- Verifique se o diretório `app/static/uploads` existe e tem permissões de escrita
- Certifique-se de que o tamanho do arquivo não excede o limite configurado
- Verifique se o tipo de arquivo é permitido

### Erro ao Executar Migrações

- Certifique-se de que o banco de dados está acessível
- Verifique se você tem permissões para criar tabelas
- Se estiver usando SQLite, verifique se o diretório tem permissões de escrita

## Executando Testes

Para executar os testes automatizados:

1. No terminal do PyCharm, execute:
   ```
   python -m unittest discover tests
   ```

2. Para executar um teste específico:
   ```
   python -m unittest tests.test_auth
   ```

3. Para gerar relatório de cobertura:
   ```
   coverage run -m unittest discover tests
   coverage report
   coverage html  # Gera relatório HTML em htmlcov/
   ```

## Personalização e Extensão

O sistema foi projetado para ser facilmente personalizado e estendido. Consulte a documentação completa no arquivo `README.md` para mais detalhes sobre como adicionar novos tipos de ordens, papéis, permissões e outras customizações.

## Suporte

Se encontrar problemas ou tiver dúvidas, consulte a documentação completa ou entre em contato com o desenvolvedor.

Aproveite o seu novo Sistema de Ordens de Serviço!

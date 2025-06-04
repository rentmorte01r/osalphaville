# Documentação do Sistema de Ordens de Serviço

## Visão Geral

O Sistema de Ordens de Serviço é uma aplicação web completa desenvolvida em Flask para gerenciamento de ordens de serviço em condomínios. O sistema permite o cadastro de usuários, condomínios, áreas, fornecedores e ordens de serviço, com controle de acesso baseado em papéis e permissões.

## Características Principais

- **Arquitetura Modular**: Sistema organizado em blueprints para melhor manutenção e escalabilidade
- **Autenticação Segura**: Login, registro e recuperação de senha com proteções contra ataques comuns
- **Controle de Acesso**: Sistema de permissões baseado em papéis para diferentes níveis de usuários
- **Gestão de Ordens**: Criação, edição, acompanhamento e conclusão de ordens de serviço
- **Dashboard e Relatórios**: Visualização de estatísticas e geração de relatórios personalizados
- **Interface Responsiva**: Design adaptável para desktop e dispositivos móveis
- **Segurança Avançada**: Proteções contra CSRF, XSS, injeção SQL e outros ataques comuns
- **Logs e Auditoria**: Registro detalhado de atividades para auditoria e troubleshooting

## Requisitos do Sistema

- Python 3.8 ou superior
- MySQL 5.7 ou superior (recomendado para produção)
- SQLite (para desenvolvimento)
- Bibliotecas Python listadas em requirements.txt

## Estrutura do Projeto

```
sistema_os_melhorado/
├── app/                      # Diretório principal da aplicação
│   ├── __init__.py           # Inicialização da aplicação Flask
│   ├── config.py             # Configurações para diferentes ambientes
│   ├── extensions.py         # Extensões Flask (SQLAlchemy, Login, etc.)
│   ├── admin/                # Blueprint de administração
│   ├── auth/                 # Blueprint de autenticação
│   ├── dashboard/            # Blueprint de dashboard
│   ├── ordens/               # Blueprint de ordens de serviço
│   ├── api/                  # Blueprint de API REST
│   ├── models/               # Modelos de dados
│   ├── static/               # Arquivos estáticos (CSS, JS, imagens)
│   ├── templates/            # Templates HTML
│   └── utils/                # Utilitários e funções auxiliares
├── migrations/               # Migrações do banco de dados
├── tests/                    # Testes automatizados
├── logs/                     # Logs da aplicação
├── run.py                    # Script para executar a aplicação
└── requirements.txt          # Dependências do projeto
```

## Instalação e Configuração

### 1. Configuração do Ambiente

1. Clone o repositório ou copie os arquivos para seu ambiente PyCharm
2. Crie um ambiente virtual:
   ```bash
   python -m venv venv
   ```
3. Ative o ambiente virtual:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
4. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

### 2. Configuração do Banco de Dados

1. Configure as variáveis de ambiente no arquivo `.env`:
   ```
   FLASK_APP=run.py
   FLASK_ENV=development
   SECRET_KEY=sua-chave-secreta
   DATABASE_URL=mysql+pymysql://usuario:senha@localhost/sistema_os
   ```

2. Inicialize o banco de dados:
   ```bash
   flask db init
   flask db migrate -m "Migração inicial"
   flask db upgrade
   ```

### 3. Execução da Aplicação

1. Execute a aplicação:
   ```bash
   flask run
   ```
   ou
   ```bash
   python run.py
   ```

2. Acesse a aplicação em `http://localhost:5000`

## Execução dos Testes

Para executar os testes automatizados:

```bash
python -m unittest discover tests
```

Para executar um teste específico:

```bash
python -m unittest tests.test_auth
```

## Módulos Principais

### Autenticação (auth)

O módulo de autenticação gerencia login, registro, recuperação de senha e perfil de usuário.

**Rotas principais:**
- `/auth/login`: Login de usuários
- `/auth/register`: Registro de novos usuários
- `/auth/logout`: Logout de usuários
- `/auth/reset_password_request`: Solicitação de redefinição de senha
- `/auth/reset_password/<token>`: Redefinição de senha com token
- `/auth/profile`: Perfil do usuário

### Ordens de Serviço (ordens)

O módulo de ordens gerencia o ciclo de vida completo das ordens de serviço.

**Rotas principais:**
- `/ordens/painel`: Painel principal com visão geral
- `/ordens/listar`: Listagem de ordens de serviço
- `/ordens/nova`: Criação de nova ordem
- `/ordens/detalhe/<id>`: Detalhes de uma ordem
- `/ordens/editar/<id>`: Edição de uma ordem
- `/ordens/concluidas`: Listagem de ordens concluídas

### Dashboard e Relatórios (dashboard)

O módulo de dashboard fornece visualizações e relatórios sobre as ordens de serviço.

**Rotas principais:**
- `/dashboard/`: Dashboard principal com gráficos e estatísticas
- `/dashboard/relatorios`: Geração de relatórios personalizados
- `/dashboard/exportar_pdf`: Exportação de relatórios em PDF
- `/dashboard/exportar_excel`: Exportação de relatórios em Excel

### Administração (admin)

O módulo de administração permite gerenciar usuários, condomínios, áreas e configurações do sistema.

**Rotas principais:**
- `/admin/dashboard`: Painel administrativo
- `/admin/users`: Gerenciamento de usuários
- `/admin/roles`: Gerenciamento de papéis e permissões
- `/admin/condominios`: Gerenciamento de condomínios
- `/admin/areas`: Gerenciamento de áreas
- `/admin/fornecedores`: Gerenciamento de fornecedores
- `/admin/relatorios`: Relatórios administrativos
- `/admin/activity_logs`: Logs de atividade do sistema

## Segurança

O sistema implementa diversas medidas de segurança:

- **Proteção CSRF**: Tokens CSRF em todos os formulários
- **Proteção XSS**: Sanitização de entrada e escape de saída
- **Validação de Uploads**: Verificação de tipos e tamanhos de arquivos
- **Controle de Acesso**: Verificação de permissões em todas as rotas
- **Senhas Seguras**: Hashing de senhas com algoritmos modernos
- **Headers de Segurança**: Headers HTTP para proteção contra ataques comuns
- **Rate Limiting**: Limitação de requisições para prevenir ataques de força bruta
- **Logs de Segurança**: Registro de tentativas de acesso e atividades suspeitas

## Customização

### Adicionando Novos Tipos de Ordens

1. Edite o arquivo `app/models/ordem.py` e adicione novos tipos à lista `TIPOS_ORDEM`
2. Atualize os formulários em `app/ordens/forms.py` para incluir os novos tipos
3. Execute uma migração do banco de dados para aplicar as alterações

### Adicionando Novos Papéis e Permissões

1. Edite o arquivo `app/models/role.py` para adicionar novos papéis
2. Atualize o arquivo `app/models/permission.py` para adicionar novas permissões
3. Associe as permissões aos papéis no arquivo `app/models/role.py`
4. Execute uma migração do banco de dados para aplicar as alterações

## Solução de Problemas

### Problemas de Login

- Verifique se o usuário está ativo no banco de dados
- Verifique se o email e senha estão corretos
- Limpe os cookies do navegador e tente novamente

### Erros de Banco de Dados

- Verifique a conexão com o banco de dados
- Verifique se todas as migrações foram aplicadas
- Consulte os logs em `logs/app.log` para mais detalhes

### Problemas de Upload de Arquivos

- Verifique se o diretório `app/static/uploads` tem permissões de escrita
- Verifique se o tamanho do arquivo não excede o limite configurado
- Verifique se o tipo de arquivo é permitido

## Contribuição

Para contribuir com o projeto:

1. Crie um fork do repositório
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Faça commit das suas alterações (`git commit -m 'Adiciona nova feature'`)
4. Faça push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para mais detalhes.

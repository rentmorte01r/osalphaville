# Estrutura Modular do Sistema de OS

## Visão Geral da Nova Arquitetura

A nova estrutura do sistema de OS seguirá uma arquitetura modular baseada em blueprints do Flask, com separação clara de responsabilidades e organização por funcionalidades. Isso facilitará a manutenção, testabilidade e escalabilidade do sistema.

## Estrutura de Diretórios

```
/sistema_os
├── app/                      # Pacote principal da aplicação
│   ├── __init__.py           # Inicialização da aplicação
│   ├── config.py             # Configurações da aplicação
│   ├── extensions.py         # Extensões Flask (db, login, etc.)
│   ├── models/               # Modelos de dados
│   │   ├── __init__.py
│   │   ├── user.py           # Modelo de usuário
│   │   ├── ordem.py          # Modelo de ordem de serviço
│   │   ├── condominio.py     # Modelo de condomínio
│   │   └── role.py           # Modelo de papéis e permissões
│   ├── auth/                 # Blueprint de autenticação
│   │   ├── __init__.py
│   │   ├── routes.py         # Rotas de autenticação
│   │   ├── forms.py          # Formulários de autenticação
│   │   └── utils.py          # Utilitários de autenticação
│   ├── admin/                # Blueprint de administração
│   │   ├── __init__.py
│   │   ├── routes.py         # Rotas de administração
│   │   ├── forms.py          # Formulários de administração
│   │   └── utils.py          # Utilitários de administração
│   ├── ordens/               # Blueprint de ordens de serviço
│   │   ├── __init__.py
│   │   ├── routes.py         # Rotas de ordens
│   │   ├── forms.py          # Formulários de ordens
│   │   └── utils.py          # Utilitários de ordens
│   ├── dashboard/            # Blueprint de dashboard
│   │   ├── __init__.py
│   │   ├── routes.py         # Rotas de dashboard
│   │   └── utils.py          # Utilitários de dashboard
│   ├── api/                  # Blueprint de API (opcional)
│   │   ├── __init__.py
│   │   └── routes.py         # Rotas de API
│   ├── utils/                # Utilitários gerais
│   │   ├── __init__.py
│   │   ├── email.py          # Funções de email
│   │   ├── security.py       # Funções de segurança
│   │   ├── uploads.py        # Funções de upload
│   │   └── decorators.py     # Decoradores personalizados
│   ├── static/               # Arquivos estáticos
│   │   ├── css/              # Estilos CSS
│   │   ├── js/               # Scripts JavaScript
│   │   ├── images/           # Imagens
│   │   └── uploads/          # Uploads de usuários
│   └── templates/            # Templates HTML
│       ├── base.html         # Template base
│       ├── auth/             # Templates de autenticação
│       ├── admin/            # Templates de administração
│       ├── ordens/           # Templates de ordens
│       ├── dashboard/        # Templates de dashboard
│       └── errors/           # Templates de erro
├── migrations/               # Migrações de banco de dados
├── tests/                    # Testes automatizados
│   ├── __init__.py
│   ├── conftest.py           # Configurações de teste
│   ├── test_auth.py          # Testes de autenticação
│   ├── test_admin.py         # Testes de administração
│   ├── test_ordens.py        # Testes de ordens
│   └── test_models.py        # Testes de modelos
├── .env.example              # Exemplo de variáveis de ambiente
├── .gitignore                # Arquivos a ignorar no Git
├── requirements.txt          # Dependências do projeto
├── run.py                    # Script para executar a aplicação
└── README.md                 # Documentação do projeto
```

## Principais Melhorias Arquiteturais

1. **Modularização com Blueprints**
   - Separação de funcionalidades em blueprints independentes
   - Cada blueprint com suas próprias rotas, formulários e utilitários

2. **Separação de Responsabilidades**
   - Modelos focados apenas na representação de dados
   - Formulários para validação de entrada
   - Utilitários para lógica de negócio reutilizável
   - Rotas para coordenação e apresentação

3. **Configuração Flexível**
   - Configurações baseadas em classes para diferentes ambientes
   - Carregamento seguro de variáveis de ambiente

4. **Extensões Centralizadas**
   - Inicialização de extensões Flask em um único local
   - Evita dependências circulares

5. **Estrutura de Testes**
   - Organização de testes por funcionalidade
   - Fixtures reutilizáveis para configuração de testes

## Padrões de Código

1. **Nomenclatura**
   - Nomes de arquivos e variáveis em snake_case
   - Nomes de classes em PascalCase
   - Constantes em UPPER_CASE

2. **Documentação**
   - Docstrings para todas as funções, classes e módulos
   - Comentários explicativos para código complexo

3. **Importações**
   - Importações agrupadas por tipo (stdlib, terceiros, locais)
   - Evitar importações circulares

4. **Tratamento de Erros**
   - Uso consistente de try/except
   - Mensagens de erro claras e informativas

## Fluxo de Dados

1. **Autenticação**
   - Login/registro de usuários
   - Verificação de permissões baseada em roles

2. **Ordens de Serviço**
   - Criação, edição e visualização de ordens
   - Fluxo de status (aberta, em andamento, concluída)
   - Upload e gerenciamento de arquivos

3. **Dashboard**
   - Visualização de estatísticas
   - Filtros por data, condomínio e status
   - Gráficos dinâmicos baseados em dados reais

4. **Administração**
   - Gerenciamento de usuários, roles e permissões
   - Configuração de condomínios e administradoras
   - Relatórios administrativos

## Segurança

1. **Autenticação e Autorização**
   - Senhas com hash bcrypt
   - Proteção CSRF em todos os formulários
   - Verificação de permissões em todas as rotas

2. **Proteção de Dados**
   - Validação rigorosa de entradas
   - Sanitização de saídas para prevenir XSS
   - Proteção contra SQL Injection via ORM

3. **Uploads Seguros**
   - Validação de tipo MIME
   - Limitação de tamanho
   - Nomes de arquivo seguros

## Performance

1. **Otimização de Consultas**
   - Eager loading para evitar N+1
   - Paginação para grandes conjuntos de dados
   - Índices adequados no banco de dados

2. **Caching**
   - Cache de consultas frequentes
   - Cache de templates

3. **Recursos Estáticos**
   - Minificação de CSS e JavaScript
   - Compressão de respostas

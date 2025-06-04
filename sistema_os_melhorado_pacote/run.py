"""
Script principal para execução da aplicação.
Este arquivo é o ponto de entrada para iniciar o servidor Flask.
"""
import os
from app import create_app
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Determinar o ambiente de execução
env = os.environ.get('FLASK_ENV', 'development')

# Criar a aplicação Flask com a configuração apropriada
app = create_app(env)

if __name__ == '__main__':
    # Configurações do servidor de desenvolvimento
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Iniciar o servidor
    app.run(host=host, port=port, debug=debug)

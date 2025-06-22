from flask import Flask, jsonify
from flask_cors import CORS
# Importa o blueprint de alunos
from routes.alunos import alunos_bp 
# Importa o novo blueprint de autenticação
from routes.auth import auth_bp 

import logging
from logging.handlers import RotatingFileHandler
import os
import mysql.connector

def create_app():
    """Factory function para criar e configurar a aplicação Flask"""
    app = Flask(__name__)
    
    # Configurações básicas da aplicação
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY') or 'dev-key-segura',
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,   # Limite de 16MB para uploads
        JSON_SORT_KEYS=False,   # Mantém ordem dos campos no JSON (mais legível para depuração)
    )
    
    # Configura CORS para permitir requisições do seu frontend Tkinter e outros
    # Adicione as rotas para o Blueprint de autenticação também.
    CORS(app, resources={
        r"/api/v1/alunos/*": {  
            "origins": ["http://localhost:3000", "https://seusite.com"], # Exemplo para frontend web
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "allow_headers": ["Content-Type", "Authorization"] # Necessário para enviar o token
        },
        r"/api/v1/auth/*": { # Permite CORS para as rotas de autenticação
            "origins": ["http://localhost:3000", "https://seusite.com"],
            "methods": ["POST"], # Login e registro são geralmente POSTs
            "allow_headers": ["Content-Type"] # Não precisa de Authorization para login/register
        }
    })
    
    # Configuração do sistema de logging
    configure_logging(app)
    
    # Registra os Blueprints na aplicação principal
    register_blueprints(app)

    # Rota raiz simples para verificar se o servidor está ativo
    @app.route('/')
    def index():
        return "Bem-vindo à API da Escola!", 200

    # Rota de teste simples para verificar conectividade básica do Flask
    @app.route('/test')
    def test_route():
        """
        Rota de teste simples para verificar conectividade básica do Flask.
        Se esta rota retornar 404, há um problema com a inicialização da aplicação Flask.
        """
        print("A rota /test foi acedida!") # Mensagem de depuração
        return "Conexão de teste bem-sucedida com o Flask!", 200
    
    @app.route('/db_test')
    def db_test_route():
        """
        Rota para testar a conexão com o banco de dados diretamente do Flask.
        Útil para depurar problemas de conectividade com o MySQL.
        """
        try:
            db_host = os.environ.get("DB_HOST", "db") 
            db_user = os.environ.get("DB_USER", "user")
            db_password = os.environ.get("DB_PASSWORD", "senha")
            db_name = os.environ.get("DB_NAME", "escola")

            conn = mysql.connector.connect(
                host=db_host,
                user=db_user,
                password=db_password,
                database=db_name
            )
            conn.close()
            print("Conexão com o banco de dados bem-sucedida!") 
            return jsonify({"message": "Conexão com o banco de dados bem-sucedida!"}), 200
        except mysql.connector.Error as err:
            app.logger.error(f"Erro MySQL ao testar DB: {err}")
            print(f"Erro MySQL ao testar DB: {err}") 
            return jsonify({"message": f"Erro ao conectar ao banco de dados: {err}", "details": str(err)}), 500
        except Exception as e:
            app.logger.error(f"Erro inesperado ao testar DB: {e}")
            print(f"Erro inesperado ao testar DB: {e}") 
            return jsonify({"message": f"Erro inesperado ao testar o banco de dados: {e}", "details": str(e)}), 500
    
    print("Aplicação Flask criada com sucesso.") 
    
    return app

def configure_logging(app):
    """Configura o sistema de logging da aplicação"""
    # Cria o diretório 'logs' se não existir
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    # Handler para arquivo de log (rotação diária, mantém 7 dias)
    file_handler = RotatingFileHandler(
        'logs/api.log',
        maxBytes=1024 * 1024 * 10,   # 10MB
        backupCount=7,
        encoding='utf-8'
    )
    # Define o formato das mensagens de log
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO) # Define o nível mínimo de log
    
    # Remove handlers padrão para evitar logs duplicados
    for handler in app.logger.handlers[:]:
        app.logger.removeHandler(handler)
    
    # Adiciona os nossos handlers configurados
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO) # Define o nível de log da aplicação
    
    app.logger.info('Aplicação iniciada')

def register_blueprints(app):
    """Registra todos os blueprints da aplicação"""
    app.register_blueprint(alunos_bp) 
    app.register_blueprint(auth_bp) # Registra o novo blueprint de autenticação
    
# Cria a instância da aplicação Flask usando a factory function
app = create_app()

if __name__ == '__main__':
    # Configurações adicionais para o ambiente de desenvolvimento
    app.config['DEBUG'] = True # Ativa o modo de depuração (recarrega o servidor ao salvar mudanças)
    app.config['TEMPLATES_AUTO_RELOAD'] = True # Recarrega templates automaticamente

    print("Iniciando o servidor Flask...")

    # Inicia o servidor Flask
    # host '0.0.0.0' permite acesso de qualquer IP (útil em Docker)
    # port 5000 é a porta padrão para o Flask
    # threaded=True permite que o servidor lide com múltiplas requisições simultaneamente
    app.run(
        host=os.environ.get('FLASK_HOST', '0.0.0.0'),
        port=int(os.environ.get('FLASK_PORT', 5000)),
        threaded=True
    )

#docker-compose logs -f backend
import os
from flask import Blueprint, request, jsonify
import mysql.connector
import bcrypt
import uuid
from datetime import datetime, timedelta
import logging
from functools import wraps # Importado para uso com decoradores

logger = logging.getLogger(__name__)

# Define o Blueprint para as rotas de autenticação
auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

# Função de conexão com o banco de dados (reutilizada de outros módulos)
def db_connection():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "db"), # 'db' é o nome do serviço no docker-compose
        user=os.environ.get("DB_USER", "user"),
        password=os.environ.get("DB_PASSWORD", "senha"),
        database=os.environ.get("DB_NAME", "escola")
    )

@auth_bp.route('/register', methods=['POST'])
def register_user():
    """
    Rota para registar um novo utilizador.
    Em um ambiente de produção, esta rota seria restrita apenas a administradores.
    Para esta demonstração, pode ser usada para criar o primeiro admin.
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'user') # Padrão para 'user', pode ser 'admin'

    if not username or not password:
        return jsonify({"message": "Nome de utilizador e senha são obrigatórios"}), 400

    # Hashing da senha usando bcrypt
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    conn = None
    try:
        conn = db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                (username, hashed_password, role)
            )
            conn.commit()
            logger.info(f"Utilizador '{username}' registado com sucesso com a função '{role}'.")
            return jsonify({"message": "Utilizador registado com sucesso"}), 201
    except mysql.connector.IntegrityError:
        # Erro de integridade ocorre se o username já existir (UNIQUE constraint)
        return jsonify({"message": "Nome de utilizador já existe"}), 409
    except Exception as e:
        logger.exception("Erro ao registar utilizador:")
        return jsonify({"message": "Erro interno ao registar utilizador"}), 500
    finally:
        if conn:
            conn.close()

@auth_bp.route('/login', methods=['POST'])
def login_user():
    """
    Rota para autenticar um utilizador e emitir um token de sessão.
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"message": "Nome de utilizador e senha são obrigatórios"}), 400

    conn = None
    try:
        conn = db_connection()
        with conn.cursor(dictionary=True) as cursor:
            # Busca o utilizador pelo username
            cursor.execute("SELECT id, username, password_hash, role FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()

            # Verifica se o utilizador existe e se a senha está correta
            if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                # Gerar um token de sessão único
                token = str(uuid.uuid4())
                # Definir expiração do token (ex: 1 hora a partir de agora)
                token_expiry = datetime.now() + timedelta(hours=1)

                # Armazenar o token e a expiração no banco de dados para validação futura
                cursor.execute(
                    "UPDATE users SET token = %s, token_expiry = %s WHERE id = %s",
                    (token, token_expiry, user['id'])
                )
                conn.commit()

                logger.info(f"Utilizador '{username}' autenticado com sucesso. Token gerado.")
                return jsonify({
                    "message": "Login bem-sucedido",
                    "token": token,
                    "expires_at": token_expiry.isoformat(), # Formato ISO 8601
                    "role": user['role']
                }), 200
            else:
                return jsonify({"message": "Nome de utilizador ou senha inválidos"}), 401
    except Exception as e:
        logger.exception("Erro durante o login:")
        return jsonify({"message": "Erro interno durante o login"}), 500
    finally:
        if conn:
            conn.close()

@auth_bp.route('/logout', methods=['POST'])
def logout_user():
    """
    Rota para invalidar o token de sessão de um utilizador.
    O token deve ser enviado no cabeçalho 'Authorization: Bearer <token>'.
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"message": "Token de autenticação ausente ou mal formatado"}), 401
    
    token = auth_header.split(' ')[1] # Extrai o token da string "Bearer <token>"

    conn = None
    try:
        conn = db_connection()
        with conn.cursor() as cursor:
            # Limpa o token e a expiração do utilizador correspondente no banco de dados
            cursor.execute(
                "UPDATE users SET token = NULL, token_expiry = NULL WHERE token = %s",
                (token,)
            )
            conn.commit()
            if cursor.rowcount > 0: # Verifica se alguma linha foi afetada (token encontrado e invalidado)
                logger.info("Token invalidado com sucesso.")
                return jsonify({"message": "Logout bem-sucedido"}), 200
            else:
                return jsonify({"message": "Token inválido ou já expirado"}), 401
    except Exception as e:
        logger.exception("Erro durante o logout:")
        return jsonify({"message": "Erro interno durante o logout"}), 500
    finally:
        if conn:
            conn.close()

def token_required(f):
    """
    Decorador para proteger rotas. Verifica a presença e validade do token de autenticação.
    Adiciona 'user_id', 'username', e 'user_role' ao objeto 'request' se o token for válido.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"message": "Token de autenticação é obrigatório"}), 401
        
        token = auth_header.split(' ')[1]
        
        conn = None
        try:
            conn = db_connection()
            with conn.cursor(dictionary=True) as cursor:
                # Busca o utilizador pelo token válido e não expirado
                cursor.execute(
                    "SELECT id, username, role, token_expiry FROM users WHERE token = %s",
                    (token,)
                )
                user = cursor.fetchone()

                if not user:
                    return jsonify({"message": "Token inválido ou não encontrado"}), 401
                
                # Verifica a expiração do token
                if user['token_expiry'] and user['token_expiry'] < datetime.now():
                    # Invalida o token expirado no BD
                    cursor.execute("UPDATE users SET token = NULL, token_expiry = NULL WHERE id = %s", (user['id'],))
                    conn.commit()
                    return jsonify({"message": "Token expirado. Por favor, faça login novamente."}), 401

                # Adiciona as informações do utilizador ao objeto request para uso posterior nas rotas protegidas
                request.user_id = user['id']
                request.user_role = user['role']
                request.username = user['username']
                
                return f(*args, **kwargs)
        except Exception as e:
            logger.exception("Erro na validação do token:")
            return jsonify({"message": "Erro interno na validação do token"}), 500
        finally:
            if conn:
                conn.close()
    return decorated

def admin_required(f):
    """
    Decorador para rotas que exigem permissões de administrador.
    Deve ser usado APÓS @token_required.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Verifica se 'user_role' foi definido pelo decorador 'token_required' e se é 'admin'
        if not hasattr(request, 'user_role') or request.user_role != 'admin':
            return jsonify({"message": "Acesso negado: Requer privilégios de administrador"}), 403
        return f(*args, **kwargs)
    return decorated


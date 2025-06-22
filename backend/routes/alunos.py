import os
from flask import Blueprint, request, jsonify, abort
from werkzeug.exceptions import HTTPException
import logging
import mysql.connector

# Importa os decoradores de autenticação do novo módulo auth.py
from routes.auth import token_required, admin_required 

# Configuração básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Blueprint para as rotas de alunos
# O url_prefix definido aqui será usado no app.py ao registrar o blueprint
alunos_bp = Blueprint('alunos', __name__, url_prefix='/api/v1/alunos/')

# Configuração do banco de dados: lê do ambiente, com valores padrão para Docker Compose
def db_connection():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "db"), # 'db' é o nome do serviço no docker-compose
        user=os.environ.get("DB_USER", "user"),
        password=os.environ.get("DB_PASSWORD", "senha"),
        database=os.environ.get("DB_NAME", "escola")
    )

@alunos_bp.errorhandler(HTTPException)
def handle_exception(e):
    """Handler global para exceções HTTP dentro do blueprint de alunos"""
    logger.error(f"Erro HTTP {e.code}: {e.description}")
    return jsonify({
        "sucesso": False,
        "mensagem": e.description,
        "codigo": e.code
    }), e.code

@alunos_bp.errorhandler(Exception)
def handle_unexpected_error(e):
    """Handler para erros inesperados dentro do blueprint de alunos"""
    logger.exception("Erro inesperado no blueprint de alunos")
    return jsonify({
        "sucesso": False,
        "mensagem": "Ocorreu um erro interno no servidor",
        "codigo": 500
    }), 500

def validar_aluno(data, operacao='create'):
    """Valida os dados do aluno conforme a operação (create/update)"""
    campos_obrigatorios = ['nome', 'matricula', 'curso', 'email']
    
    if not data:
        abort(400, description="Dados do aluno não fornecidos")
    
    if operacao == 'create':
        for campo in campos_obrigatorios:
            if campo not in data or not str(data[campo]).strip():
                abort(400, description=f"Campo '{campo}' é obrigatório")
    
    # Validações específicas para campos se eles estiverem presentes
    if 'email' in data and '@' not in data['email']:
        abort(400, description="Email inválido")
    
    if 'matricula' in data and not str(data['matricula']).isdigit():
        abort(400, description="Matrícula deve conter apenas números")

# Rota para listar todos os alunos (pode ser pública ou exigir token, dependendo da necessidade)
# Para esta demo, vamos exigir token para todas as operações CRUD
@alunos_bp.route('/', methods=['GET'])
@token_required # Agora exige um token válido para listar alunos
def listar_alunos():
    """Lista todos os alunos com paginação."""
    conn = None 
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        offset = (page - 1) * per_page

        conn = db_connection()
        with conn.cursor(dictionary=True) as cursor:
            # Query para os dados dos alunos
            cursor.execute("""
                SELECT id, nome, matricula, curso, email 
                FROM alunos 
                LIMIT %s OFFSET %s
            """, (per_page, offset))
            alunos = cursor.fetchall()

            # Query para o total de alunos (para paginação)
            cursor.execute("SELECT COUNT(*) as total FROM alunos")
            total = cursor.fetchone()['total']

            return jsonify({
                'sucesso': True,
                'alunos': alunos,
                'total': total,
                'pagina': page,
                'por_pagina': per_page
            }), 200
            
    except mysql.connector.Error as err:
        logger.error(f"Erro MySQL ao listar alunos: {err}")
        abort(500, description=f"Erro no banco de dados ao listar alunos: {err}")
    except Exception as e:
        logger.exception("Erro inesperado ao listar alunos")
        abort(500, description="Erro ao listar alunos")
    finally:
        if conn:
            conn.close()

# Rota para cadastrar um novo aluno (exige token e privilégios de admin)
@alunos_bp.route('/', methods=['POST'])
@token_required
@admin_required # Apenas administradores podem cadastrar
def cadastrar_aluno():
    """Cadastra um novo aluno."""
    conn = None
    try:
        data = request.get_json()
        validar_aluno(data, 'create') # Valida dados para criação
        
        conn = db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO alunos (nome, matricula, curso, email) 
                VALUES (%s, %s, %s, %s)
            """, (
                data['nome'].strip(),
                data['matricula'].strip(),
                data['curso'].strip(),
                data['email'].strip().lower()
            ))
            aluno_id = cursor.lastrowid
            conn.commit()
            
            logger.info(f"Aluno cadastrado com ID: {aluno_id}")
            return jsonify({
                'sucesso': True,
                'mensagem': 'Aluno cadastrado com sucesso',
                'id': aluno_id
            }), 201
            
    except mysql.connector.IntegrityError as e:
        logger.error(f"Erro de integridade ao cadastrar aluno: {str(e)}")
        abort(400, description="Matrícula ou email já cadastrados")
    except mysql.connector.Error as err:
        logger.error(f"Erro MySQL ao cadastrar aluno: {err}")
        abort(500, description=f"Erro no banco de dados ao cadastrar aluno: {err}")
    except Exception as e:
        logger.exception("Erro inesperado ao cadastrar aluno")
        abort(500, description="Erro ao cadastrar aluno")
    finally:
        if conn:
            conn.close()

# Rota para obter detalhes de um aluno específico (exige token)
@alunos_bp.route('/<int:id>', methods=['GET'])
@token_required 
def obter_aluno(id):
    """Obtém detalhes de um aluno específico."""
    conn = None
    try:
        conn = db_connection()
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT id, nome, matricula, curso, email 
                FROM alunos 
                WHERE id = %s
            """, (id,))
            aluno = cursor.fetchone()
            
            if not aluno:
                abort(404, description="Aluno não encontrado")
                
            return jsonify({
                'sucesso': True,
                'aluno': aluno
            }), 200
            
    except mysql.connector.Error as err:
        logger.error(f"Erro MySQL ao obter aluno {id}: {err}")
        abort(500, description=f"Erro no banco de dados ao obter aluno: {err}")
    except Exception as e:
        logger.exception(f"Erro inesperado ao obter aluno {id}")
        abort(500, description="Erro ao obter aluno")
    finally:
        if conn:
            conn.close()

# Rota para atualizar os dados de um aluno (exige token e privilégios de admin)
@alunos_bp.route('/<int:id>', methods=['PUT'])
@token_required
@admin_required # Apenas administradores podem editar
def editar_aluno(id):
    """Atualiza os dados de um aluno."""
    conn = None
    try:
        data = request.get_json()
        validar_aluno(data, 'update') # Valida dados para atualização
        
        conn = db_connection()
        with conn.cursor() as cursor:
            # Verifica se o aluno existe
            cursor.execute("SELECT id FROM alunos WHERE id = %s", (id,))
            if not cursor.fetchone():
                abort(404, description="Aluno não encontrado")
            
            # Constrói a query de atualização dinamicamente
            campos = []
            valores = []
            
            # Itera sobre os campos esperados e adiciona-os à query se estiverem nos dados recebidos
            for campo in ['nome', 'matricula', 'curso', 'email']:
                if campo in data:
                    campos.append(f"{campo} = %s")
                    valores.append(data[campo].strip())
            
            if not campos:
                abort(400, description="Nenhum dado fornecido para atualização")
            
            valores.append(id) # Adiciona o ID para a cláusula WHERE
            query = f"UPDATE alunos SET {', '.join(campos)} WHERE id = %s"
            
            cursor.execute(query, valores)
            conn.commit()
            
            logger.info(f"Aluno {id} atualizado")
            return jsonify({
                'sucesso': True,
                'mensagem': 'Aluno atualizado com sucesso'
            }), 200
            
    except mysql.connector.IntegrityError as e:
        logger.error(f"Erro de integridade ao atualizar aluno: {str(e)}")
        abort(400, description="Matrícula ou email já cadastrados")
    except mysql.connector.Error as err:
        logger.error(f"Erro MySQL ao atualizar aluno {id}: {err}")
        abort(500, description=f"Erro no banco de dados ao atualizar aluno: {err}")
    except Exception as e:
        logger.exception(f"Erro inesperado ao atualizar aluno {id}")
        abort(500, description="Erro ao atualizar aluno")
    finally:
        if conn:
            conn.close()

# Rota para remover um aluno do sistema (exige token e privilégios de admin)
@alunos_bp.route('/<int:id>', methods=['DELETE'])
@token_required
@admin_required # Apenas administradores podem excluir
def excluir_aluno(id):
    """Remove um aluno do sistema."""
    conn = None
    try:
        conn = db_connection()
        with conn.cursor() as cursor:
            # Verifica se o aluno existe antes de tentar excluir
            cursor.execute("SELECT id FROM alunos WHERE id = %s", (id,))
            if not cursor.fetchone():
                abort(404, description="Aluno não encontrado")
            
            cursor.execute("DELETE FROM alunos WHERE id = %s", (id,))
            conn.commit()
            
            logger.info(f"Aluno {id} removido")
            return jsonify({
                'sucesso': True,
                'mensagem': 'Aluno excluído com sucesso'
            }), 200
            
    except mysql.connector.Error as err:
        logger.error(f"Erro MySQL ao excluir aluno {id}: {err}")
        abort(500, description=f"Erro no banco de dados ao excluir aluno: {err}")
    except Exception as e:
        logger.exception(f"Erro inesperado ao excluir aluno {id}")
        abort(500, description="Erro ao excluir aluno")
    finally:
        if conn:
            conn.close()

import bcrypt

# A senha que você deseja usar para o seu utilizador 'admin'.
# É crucial que esta seja a senha que você digitará na tela de login da sua app.
password_to_hash = b'admin' # A senha 'admin' deve ser uma sequência de bytes

# Gera um 'salt' (valor aleatório) e depois gera o hash da senha usando bcrypt.
# O 'salt' é parte integrante do hash e garante que senhas iguais tenham hashes diferentes.
hashed_password = bcrypt.hashpw(password_to_hash, bcrypt.gensalt())

# Decodifica o hash de bytes para uma string UTF-8 para que possa ser armazenado no banco de dados.
print("COPIE ESTE HASH INTEIRO E COLE NO CAMPO 'password_hash' DA TABELA 'users':")
print(hashed_password.decode('utf-8'))
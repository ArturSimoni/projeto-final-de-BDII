📚 Projeto de Gerenciamento de Alunos - API RESTful + Cliente Desktop
🗓️ Data de Apresentação: 23/06/2025
📘 Disciplina: Banco de Dados II
👨‍🏫 Objetivo: Criar um sistema completo para gerenciar alunos, com API segura e interface gráfica.

🎯 Objetivos do Projeto
Este projeto foi desenvolvido como parte da atividade prática da disciplina de Banco de Dados II. O principal objetivo foi montar um ambiente com banco de dados, API e uma aplicação cliente funcional. Também foi solicitado que fossem implementadas melhorias, como autenticação e controle de acesso.

Principais entregas:
✅ Configurar e rodar o servidor web e banco de dados.

✅ Criar uma API RESTful para o gerenciamento de alunos.

✅ Melhorar a API com autenticação e autorização (RBAC).

✅ Desenvolver um cliente desktop simples para consumir a API.

🛠️ Tecnologias Utilizadas
Backend (API RESTful)
Python 3.x – linguagem principal.

Flask – microframework para criação da API.

flask-cors – para liberar acesso da API a outros domínios.

mysql-connector-python – conexão entre Python e MySQL.

bcrypt – para criptografar senhas com segurança.

uuid – para gerar tokens simples de autenticação.

Banco de Dados
MySQL 8 – banco de dados relacional.

phpMyAdmin – ferramenta web para gerenciar o MySQL (usada via Docker).

Containerização
Docker – para isolar os ambientes da API e do banco.

Docker Compose – para subir os serviços juntos de forma organizada.

Cliente Desktop
Python 3.x

Tkinter – para criar a interface gráfica.

requests – para fazer chamadas HTTP para a API.

Outros
Logging – para registrar atividades e possíveis erros da API.

🚀 Como Funciona
O Docker sobe o MySQL e a API Flask.

A API se conecta ao banco e expõe rotas para cadastro, login, listagem e alteração de alunos.

O cliente em Tkinter permite usar a aplicação de forma gráfica, sem precisar abrir o navegador ou terminal.

O sistema possui autenticação com hash de senha e controle de permissões baseado em papéis (admin, usuário comum etc).

💡 Melhorias Implementadas
🔐 Autenticação segura com bcrypt e tokens.

🛡️ Autorização com RBAC (controle de acesso por função).

🐞 Log de erros e ações para facilitar a manutenção.

🧼 Interface simples e amigável para o usuário final.

📷 Prints (se desejar, pode incluir aqui imagens da interface ou da API rodando)
🙋‍♂️ Desenvolvido por
Aluno do curso de Análise e Desenvolvimento de Sistemas – IFPR Campus Paranaguá
Contato: artursimonijesus@gmail.com

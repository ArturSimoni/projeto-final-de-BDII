FROM python:3.11

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expõe a porta que o Flask vai usar
EXPOSE 5000

# Variável de ambiente para o Flask rodar em modo de produção (se quiser)
ENV FLASK_ENV=production
ENV FLASK_APP=app.py

# Comando para rodar o Flask escutando em todas interfaces (0.0.0.0)
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]

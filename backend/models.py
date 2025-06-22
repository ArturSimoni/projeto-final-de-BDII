import mysql.connector
import os

def db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "user"),
        password=os.getenv("DB_PASSWORD", "senha"),
        database=os.getenv("DB_NAME", "escola")
    )

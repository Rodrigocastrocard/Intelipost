import mysql.connector
from mysql.connector import Error

print("Iniciando teste...")

try:
    conn = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="Janete4353",  # a mesma do Workbench
        database="templariosapp",
        port=3306,
        connection_timeout=5
    )
    print("Conectado?", conn.is_connected())
    if conn.is_connected():
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        print("Resultado:", cursor.fetchone())
        cursor.close()
        conn.close()
except Error as e:
    print("Erro MySQL:", e)

input("Fim do teste, ENTER...")

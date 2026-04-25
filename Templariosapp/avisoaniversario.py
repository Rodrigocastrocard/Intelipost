from datetime import datetime
from urllib.parse import quote
import pymysql
import requests

CALLMEBOT_PHONE = "553798325701"
CALLMEBOT_APIKEY = "8154787"

def get_db_connection():
    return pymysql.connect(
        host="127.0.0.1",
        user="root",
        password="Janete4353",
        database="templariosapp",
        port=3306,
        cursorclass=pymysql.cursors.DictCursor,
        charset="utf8mb4"
    )

def buscar_aniversariantes():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT nome, data_aniversario
                FROM membros
                WHERE DAY(data_aniversario) = DAY(CURDATE())
                  AND MONTH(data_aniversario) = MONTH(CURDATE())
            """
            cursor.execute(sql)
            return cursor.fetchall()
    finally:
        conn.close()

def enviar_whatsapp_callmebot(mensagem):
    url = (
        "https://api.callmebot.com/whatsapp.php"
        f"?phone={CALLMEBOT_PHONE}"
        f"&text={quote(mensagem)}"
        f"&apikey={CALLMEBOT_APIKEY}"
    )

    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.text

def main():
    try:
        aniversariantes = buscar_aniversariantes()

        if not aniversariantes:
            print("Nenhum aniversariante hoje.")
            return

        nomes = ", ".join(p["nome"] for p in aniversariantes)
        mensagem = f"Aniversariantes de hoje ({datetime.now().strftime('%d/%m/%Y')}): {nomes}"

        retorno = enviar_whatsapp_callmebot(mensagem)
        print("Mensagem enviada com sucesso.")
        print(retorno)

    except Exception as e:
        print(f"Erro ao executar rotina: {e}")

if __name__ == "__main__":
    main()
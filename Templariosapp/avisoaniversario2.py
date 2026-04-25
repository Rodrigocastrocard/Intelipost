from datetime import datetime
import pymysql
import pywhatkit

GROUP_ID = "L6ezunL0xntDfrxKdquR9W"

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

def montar_mensagem(aniversariantes):
    data_hoje = datetime.now().strftime("%d/%m/%Y")

    if aniversariantes:
        nomes = ", ".join(p["nome"] for p in aniversariantes)
        return (
            f"🎉 Aniversariantes de hoje: {nomes}\n"
            f"Vamos desejar os parabéns! 🥳"
        )
    else:
        return f"Hoje não há aniversariantes cadastrados."

def enviar_mensagem_grupo(mensagem):
    agora = datetime.now()
    hora = agora.hour
    minuto = agora.minute + 2

    if minuto >= 60:
        minuto -= 60
        hora = (hora + 1) % 24

    pywhatkit.sendwhatmsg_to_group(
        GROUP_ID,
        mensagem,
        hora,
        minuto,
        wait_time=25,
        tab_close=True
    )

def main():
    try:
        aniversariantes = buscar_aniversariantes()
        mensagem = montar_mensagem(aniversariantes)

        print("Preparando envio para o grupo...")
        print(mensagem)

        enviar_mensagem_grupo(mensagem)
        print("Mensagem programada para envio no grupo com sucesso.")

    except Exception as e:
        print(f"Erro ao executar rotina: {e}")

if __name__ == "__main__":
    main()
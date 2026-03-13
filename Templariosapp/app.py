from flask import Flask, request, jsonify
import pymysql
from pymysql.err import MySQLError
from datetime import datetime

app = Flask(__name__)


def get_db_connection():
    return pymysql.connect(
        host="127.0.0.1",
        user="root",
        password="Janete4353",       # mesma do Workbench
        database="templariosapp",
        port=3306,
        cursorclass=pymysql.cursors.DictCursor  # sempre retorna dict
    )


@app.route("/")
def home():
    return "API do Templários está no ar!"


# ============================================================
# FUNÇÕES AUXILIARES PARA APP_CONFIG
# ============================================================

def get_app_config(conn):
    """
    Busca a configuração global (id = 1) na tabela app_config.
    Ajuste se você quiser outro critério.
    AGORA inclui também url_atas_reuniao.
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            id,
            server_base_url,
            pix_key,
            url_estatuto,
            url_agenda,
            url_galeria,
            url_agenda_interna,
            url_atas_reuniao
        FROM app_config
        WHERE id = 1
    """)
    config = cursor.fetchone()
    cursor.close()
    return config


def update_app_config(conn, data):
    """
    Atualiza campos da tabela app_config (id = 1).
    Aceita qualquer subset de:
    server_base_url, pix_key, url_estatuto, url_agenda,
    url_galeria, url_agenda_interna, url_atas_reuniao
    """
    campos_validos = [
        "server_base_url",
        "pix_key",
        "url_estatuto",
        "url_agenda",
        "url_galeria",
        "url_agenda_interna",
        "url_atas_reuniao"   # <-- NOVO CAMPO
    ]

    sets = []
    valores = []

    for campo in campos_validos:
        if campo in data:
            sets.append(f"{campo} = %s")
            valores.append(data[campo])

    if not sets:
        # Nada para atualizar
        return False

    sql = f"""
        UPDATE app_config
        SET {', '.join(sets)}
        WHERE id = 1
    """

    cursor = conn.cursor()
    cursor.execute(sql, tuple(valores))
    conn.commit()
    afetadas = cursor.rowcount
    cursor.close()
    return afetadas > 0


# ============================================================
# ENDPOINTS DE CONFIGURAÇÃO GERAL (app_config)
# ============================================================

@app.route("/app_config", methods=["GET"])
def get_app_config_endpoint():
    """
    Retorna todas as configurações da tabela app_config (registro id = 1).
    Já inclui url_atas_reuniao no JSON.
    """
    try:
        conn = get_db_connection()
        config = get_app_config(conn)
        conn.close()

        if config:
            return jsonify(config), 200
        else:
            return jsonify({"erro": "Configuração global não encontrada"}), 404
    except MySQLError as e:
        return jsonify({"erro": str(e)}), 500


@app.route("/app_config", methods=["PUT"])
def update_app_config_endpoint():
    """
    Atualiza configurações na tabela app_config.
    Exemplo de JSON aceito:
    {
        "server_base_url": "http://192.168.2.139:5000",
        "pix_key": "chavePIX123",
        "url_estatuto": "http://...",
        "url_agenda": "http://...",
        "url_galeria": "http://...",
        "url_agenda_interna": "http://...",
        "url_atas_reuniao": "https://drive.google.com/..."
    }
    """
    data = request.get_json() or {}

    try:
        conn = get_db_connection()
        ok = update_app_config(conn, data)
        conn.close()

        if ok:
            return jsonify({"sucesso": True}), 200
        else:
            return jsonify({"erro": "Nenhum campo válido informado ou configuração não encontrada"}), 400
    except MySQLError as e:
        return jsonify({"erro": str(e)}), 500


# ============================================================
# ENDPOINTS ESPECÍFICOS PARA PIX (usados pelo app Android)
# ============================================================

@app.route("/config/pix", methods=["GET"])
def get_pix():
    """
    Retorna apenas a chave PIX da configuração global.
    Resposta esperada pelo app:
    { "pix": "chavePIX..." }
    """
    try:
        conn = get_db_connection()
        config = get_app_config(conn)
        conn.close()

        if not config:
            return jsonify({"erro": "Configuração global não encontrada"}), 404

        return jsonify({"pix": config.get("pix_key", "")}), 200
    except MySQLError as e:
        return jsonify({"erro": str(e)}), 500


@app.route("/config/pix", methods=["POST"])
def set_pix():
    """
    Atualiza apenas a chave PIX.
    Body JSON esperado:
    { "pix": "nova_chave_pix" }
    """
    data = request.get_json() or {}
    pix = data.get("pix")

    if pix is None:
        return jsonify({"erro": "Campo 'pix' é obrigatório no JSON"}), 400

    try:
        conn = get_db_connection()
        ok = update_app_config(conn, {"pix_key": pix})
        conn.close()

        if ok:
            return jsonify({"sucesso": True, "pix": pix}), 200
        else:
            return jsonify({"erro": "Não foi possível atualizar a chave PIX"}), 500
    except MySQLError as e:
        return jsonify({"erro": str(e)}), 500


# ============================================================
# === CAIXA ===
# ============================================================

@app.route("/caixa", methods=["GET"])
def caixa():
    inicio = request.args.get("inicio")
    fim = request.args.get("fim")

    if not inicio or not fim:
        return jsonify({"erro": "Parâmetros 'inicio' e 'fim' são obrigatórios (yyyy-mm-dd)."}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT COALESCE(SUM(valor), 0) AS total
            FROM recebimentos
            WHERE data_recebimento BETWEEN %s AND %s
        """
        cursor.execute(query, (inicio, fim))
        resultado = cursor.fetchone()
        total = resultado["total"] if resultado else 0.0

        cursor.close()
        conn.close()

        return jsonify({"total": float(total)}), 200
    except MySQLError as e:
        return jsonify({"erro": str(e)}), 500


# === RECEBIMENTOS (vinculados a membros) ===
@app.route("/recebimentos", methods=["GET"])
def listar_recebimentos():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, codigo_membro, nome, descricao, valor, data_recebimento "
            "FROM recebimentos ORDER BY data_recebimento DESC"
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(rows), 200
    except MySQLError as e:
        return jsonify({"erro": str(e)}), 500


@app.route("/recebimentos", methods=["POST"])
def criar_recebimento():
    data = request.get_json()

    if not all(k in data for k in ["codigo_membro", "nome", "descricao", "valor", "data_recebimento"]):
        return jsonify({
            "erro": "codigo_membro, nome, descricao, valor, data_recebimento obrigatórios"
        }), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """
            INSERT INTO recebimentos (codigo_membro, nome, descricao, valor, data_recebimento)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (
            data["codigo_membro"],
            data["nome"],
            data["descricao"],
            float(data["valor"]),
            data["data_recebimento"]
        ))
        conn.commit()
        novo_id = cursor.lastrowid
        cursor.close()
        conn.close()

        return jsonify({"sucesso": True, "id": novo_id}), 201
    except MySQLError as e:
        return jsonify({"erro": str(e)}), 500


# === RECEBIMENTOS DIVERSOS (sem membro) ===
@app.route("/recebimentos_diversos", methods=["POST"])
def criar_recebimento_diverso():
    dados = request.get_json()
    descricao = dados.get("descricao")
    data_recebimento = dados.get("data_recebimento")  # formato yyyy-mm-dd
    valor = dados.get("valor")

    if not descricao or not data_recebimento or valor is None:
        return jsonify({"erro": "Campos obrigatórios: descricao, data_recebimento, valor"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO recebimentos_diversos (data, descricao, valor)
            VALUES (%s, %s, %s)
            """,
            (data_recebimento, descricao, float(valor))
        )
        conn.commit()
        novo_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return jsonify({"msg": "Recebimento diverso criado com sucesso", "id": novo_id}), 201
    except MySQLError as e:
        if 'conn' in locals():
            conn.rollback()
            cursor.close()
            conn.close()
        return jsonify({"erro": str(e)}), 500


# === MEMBROS ===
@app.route("/membros", methods=["GET"])
def listar_membros():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, codigo, nome, telefone,
                   data_candidatura, data_aniversario,
                   ativo, valor_mensal
            FROM membros
            ORDER BY nome
        """)
        membros = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(membros), 200
    except MySQLError as e:
        return jsonify({"erro": str(e)}), 500


@app.route("/membros", methods=["POST"])
def criar_membro():
    data = request.get_json()

    obrigatorios = ["codigo", "nome", "telefone",
                    "data_candidatura", "data_aniversario",
                    "ativo", "valor_mensal"]
    if not all(k in data for k in obrigatorios):
        return jsonify({"erro": "Campos obrigatórios: " + ", ".join(obrigatorios)}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """
            INSERT INTO membros
              (codigo, nome, telefone, data_candidatura,
               data_aniversario, ativo, valor_mensal)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (
            data["codigo"],
            data["nome"],
            data.get("telefone", ""),
            data["data_candidatura"],
            data["data_aniversario"],
            bool(data["ativo"]),
            float(data["valor_mensal"])
        ))
        conn.commit()
        novo_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return jsonify({"sucesso": True, "id": novo_id}), 201
    except MySQLError as e:
        return jsonify({"erro": str(e)}), 500


@app.route("/membros/<codigo>", methods=["PUT"])
def atualizar_membro(codigo):
    data = request.get_json()

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        valor_mensal = float(
            data.get("valor_mensal", data.get("valormensal", 0))
        )

        sql = """
            UPDATE membros
            SET nome = %s,
                telefone = %s,
                data_candidatura = %s,
                data_aniversario = %s,
                ativo = %s,
                valor_mensal = %s
            WHERE codigo = %s
        """
        cursor.execute(sql, (
            data.get("nome", ""),
            data.get("telefone", ""),
            data.get("data_candidatura", data.get("datacandidatura", None)),
            data.get("data_aniversario", data.get("dataaniversario", None)),
            bool(data.get("ativo", True)),
            valor_mensal,
            codigo
        ))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"sucesso": True}), 200
    except MySQLError as e:
        return jsonify({"erro": str(e)}), 500


# === DESPESAS ===
@app.route("/despesas", methods=["GET"])
def listar_despesas():
    data_inicio = request.args.get("inicio")
    data_fim = request.args.get("fim")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if data_inicio and data_fim:
            cursor.execute("""
                SELECT id, descricao, data_evento, valor 
                FROM despesas 
                WHERE data_evento BETWEEN %s AND %s 
                ORDER BY data_evento DESC
            """, (data_inicio, data_fim))
        else:
            cursor.execute("""
                SELECT id, descricao, data_evento, valor 
                FROM despesas 
                ORDER BY data_evento DESC 
                LIMIT 50
            """)

        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(rows), 200
    except MySQLError as e:
        return jsonify({"erro": str(e)}), 500


@app.route("/despesas", methods=["POST"])
def criar_despesa():
    data = request.get_json()

    if not all(k in data for k in ["descricao", "data_evento", "valor"]):
        return jsonify({"erro": "descricao, data_evento, valor obrigatórios"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """
            INSERT INTO despesas (descricao, data_evento, valor)
            VALUES (%s, %s, %s)
        """
        cursor.execute(sql, (
            data["descricao"],
            data["data_evento"],
            float(data["valor"])
        ))
        conn.commit()
        novo_id = cursor.lastrowid
        cursor.close()
        conn.close()

        return jsonify({
            "sucesso": True,
            "id": novo_id,
            "descricao": data["descricao"]
        }), 201
    except MySQLError as e:
        return jsonify({"erro": str(e)}), 500


@app.route("/despesas/total", methods=["GET"])
def total_despesas():
    data_inicio = request.args.get("inicio")
    data_fim = request.args.get("fim")

    if not data_inicio or not data_fim:
        return jsonify({"erro": "Parâmetros 'inicio' e 'fim' obrigatórios"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
            SELECT COALESCE(SUM(valor), 0) AS total_despesas
            FROM despesas
            WHERE data_evento BETWEEN %s AND %s
        """
        cursor.execute(query, (data_inicio, data_fim))
        resultado = cursor.fetchone()
        total = resultado["total_despesas"] if resultado else 0.0
        cursor.close()
        conn.close()

        return jsonify({"total_despesas": float(total)}), 200
    except MySQLError as e:
        return jsonify({"erro": str(e)}), 500


# === PRESENÇA REUNIÃO ===
@app.route("/presenca_reuniao", methods=["GET"])
def listar_presencas():
    data_reuniao = request.args.get("data")
    codigo_membro = request.args.get("codigo_membro")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if data_reuniao and codigo_membro:
            cursor.execute("""
                SELECT id, codigo_membro, nome_membro, data_reuniao 
                FROM presenca_reuniao 
                WHERE data_reuniao = %s AND codigo_membro = %s
            """, (data_reuniao, codigo_membro))
        elif data_reuniao:
            cursor.execute("""
                SELECT id, codigo_membro, nome_membro, data_reuniao 
                FROM presenca_reuniao 
                WHERE data_reuniao = %s 
                ORDER BY nome_membro
            """, (data_reuniao,))
        else:
            cursor.execute("""
                SELECT id, codigo_membro, nome_membro, data_reuniao 
                FROM presenca_reuniao 
                ORDER BY data_reuniao DESC, nome_membro 
                LIMIT 50
            """)

        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(rows), 200
    except MySQLError as e:
        return jsonify({"erro": str(e)}), 500


@app.route("/presenca_reuniao", methods=["POST"])
def registrar_presenca():
    data = request.get_json()

    if not all(k in data for k in ["codigo_membro", "nome_membro", "data_reuniao"]):
        return jsonify({"erro": "codigo_membro, nome_membro, data_reuniao obrigatórios"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """
            INSERT INTO presenca_reuniao (codigo_membro, nome_membro, data_reuniao)
            VALUES (%s, %s, %s)
        """
        cursor.execute(sql, (
            data["codigo_membro"],
            data["nome_membro"],
            data["data_reuniao"]
        ))
        conn.commit()
        novo_id = cursor.lastrowid
        cursor.close()
        conn.close()

        return jsonify({
            "sucesso": True,
            "id": novo_id,
            "data_reuniao": data["data_reuniao"]
        }), 201
    except MySQLError as e:
        if "Duplicate entry" in str(e):
            return jsonify({"erro": "Presença já registrada para este membro/data"}), 409
        return jsonify({"erro": str(e)}), 500


@app.route("/presenca_reuniao/resumo", methods=["GET"])
def resumo_presencas():
    data_reuniao = request.args.get("data")
    if not data_reuniao:
        return jsonify({"erro": "Parâmetro 'data' obrigatório"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                COUNT(*) as total_presentes,
                (SELECT COUNT(DISTINCT codigo_membro) FROM membros WHERE ativo = TRUE) as total_membros
            FROM presenca_reuniao 
            WHERE data_reuniao = %s
        """, (data_reuniao,))

        resultado = cursor.fetchone()
        cursor.close()
        conn.close()

        return jsonify({
            "data_reuniao": data_reuniao,
            "total_presentes": resultado["total_presentes"],
            "total_membros": resultado["total_membros"] or 0,
            "frequencia": f"{resultado['total_presentes']}/{resultado['total_membros'] or 0}"
        }), 200
    except MySQLError as e:
        return jsonify({"erro": str(e)}), 500


# === PRESENÇA PASSEIO ===
@app.route("/presenca_passeio", methods=["GET"])
def listar_presencas_passeio():
    data_passeio = request.args.get("data")
    codigo_membro = request.args.get("codigo_membro")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if data_passeio and codigo_membro:
            cursor.execute("""
                SELECT id, codigo_membro, nome_membro, data_passeio 
                FROM presenca_passeio 
                WHERE data_passeio = %s AND codigo_membro = %s
            """, (data_passeio, codigo_membro))
        elif data_passeio:
            cursor.execute("""
                SELECT id, codigo_membro, nome_membro, data_passeio 
                FROM presenca_passeio 
                WHERE data_passeio = %s 
                ORDER BY nome_membro
            """, (data_passeio,))
        else:
            cursor.execute("""
                SELECT id, codigo_membro, nome_membro, data_passeio 
                FROM presenca_passeio 
                ORDER BY data_passeio DESC, nome_membro 
                LIMIT 50
            """)

        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(rows), 200
    except MySQLError as e:
        return jsonify({"erro": str(e)}), 500


@app.route("/presenca_passeio", methods=["POST"])
def registrar_presenca_passeio():
    data = request.get_json()

    if not all(k in data for k in ["codigo_membro", "nome_membro", "data_passeio"]):
        return jsonify({"erro": "codigo_membro, nome_membro, data_passeio obrigatórios"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """
            INSERT INTO presenca_passeio (codigo_membro, nome_membro, data_passeio)
            VALUES (%s, %s, %s)
        """
        cursor.execute(sql, (
            data["codigo_membro"],
            data["nome_membro"],
            data["data_passeio"]
        ))
        conn.commit()
        novo_id = cursor.lastrowid
        cursor.close()
        conn.close()

        return jsonify({
            "sucesso": True,
            "id": novo_id,
            "data_passeio": data["data_passeio"]
        }), 201
    except MySQLError as e:
        if "Duplicate entry" in str(e):
            return jsonify({"erro": "Presença já registrada para este membro/passeio"}), 409
        return jsonify({"erro": str(e)}), 500


@app.route("/presenca_passeio/resumo", methods=["GET"])
def resumo_presencas_passeio():
    data_passeio = request.args.get("data")
    if not data_passeio:
        return jsonify({"erro": "Parâmetro 'data' obrigatório"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                COUNT(*) as total_presentes,
                (SELECT COUNT(DISTINCT codigo_membro) FROM membros WHERE ativo = TRUE) as total_membros
            FROM presenca_passeio 
            WHERE data_passeio = %s
        """, (data_passeio,))

        resultado = cursor.fetchone()
        cursor.close()
        conn.close()

        return jsonify({
            "data_passeio": data_passeio,
            "total_presentes": resultado["total_presentes"],
            "total_membros": resultado["total_membros"] or 0,
            "frequencia": f"{resultado['total_presentes']}/{resultado['total_membros'] or 0}"
        }), 200
    except MySQLError as e:
        return jsonify({"erro": str(e)}), 500


# === CONFIGURAÇÃO ANTIGA (por codigomc) ===
@app.route("/configuracao/<codigomc>", methods=["GET"])
def get_configuracao(codigomc):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT codigomc, urlestatuto, urlagendainterna, urlfotos, urllogo 
            FROM configuracao 
            WHERE codigomc = %s
        """, (codigomc,))
        config = cursor.fetchone()
        cursor.close()
        conn.close()

        if config:
            return jsonify(config), 200
        else:
            return jsonify({"erro": "Configuração não encontrada"}), 404
    except MySQLError as e:
        return jsonify({"erro": str(e)}), 500


@app.route("/configuracao", methods=["POST"])
def criar_configuracao():
    data = request.get_json()

    if not data.get("codigomc"):
        return jsonify({"erro": "codigomc obrigatório"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """
            INSERT INTO configuracao (codigomc, urlestatuto, urlagendainterna, urlfotos, urllogo)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (
            data["codigomc"],
            data.get("urlestatuto"),
            data.get("urlagendainterna"),
            data.get("urlfotos"),
            data.get("urllogo")
        ))
        conn.commit()
        novo_id = cursor.lastrowid
        cursor.close()
        conn.close()

        return jsonify({
            "sucesso": True,
            "id": novo_id,
            "codigomc": data["codigomc"]
        }), 201
    except MySQLError as e:
        if "Duplicate entry" in str(e):
            return jsonify({"erro": "Configuração já existe"}), 409
        return jsonify({"erro": str(e)}), 500


@app.route("/configuracao/<codigomc>", methods=["PUT"])
def atualizar_configuracao(codigomc):
    data = request.get_json()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """
            UPDATE configuracao 
            SET urlestatuto = %s, urlagendainterna = %s, urlfotos = %s, urllogo = %s
            WHERE codigomc = %s
        """
        cursor.execute(sql, (
            data.get("urlestatuto"),
            data.get("urlagendainterna"),
            data.get("urlfotos"),
            data.get("urllogo"),
            codigomc
        ))

        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({"erro": "Configuração não encontrada"}), 404

        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"sucesso": True}), 200
    except MySQLError as e:
        return jsonify({"erro": str(e)}), 500


# === EXTRATO ===
@app.route("/extrato")
def extrato():
    inicio = request.args.get("inicio")
    fim = request.args.get("fim")

    if not inicio or not fim:
        return jsonify({"erro": "Parâmetros 'inicio' e 'fim' são obrigatórios (yyyy-mm-dd)."}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        resultado = {
            "mensalidades_pagas": [],
            "recebimentos": [],
            "recebimentos_diversos": [],
            "despesas": [],
            "erros": []
        }

        # 1. Mensalidades pagas
        try:
            cursor.execute(
                """
                SELECT nome, referencia, valor
                FROM mensalidades
                WHERE pago = 1
                  AND data_pagamento BETWEEN %s AND %s
                """,
                (inicio, fim)
            )
            resultado["mensalidades_pagas"] = cursor.fetchall()
        except MySQLError as e:
            resultado["erros"].append(f"Mensalidades: {str(e)}")

        # 2. Recebimentos membros
        try:
            cursor.execute(
                """
                SELECT data_recebimento AS data, descricao, valor, nome
                FROM recebimentos
                WHERE data_recebimento BETWEEN %s AND %s
                """,
                (inicio, fim)
            )
            resultado["recebimentos"] = cursor.fetchall()
        except MySQLError as e:
            resultado["erros"].append(f"Recebimentos: {str(e)}")

        # 3. Recebimentos diversos
        try:
            cursor.execute(
                """
                SELECT data, descricao, valor
                FROM recebimentos_diversos
                WHERE data BETWEEN %s AND %s
                """,
                (inicio, fim)
            )
            resultado["recebimentos_diversos"] = cursor.fetchall()
        except MySQLError as e:
            resultado["erros"].append(f"Recebimentos diversos: {str(e)}")

        # 4. Despesas
        try:
            cursor.execute(
                """
                SELECT data_evento AS data, descricao, valor
                FROM despesas
                WHERE data_evento BETWEEN %s AND %s
                """,
                (inicio, fim)
            )
            resultado["despesas"] = cursor.fetchall()
        except MySQLError as e:
            resultado["erros"].append(f"Despesas: {str(e)}")

        cursor.close()
        conn.close()

        total_mensalidades = sum(float(m.get("valor", 0)) for m in resultado["mensalidades_pagas"])
        total_recebimentos_membros = sum(float(r.get("valor", 0)) for r in resultado["recebimentos"])
        total_recebimentos_diversos = sum(float(r.get("valor", 0)) for r in resultado["recebimentos_diversos"])
        total_recebimentos = total_recebimentos_membros + total_recebimentos_diversos
        total_despesas = sum(float(d.get("valor", 0)) for d in resultado["despesas"])
        saldo = total_mensalidades + total_recebimentos - total_despesas

        resultado.update({
            "total_mensalidades": float(total_mensalidades),
            "total_recebimentos": float(total_recebimentos),
            "total_despesas": float(total_despesas),
            "total_recebimentos_membros": float(total_recebimentos_membros),
            "total_recebimentos_diversos": float(total_recebimentos_diversos),
            "saldo": float(saldo),
            "periodo": f"{inicio} a {fim}"
        })

        return jsonify(resultado), 200

    except Exception as e:
        return jsonify({"erro": f"Erro geral: {str(e)}", "traceback": str(e)}), 500


# === MENSALIDADES ===
@app.route("/mensalidades", methods=["GET"])
def listar_mensalidades():
    inicio = request.args.get("inicio")
    fim = request.args.get("fim")
    status = request.args.get("status", "ambas")  # abertas, pagas, ambas

    if not inicio or not fim:
        return jsonify({"erro": "Parâmetros inicio e fim são obrigatórios (YYYY-MM-DD)."}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        base_sql = """
            SELECT id, codigo_membro, nome, valor, referencia, pago
            FROM mensalidades
        """
        params = []
        where_clauses = []

        if status == "abertas":
            where_clauses.append("pago = 0")
        elif status == "pagas":
            where_clauses.append("pago = 1")

        if where_clauses:
            base_sql += " WHERE " + " AND ".join(where_clauses)

        base_sql += " ORDER BY nome, referencia"

        cursor.execute(base_sql, tuple(params))
        mensalidades = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify(mensalidades), 200

    except MySQLError as e:
        return jsonify({"erro": str(e)}), 500


# === BAIXA DE MENSALIDADES ===
@app.route("/mensalidades/baixa", methods=["POST"])
def baixa_mensalidade():
    data = request.get_json()

    obrigatorios = ["id_mensalidade", "valor", "data_pagamento"]
    if not all(k in data for k in obrigatorios):
        return jsonify({"erro": "id_mensalidade, valor, data_pagamento obrigatórios"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT codigo_membro, nome, referencia
            FROM mensalidades
            WHERE id = %s
        """, (int(data["id_mensalidade"]),))
        m = cursor.fetchone()
        if not m:
            cursor.close()
            conn.close()
            return jsonify({"erro": "Mensalidade não encontrada"}), 404

        codigo_membro = m["codigo_membro"]
        nome = m["nome"]
        referencia = m["referencia"]
        valor = float(data["valor"])
        data_pagamento = data["data_pagamento"]

        cursor.execute("""
            UPDATE mensalidades
            SET pago = 1,
                valor = %s,
                data_pagamento = %s
            WHERE id = %s
        """, (valor, data_pagamento, int(data["id_mensalidade"])))

        descricao = f"Mensalidade {referencia}"
        cursor.execute("""
            INSERT INTO recebimentos (codigo_membro, nome, descricao, valor, data_recebimento)
            VALUES (%s, %s, %s, %s, %s)
        """, (codigo_membro, nome, descricao, valor, data_pagamento))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"sucesso": True}), 200

    except MySQLError as e:
        return jsonify({"erro": str(e)}), 500


@app.route("/mensalidades/abertas/<codigo_membro>", methods=["GET"])
def listar_mensalidades_abertas_membro(codigo_membro):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, codigo_membro, nome, valor, referencia, pago
            FROM mensalidades
            WHERE codigo_membro = %s
              AND pago = 0
            ORDER BY referencia
        """, (codigo_membro,))

        mensalidades = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify(mensalidades), 200

    except MySQLError as e:
        return jsonify({"erro": str(e)}), 500


@app.route("/mensalidades/gerar", methods=["POST"])
def gerar_mensalidades():
    try:
        hoje = datetime.today()
        referencia = hoje.strftime("%m/%Y")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT codigo, nome, valor_mensal
            FROM membros
            WHERE ativo = 1
              AND valor_mensal IS NOT NULL
              AND valor_mensal > 0
        """)
        membros = cursor.fetchall()

        if not membros:
            cursor.close()
            conn.close()
            return jsonify({
                "gerados": 0,
                "ignorados": 0,
                "msg": "Nenhum membro ativo com valor de mensalidade definido."
            }), 200

        gerados = 0
        ignorados = 0

        for m in membros:
            codigo = m["codigo"]
            nome = m["nome"]
            valor = float(m["valor_mensal"])

            cursor.execute("""
                SELECT id
                FROM mensalidades
                WHERE codigo_membro = %s
                  AND referencia = %s
            """, (codigo, referencia))
            existe = cursor.fetchone()

            if existe:
                ignorados += 1
                continue

            cursor.execute("""
                INSERT INTO mensalidades (codigo_membro, nome, valor, referencia, pago)
                VALUES (%s, %s, %s, %s, 0)
            """, (codigo, nome, valor, referencia))
            gerados += 1

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "sucesso": True,
            "gerados": gerados,
            "ignorados": ignorados,
            "referencia": referencia
        }), 201 if gerados > 0 else 200

    except MySQLError as e:
        return jsonify({"erro": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

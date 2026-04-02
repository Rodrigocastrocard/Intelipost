import json
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request, jsonify
from datetime import datetime
import requests

app = Flask(__name__)

URL_INTELIPOST = "https://api.intelipost.com.br/api/v1/tracking/add/events"
API_KEY = "b1756bca-aeb3-42b1-825a-968e31ed6cdc"

# =============== CONFIGURAÇÃO DE LOG ===============
log_handler = RotatingFileHandler(
    "integracao_intelipost.log",
    maxBytes=5 * 1024 * 1024,
    backupCount=3,
    encoding="utf-8"
)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
log_handler.setFormatter(formatter)
log_handler.setLevel(logging.INFO)

logger = logging.getLogger("integracao_intelipost")
logger.setLevel(logging.INFO)

if not logger.handlers:
    logger.addHandler(log_handler)

# =============== FUNÇÕES AUXILIARES ===============

def formatar_data_br_para_iso(data_br: str) -> str:
    dt = datetime.strptime(data_br, "%d/%m/%Y %H:%M:%S")
    return dt.strftime("%Y-%m-%dT%H:%M:%S-03:00")


def montar_payload_intelipost(webhook_json: dict) -> dict:
    service = webhook_json.get("service", {})
    checkpoint = service.get("checkpoint", {})

    operation_date = checkpoint.get("operation_date")
    event_date = formatar_data_br_para_iso(operation_date) if operation_date else ""

    return {
        "logistic_provider": "Agile",
        "logistic_provider_id": 14444,
        "shipper": "",
        "order_number": str(service.get("user_service_unique_code", "")).strip(),
        "volume_number": "1",
        "events": [
            {
                "event_date": event_date,
                "original_code": str(checkpoint.get("user_event_unique_code", "")),
                "original_message": checkpoint.get("event_description", "") or "",
                "extra": {
                    "live_tracking_url": ""
                },
                "attachments": [],
                "location": {}
            }
        ]
    }

# =============== ENDPOINT WEBHOOK ===============

@app.route("/webhook", methods=["POST"])
def receber_webhook():
    if not request.is_json:
        logger.warning("Requisição sem JSON válido. Headers=%s", dict(request.headers))
        return jsonify({"erro": "Content-Type deve ser application/json"}), 400

    dados = request.get_json(silent=True)
    if dados is None:
        logger.warning("JSON inválido recebido. Raw data=%s", request.data)
        return jsonify({"erro": "JSON inválido"}), 400

    logger.info("Webhook recebido: %s", json.dumps(dados, ensure_ascii=False))

    try:
        payload = montar_payload_intelipost(dados)
    except Exception as e:
        logger.exception("Erro ao montar payload para Intelipost")
        return jsonify({"erro": f"Falha ao montar payload: {e}"}), 500

    headers = {
        "logistic-provider-api-key": API_KEY,
        "Content-Type": "application/json"
    }

    logger.info("Enviando para Intelipost. Payload=%s", json.dumps(payload, ensure_ascii=False))

    try:
        response = requests.post(
            URL_INTELIPOST,
            headers=headers,
            json=payload,
            timeout=30
        )

        if 200 <= response.status_code < 300:
            logger.info(
                "Intelipost OK. status=%s, response=%s",
                response.status_code,
                response.text
            )
        else:
            logger.error(
                "Intelipost ERRO. status=%s, response=%s",
                response.status_code,
                response.text
            )

    except requests.RequestException as e:
        logger.exception("Erro de rede ao chamar Intelipost")
        return jsonify({"erro": f"Erro ao chamar Intelipost: {e}"}), 502

    return jsonify({
        "status": "processado",
        "intelipost_status": response.status_code,
        "intelipost_response": response.text,
        "payload_enviado": payload
    }), 200

# =============== HEALTHCHECK ===============

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
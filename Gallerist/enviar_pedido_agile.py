import csv
import json
import os
import requests
import tkinter as tk
from tkinter import filedialog, messagebox
import hmac
import hashlib
import base64

CONFIG_FILE = "config.json"

# 🔧 Mapeamento entre cabeçalhos da planilha e campos do JSON
MAPEAMENTO = {
    "Código CD": "user_depot_unique_code",
    "Razão Social": "client_formal_name",
    "Nome informal": "client_informal_name",
    "Código (NF/PD)": "user_service_unique_code",
    "CNPJ/CPF": "user_client_unique_code",
    "Contato": "contact_name",
    "Telefone": "contact_phone",
    "Endereço": "address_street",
    "Número": "address_number",
    "Complemento": "address_complement",
    "Bairro": "address_district",
    "Município": "address_city",
    "Estado": "address_state",
    "CEP": "address_zip_code",
    "Tipo": "service_type",
    "Quantidade de volumes": "volumes",
    "Janela Inicio A": "initial_attendance_window_a",
    "Janela Fim A": "final_attendance_window_a",
    "Janela Inicio B": "initial_attendance_window_b",
    "Janela Fim B": "final_attendance_window_b",
    "Tempo de atendimento estimado": "duration",
    "Etiquetas": "tags",
    "Carga (KG)": "carga_kg",
    "Carga (CM³)": "carga_cm3",
    "Valor (R$)": "valor_rs",
    "Habilidades": "skills",
    # repare no espaço no final – igual ao HEADERS CSV LIDOS
    "observation ": "observation"
}


def remover_vazios(d):
    if isinstance(d, dict):
        return {k: remover_vazios(v) for k, v in d.items() if v not in ("", [], {}, None)}
    elif isinstance(d, list):
        return [remover_vazios(v) for v in d if v not in ("", [], {}, None)]
    return d


def parse_list(valor):
    if not valor:
        return []
    return [v.strip() for v in valor.split(";") if v.strip()]


def parse_json(valor):
    if not valor:
        return []
    try:
        return json.loads(valor)
    except json.JSONDecodeError:
        return []


def try_int(valor):
    try:
        return int(valor)
    except (ValueError, TypeError):
        return valor


def try_float(valor):
    try:
        return float(str(valor).replace(",", "."))
    except (ValueError, TypeError):
        return valor


def csv_para_json(caminho_csv):
    with open(caminho_csv, newline='', encoding='utf-8-sig') as csvfile:
        leitor = csv.DictReader(csvfile, delimiter=';')

        print("HEADERS CSV LIDOS:", leitor.fieldnames)

        registros = []

        for linha in leitor:
            dados = {}
            for coluna_csv, campo_json in MAPEAMENTO.items():
                valor = linha.get(coluna_csv)
                if valor is None:
                    continue
                valor = valor.strip()
                if valor != "":
                    dados[campo_json] = valor

            dimensoes = []
            if dados.get("carga_kg"):
                dimensoes.append({
                    "name": "Peso (kg)",
                    "compartment_name": "Normal",
                    "value": try_float(dados["carga_kg"])
                })
            if dados.get("carga_cm3"):
                dimensoes.append({
                    "name": "Cubagem (m³)",
                    "compartment_name": "Normal",
                    "value": try_float(dados["carga_cm3"])
                })
            if dados.get("valor_rs"):
                dimensoes.append({
                    "name": "Valor (R$)",
                    "compartment_name": "Normal",
                    "value": try_float(dados["valor_rs"])
                })

            reg = {
                "user_depot_unique_code": dados.get("user_depot_unique_code"),
                "client_formal_name": dados.get("client_formal_name"),
                "client_informal_name": dados.get("client_informal_name"),
                "user_service_unique_code": dados.get("user_service_unique_code"),
                "user_client_unique_code": dados.get("user_client_unique_code"),
                "contact_name": dados.get("contact_name"),
                "contact_phone": dados.get("contact_phone"),
                "address": {
                    "street": dados.get("address_street"),
                    "number": try_int(dados.get("address_number")),
                    "complement": dados.get("address_complement"),
                    "district": dados.get("address_district"),
                    "city": dados.get("address_city"),
                    "state": dados.get("address_state"),
                    "zip_code": dados.get("address_zip_code")
                },
                "service_type": dados.get("service_type"),
                "volumes": try_int(dados.get("volumes")),
                "initial_attendance_window_a": dados.get("initial_attendance_window_a"),
                "final_attendance_window_a": dados.get("final_attendance_window_a"),
                "initial_attendance_window_b": dados.get("initial_attendance_window_b"),
                "final_attendance_window_b": dados.get("final_attendance_window_b"),
                "duration": dados.get("duration"),
                "tags": parse_list(dados.get("tags", "")),
                "dimensions": dimensoes,
                "sender": parse_json(dados.get("sender", "")),
                # agora observation sempre entra se houver texto na coluna
                "observation": dados.get("observation", "")
            }

            registros.append(remover_vazios(reg))

        if registros:
            print("DEBUG PRIMEIRO REGISTRO:", json.dumps(registros[0], ensure_ascii=False, indent=2))

    return {
        "filters": {},
        "action": "insert_or_update",
        "json_content": registros
    }


def gerar_token_hmac(secret_key: str) -> str:
    text = "POST\n\napplication/json\n/dash-beta/api/v2/service"
    key_bytes = secret_key.encode("utf-8")
    msg_bytes = text.encode("utf-8")
    digest = hmac.new(key_bytes, msg_bytes, hashlib.sha1).digest()
    token = base64.b64encode(digest).decode("utf-8")
    return token


def enviar_json_para_api(conteudo, ambiente, usuario, secret_key):
    url = ambiente.rstrip('/') + "/dash-beta/api/v2/service"
    token = gerar_token_hmac(secret_key)
    authorization = f"AWS {usuario}:{token}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": authorization
    }
    print("JSON ENVIADO:", json.dumps(conteudo, ensure_ascii=False, indent=2))
    resposta = requests.post(url, json=conteudo, headers=headers)
    return resposta.status_code, resposta.text


def salvar_config(ambiente, usuario, secret_key):
    config = {"ambiente": ambiente, "usuario": usuario, "secret_key": secret_key}
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)


def carregar_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"ambiente": "", "usuario": "", "secret_key": ""}


def selecionar_csv():
    global caminho_csv_selecionado
    caminho_csv_selecionado = filedialog.askopenfilename(
        title="Selecione o arquivo CSV",
        filetypes=[("CSV Files", "*.csv")],
    )
    label_arquivo.config(
        text=f"Arquivo: {caminho_csv_selecionado}" if caminho_csv_selecionado else "Nenhum arquivo selecionado"
    )


def enviar():
    ambiente = entry_ambiente.get().strip()
    usuario = entry_usuario.get().strip()
    secret_key = entry_secret.get().strip()

    if not ambiente or not usuario or not secret_key:
        messagebox.showwarning("Aviso", "Preencha ambiente, usuário e chave secreta!")
        return

    if not caminho_csv_selecionado:
        messagebox.showwarning("Aviso", "Selecione um arquivo CSV primeiro!")
        return

    try:
        conteudo = csv_para_json(caminho_csv_selecionado)
        status, resposta = enviar_json_para_api(conteudo, ambiente, usuario, secret_key)
        salvar_config(ambiente, usuario, secret_key)
        messagebox.showinfo("Sucesso", f"Status: {status}\n\nResposta: {resposta}")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao processar: {str(e)}")


# GUI
root = tk.Tk()
root.title("Enviar CSV com Autenticação para API")
root.geometry("600x420")

frame = tk.Frame(root, padx=15, pady=15)
frame.pack(fill=tk.BOTH, expand=True)

config = carregar_config()

tk.Label(
    frame,
    text="Ambiente (ex: https://gallerist.agileprocess.com.br):",
    font=("Arial", 10, "bold"),
).pack(anchor=tk.W)
entry_ambiente = tk.Entry(frame)
entry_ambiente.pack(fill=tk.X, pady=(0, 10))
entry_ambiente.insert(0, config.get("ambiente", ""))

tk.Label(
    frame,
    text="Usuário de autenticação (ex: gallerist):",
    font=("Arial", 10, "bold"),
).pack(anchor=tk.W)
entry_usuario = tk.Entry(frame)
entry_usuario.pack(fill=tk.X, pady=(0, 10))
entry_usuario.insert(0, config.get("usuario", ""))

tk.Label(
    frame,
    text="Chave secreta (senha/base64) para gerar o TOKEN:",
    font=("Arial", 10, "bold"),
).pack(anchor=tk.W)
entry_secret = tk.Entry(frame, show="*")
entry_secret.pack(fill=tk.X, pady=(0, 15))
entry_secret.insert(0, config.get("secret_key", ""))

tk.Label(frame, text="Arquivo CSV:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
frame_arquivo = tk.Frame(frame)
frame_arquivo.pack(fill=tk.X, pady=(0, 15))

label_arquivo = tk.Label(
    frame_arquivo,
    text="Nenhum arquivo selecionado",
    fg="gray",
    font=("Arial", 9),
)
label_arquivo.pack(side=tk.LEFT, fill=tk.X, expand=True)

tk.Button(frame_arquivo, text="Procurar...", command=selecionar_csv, width=12).pack(
    side=tk.RIGHT, padx=(10, 0)
)

tk.Button(
    frame,
    text="ENVIAR",
    command=enviar,
    bg="#4CAF50",
    fg="white",
    font=("Arial", 12, "bold"),
    height=2,
    cursor="hand2",
).pack(fill=tk.X, pady=(10, 0))

caminho_csv_selecionado = None
root.mainloop()

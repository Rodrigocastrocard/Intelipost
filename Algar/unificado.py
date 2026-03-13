import os
import sys

if getattr(sys, 'frozen', False):
    application_path = sys._MEIPASS
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

os.chdir(application_path)


import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import requests
import json
import os
from datetime import datetime
import base64
import numpy as np
from openpyxl import load_workbook

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

CONFIG_FILE_INTELIPOST = "config.json"
CONFIG_FILE_AUTH = "auth.json"


# ===================== FUNÇÕES INTELIPOST (TODAS AS 5) =====================

def load_config_intelipost():
    if os.path.exists(CONFIG_FILE_INTELIPOST):
        with open(CONFIG_FILE_INTELIPOST, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                return {}
        api_key_b64 = data.get("ApiKey")
        if api_key_b64:
            try:
                decoded = base64.b64decode(api_key_b64.encode("utf-8")).decode("utf-8")
                data["ApiKey"] = decoded
            except Exception:
                pass
        return data
    return {}


def save_config_intelipost(config):
    data = config.copy()
    api_key = data.get("ApiKey")
    if api_key:
        encoded = base64.b64encode(api_key.encode("utf-8")).decode("utf-8")
        data["ApiKey"] = encoded
    with open(CONFIG_FILE_INTELIPOST, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def _obter_apikey_intelipost(entry_apikey):
    api_key_display = entry_apikey.get().strip()
    if api_key_display.startswith("********"):
        config = load_config_intelipost()
        api_key = config.get("ApiKey", "").strip()
    else:
        api_key = api_key_display.strip()
    return api_key if api_key else None


def _montar_pedidos_do_csv(caminho_csv):
    if not caminho_csv or not os.path.exists(caminho_csv):
        return None, None
    try:
        df = pd.read_csv(caminho_csv, sep=None, engine="python")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao ler CSV: {e}")
        return None, None

    if "Pedido" not in df.columns:
        messagebox.showerror("Erro", "O CSV deve conter a coluna 'Pedido'.")
        return None, None

    pedidos = []
    now_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    for pedido in df["Pedido"].dropna():
        pedidos.append({"order_number": str(pedido), "event_date": now_str})
    return pedidos, caminho_csv if pedidos else None


# ✅ 1. PRONTO PARA ENVIO
def enviar_pedidos(entry_csv, entry_apikey):
    api_key = _obter_apikey_intelipost(entry_apikey)
    if not api_key:
        return
    pedidos, caminho_csv = _montar_pedidos_do_csv(entry_csv.get())
    if pedidos is None:
        return

    url = "https://api.intelipost.com.br/api/v1/shipment_order/multi/ready_for_shipment/with_date"
    headers = {"Content-Type": "application/json", "Api-Key": api_key}

    try:
        response = requests.post(url, headers=headers, json=pedidos)
        if response.status_code == 200:
            messagebox.showinfo("Sucesso", "✅ Pedidos marcados como PRONTO PARA ENVIO!")
            if caminho_csv:
                base, ext = os.path.splitext(caminho_csv)
                os.rename(caminho_csv, f"{base}_Ready{ext}")
        else:
            messagebox.showerror("Erro", f"❌ Status: {response.status_code}\n{response.text}")
    except Exception as e:
        messagebox.showerror("Erro", f"❌ Erro de conexão: {e}")


# ✅ 2. DESPACHADO
def enviar_pedidos_despachado(entry_csv, entry_apikey):
    api_key = _obter_apikey_intelipost(entry_apikey)
    if not api_key:
        return
    pedidos, caminho_csv = _montar_pedidos_do_csv(entry_csv.get())
    if pedidos is None:
        return

    url = "https://api.intelipost.com.br/api/v1/shipment_order/multi/shipped/with_date"
    headers = {"Content-Type": "application/json", "Api-Key": api_key}

    try:
        response = requests.post(url, headers=headers, json=pedidos)
        if response.status_code == 200:
            messagebox.showinfo("Sucesso", "✅ Pedidos marcados como DESPACHADOS!")
            if caminho_csv:
                base, ext = os.path.splitext(caminho_csv)
                os.rename(caminho_csv, f"{base}_Shipped{ext}")
        else:
            messagebox.showerror("Erro", f"❌ Status: {response.status_code}\n{response.text}")
    except Exception as e:
        messagebox.showerror("Erro", f"❌ Erro de conexão: {e}")


# ✅ 2.1 ENTREGUE
def enviar_pedidos_entregue(entry_csv, entry_apikey):
    api_key = _obter_apikey_intelipost(entry_apikey)
    if not api_key:
        return
    pedidos, caminho_csv = _montar_pedidos_do_csv(entry_csv.get())
    if pedidos is None:
        return

    url = "https://api.intelipost.com.br/api/v1/shipment_order/multi/delivered/with_date"
    headers = {"Content-Type": "application/json", "Api-Key": api_key}

    try:
        response = requests.post(url, headers=headers, json=pedidos)
        if response.status_code == 200:
            messagebox.showinfo("Sucesso", "✅ Pedidos marcados como ENTREGUES!")
            if caminho_csv:
                base, ext = os.path.splitext(caminho_csv)
                os.rename(caminho_csv, f"{base}_Delivered{ext}")
        else:
            messagebox.showerror("Erro", f"❌ Status: {response.status_code}\n{response.text}")
    except Exception as e:
        messagebox.showerror("Erro", f"❌ Erro de conexão: {e}")


# ✅ 3. CANCELAR PEDIDOS
def cancelar_pedidos(entry_csv, entry_apikey):
    api_key = _obter_apikey_intelipost(entry_apikey)
    if not api_key:
        return

    caminho_csv = entry_csv.get().strip()
    if not caminho_csv or not os.path.exists(caminho_csv):
        messagebox.showerror("Erro", "❌ Selecione um arquivo CSV válido.")
        return

    try:
        df = pd.read_csv(caminho_csv, sep=None, engine="python")
    except Exception as e:
        messagebox.showerror("Erro", f"❌ Erro ao ler CSV: {e}")
        return

    if "Pedido" not in df.columns:
        messagebox.showerror("Erro", "❌ CSV deve conter coluna 'Pedido'.")
        return

    headers = {"Content-Type": "application/json", "Api-Key": api_key}
    base_url = "https://api.intelipost.com.br/api/v1/order/"

    total, sucesso, falhas = len(df), 0, 0
    for pedido in df["Pedido"].dropna():
        order_number = str(pedido).strip()
        if not order_number:
            continue

        url = f"{base_url}{order_number}/cancel"
        payload = {"order_number": order_number}

        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code in [200, 201, 204]:
                sucesso += 1
            else:
                falhas += 1
        except:
            falhas += 1

    messagebox.showinfo("Concluído",
                        f"✅ Cancelamento concluído!\nSucessos: {sucesso}\nFalhas: {falhas}\nTotal: {total}")
    if sucesso > 0:
        base, ext = os.path.splitext(caminho_csv)
        try:
            os.rename(caminho_csv, f"{base}_Cancelado{ext}")
        except:
            pass


# ✅ 4. ALTERAR TRANSPORTADORA (RESTABELECIDA!)
def alterar_transportadora(entry_csv, entry_apikey):
    api_key = _obter_apikey_intelipost(entry_apikey)
    if not api_key:
        messagebox.showerror("Erro", "❌ Informe a ApiKey!")
        return

    caminho_csv = entry_csv.get().strip()
    if not caminho_csv or not os.path.exists(caminho_csv):
        messagebox.showerror("Erro", "❌ Selecione um arquivo CSV válido.")
        return

    try:
        df = pd.read_csv(caminho_csv, sep=None, engine="python")
    except Exception as e:
        messagebox.showerror("Erro", f"❌ Erro ao ler CSV: {e}")
        return

    if "Pedido" not in df.columns or "Transportadora" not in df.columns:
        messagebox.showerror("Erro", "❌ CSV deve conter colunas 'Pedido' e 'Transportadora'.")
        return

    headers = {"Content-Type": "application/json", "Api-Key": api_key}
    url_get_base = "https://api.intelipost.com.br/api/v1/shipment_order/"
    url_post = "https://api.intelipost.com.br/api/v1/shipment_order/change_delivery_method"

    total, sucesso, falhas = len(df), 0, 0
    for _, linha in df.iterrows():
        pedido = str(linha["Pedido"]).strip()
        transportadora = linha["Transportadora"]
        if not pedido:
            continue

        try:
            # GET para obter dados do pedido
            resp_get = requests.get(url_get_base + pedido, headers=headers)
            if resp_get.status_code != 200:
                falhas += 1
                continue

            dados = resp_get.json()
            content = dados.get("content", {})

            # Monta volumes
            volumes_get = content.get("shipment_order_volume_array", [])
            volumes_body = []
            for v in volumes_get:
                volume_number = v.get("shipment_order_volume_number")
                tracking_code = v.get("tracking_code")
                if volume_number is not None:
                    volumes_body.append({
                        "volume_number": str(volume_number),
                        "tracking_code": tracking_code
                    })

            # Monta body para POST
            est_date = content.get("estimated_delivery_date") or datetime.now().isoformat(timespec="seconds")
            body = {
                "quote_id": content.get("quote_id"),
                "estimated_delivery_date": est_date,
                "delivery_method_id": int(transportadora),
                "order_number": pedido,
                "volumes": volumes_body
            }

            # POST para alterar transportadora
            resp_post = requests.post(url_post, headers=headers, json=body)
            if resp_post.status_code in [200, 201]:
                sucesso += 1
            else:
                falhas += 1

        except Exception:
            falhas += 1

    messagebox.showinfo("Concluído", f"✅ Alteração concluída!\nSucessos: {sucesso}\nFalhas: {falhas}\nTotal: {total}")
    if sucesso > 0:
        base, ext = os.path.splitext(caminho_csv)
        try:
            os.rename(caminho_csv, f"{base}_Transportadora{ext}")
        except:
            pass


# ===================== FUNÇÕES PLANILHA COMPLEXA =====================

def json_serial(obj):
    if isinstance(obj, (datetime, pd.Timestamp)):
        return obj.isoformat()
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"Objeto {type(obj).__name__} não serializável")


def carregar_config_auth():
    if not os.path.exists(CONFIG_FILE_AUTH):
        return None
    try:
        with open(CONFIG_FILE_AUTH, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get('api-key')
    except:
        return None


def salvar_config_auth(api_key):
    data = {'api-key': api_key}
    if os.path.exists(CONFIG_FILE_AUTH):
        try:
            with open(CONFIG_FILE_AUTH, 'r', encoding='utf-8') as f:
                data.update(json.load(f))
        except:
            pass
    with open(CONFIG_FILE_AUTH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def set_nested_value(d, path, value):
    for i, key_part in enumerate(path):
        try:
            key = int(key_part)
        except ValueError:
            key = key_part
        is_last_key = (i == len(path) - 1)
        if is_last_key:
            if isinstance(d, list):
                while len(d) <= key:
                    d.append(None)
            d[key] = value
        else:
            try:
                next_level_is_list = bool(int(path[i + 1]))
            except:
                next_level_is_list = False
            if isinstance(d, list):
                while len(d) <= key:
                    d.append(None)
                if d[key] is None:
                    d[key] = [] if next_level_is_list else {}
                d = d[key]
            else:
                if key not in d:
                    d[key] = [] if next_level_is_list else {}
                d = d[key]


def processar_planilha(nome_arquivo):
    df = pd.read_excel(nome_arquivo, header=2, engine='openpyxl', dtype=str)
    df.fillna('', inplace=True)

    NUMERIC_KEYS = {'quote_id', 'customer_shipping_costs', 'provider_shipping_costs', 'delivery_method_id',
                    'weight', 'width', 'height', 'length', 'products_quantity', 'price', 'quantity',
                    'invoice_total_value', 'invoice_products_value', 'content_declaration_total_value',
                    'shipment_order_volume_number'}
    BOOLEAN_KEYS = {'scheduled', 'is_company', 'opt_in', 'whatsapp', 'is_icms_exempt'}
    DATE_KEYS = {'created', 'shipped_date', 'estimated_delivery_date', 'invoice_date', 'content_declaration_date'}

    def convert_value_type(key, value):
        if not value:
            return value
        if key in DATE_KEYS:
            for fmt in ['%d/%m/%Y %H:%M:%S', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
                try:
                    dt = datetime.strptime(str(value), fmt)
                    return dt.strftime('%Y-%m-%dT%H:%M:%S-03:00') if 'H' in fmt else dt.strftime(
                        '%Y-%m-%dT00:00:00-03:00')
                except:
                    pass
            return value
        elif key in NUMERIC_KEYS:
            try:
                return float(value) if '.' in str(value) else int(value)
            except:
                return value
        elif key in BOOLEAN_KEYS:
            val_lower = str(value).lower()
            if val_lower in ['true', '1', 'sim', 'verdadeiro', 's']:
                return True
            if val_lower in ['false', '0', 'não', 'nao', 'falso', 'n']:
                return False
        return value

    if 'order_number' not in df.columns:
        raise RuntimeError("Coluna 'order_number' não encontrada")

    pedidos_agrupados = df.groupby('order_number')
    lista_de_requisicoes = []

    for order_number, group in pedidos_agrupados:
        payload_base = {}
        primeira_linha = group.iloc[0]

        for chave_completa, valor in primeira_linha.items():
            chave_limpa = str(chave_completa).strip()
            if chave_limpa.startswith('shipment_order_volume_array.') or valor == '':
                continue
            path = chave_limpa.split('.')
            final_value = convert_value_type(path[-1], valor)
            set_nested_value(payload_base, path, final_value)

        volumes_list = []
        for _, row in group.iterrows():
            volume_obj = {}
            colunas_volume = {k.strip(): v for k, v in row.items()
                              if str(k).strip().startswith('shipment_order_volume_array.') and v != ''}
            if colunas_volume:
                if 'shipment_order_volume_array.volume_name' in colunas_volume:
                    colunas_volume['shipment_order_volume_array.name'] = colunas_volume.pop(
                        'shipment_order_volume_array.volume_name')
                for chave_completa, valor in colunas_volume.items():
                    path = chave_completa.replace('shipment_order_volume_array.', '', 1).split('.')
                    final_value = convert_value_type(path[-1], valor)
                    set_nested_value(volume_obj, path, final_value)
                volumes_list.append(volume_obj)

        payload_base['shipment_order_volume_array'] = volumes_list
        lista_de_requisicoes.append(payload_base)

    return lista_de_requisicoes


def enviar_requisicoes_planilha(api_key, requisicoes, label_status):
    url = "https://api.intelipost.com.br/api/v1/shipment_order"
    headers = {"Accept": "application/json", "Content-Type": "application/json; charset=utf-8", "api-key": api_key}

    total, sucesso = len(requisicoes), 0
    erros = []

    label_status.configure(text="🔄 Processando pedidos...")
    app.update()

    for i, req_payload in enumerate(requisicoes, 1):
        order_number = req_payload.get("order_number", "(sem número)")
        try:
            data = json.dumps(req_payload, default=json_serial, ensure_ascii=False)
            response = requests.post(url, headers=headers, data=data.encode('utf-8'), timeout=30)
            response.raise_for_status()
            resp_json = response.json()
            if 'error' not in resp_json:
                sucesso += 1
            else:
                erros.append(f"Pedido {order_number}: {resp_json.get('error')}")
        except Exception as e:
            erros.append(f"Pedido {order_number}: {e}")

        label_status.configure(text=f"📊 Processando... {i}/{total}")
        app.update()

    if sucesso == total:
        messagebox.showinfo("Sucesso", f"✅ Todos os {total} pedidos importados!")
    else:
        messagebox.showwarning("Aviso", f"✅ {sucesso}/{total} pedidos importados com sucesso\n❌ {len(erros)} erros")


# ===================== INTERFACE 3D COMPLETA =====================

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🚚 Manager Pro - Interface 3D")
        self.geometry("950x750")
        self.resizable(True, True)

        self.config_intelipost = load_config_intelipost()
        self.api_key_auth = carregar_config_auth()

        self.create_interface()
        self.app = self  # Referência global para funções

    def create_interface(self):
        # Título principal
        self.title_label = ctk.CTkLabel(self, text="🚚 Manager Pro",
                                        font=ctk.CTkFont(size=28, weight="bold"))
        self.title_label.pack(pady=20)

        # Main frame com scroll
        self.main_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # ========== ABA 1: OPERAÇÕES RÁPIDAS (5 BOTÕES) ==========
        frame_intelipost = ctk.CTkFrame(self.main_frame, corner_radius=15)
        frame_intelipost.pack(fill="x", pady=(0, 20))

        title_ip = ctk.CTkLabel(frame_intelipost, text="⚡ Operações Rápidas CSV (5 Funções)",
                                font=ctk.CTkFont(size=20, weight="bold"))
        title_ip.pack(pady=15)

        # API Key Intelipost
        frame_apikey = ctk.CTkFrame(frame_intelipost)
        frame_apikey.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(frame_apikey, text="🔑 ApiKey Intelipost:",
                     font=ctk.CTkFont(size=14)).pack(side="left", padx=10, pady=10)
        self.entry_apikey_ip = ctk.CTkEntry(frame_apikey, width=450, placeholder_text="Cole sua ApiKey aqui...")
        self.entry_apikey_ip.pack(side="left", padx=10, pady=10)

        if self.config_intelipost.get("ApiKey"):
            self.entry_apikey_ip.insert(0, "******** (oculta)")
            self.entry_apikey_ip.configure(state="disabled")

        # Arquivo CSV
        self.frame_csv = ctk.CTkFrame(frame_intelipost)
        self.frame_csv.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(self.frame_csv, text="📄 Arquivo CSV:",
                     font=ctk.CTkFont(size=14)).pack(side="left", padx=10, pady=10)
        self.entry_csv = ctk.CTkEntry(self.frame_csv, width=450, placeholder_text="Selecione um arquivo CSV...")
        self.entry_csv.pack(side="left", padx=10, pady=10)

        self.btn_csv = ctk.CTkButton(self.frame_csv, text="📁 Procurar", width=120,
                                     command=self.selecionar_csv)
        self.btn_csv.pack(side="left", padx=10, pady=10)

        # BOTÕES 3D - Todas as funcionalidades!
        frame_botoes = ctk.CTkFrame(frame_intelipost)
        frame_botoes.pack(fill="x", padx=20, pady=20)

        # Linha 1
        ctk.CTkButton(
            frame_botoes,
            text="✅ Pronto para Envio",
            width=180,
            height=55,
            command=lambda: enviar_pedidos(self.entry_csv, self.entry_apikey_ip),
            fg_color="#4CAF50",
            hover_color="#45a049",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=10, pady=10)

        ctk.CTkButton(
            frame_botoes,
            text="🚚 Despachado",
            width=180,
            height=55,
            command=lambda: enviar_pedidos_despachado(self.entry_csv, self.entry_apikey_ip),
            fg_color="#FF9800",
            hover_color="#e68900",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=10, pady=10)

        ctk.CTkButton(
            frame_botoes,
            text="📦 Entregue",
            width=180,
            height=55,
            command=lambda: enviar_pedidos_entregue(self.entry_csv, self.entry_apikey_ip),
            fg_color="#9C27B0",
            hover_color="#7B1FA2",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=10, pady=10)

        # Linha 2
        ctk.CTkButton(
            frame_botoes,
            text="❌ Cancelar Pedidos",
            width=180,
            height=55,
            command=lambda: cancelar_pedidos(self.entry_csv, self.entry_apikey_ip),
            fg_color="#f44336",
            hover_color="#da190b",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=10, pady=10)

        ctk.CTkButton(
            frame_botoes,
            text="🔄 Alterar Transportadora",
            width=200,
            height=55,
            command=lambda: alterar_transportadora(self.entry_csv, self.entry_apikey_ip),
            fg_color="#2196F3",
            hover_color="#1976D2",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=10, pady=10)

        ctk.CTkLabel(
            frame_botoes,
            text="📋 CSV precisa: 'Pedido' | 'Pedido,Transportadora' (para alterar)",
            font=ctk.CTkFont(size=12)
        ).pack(side="left", padx=20, pady=15)

        # ========== ABA 2: PLANILHA EXCEL ==========
        frame_planilha = ctk.CTkFrame(self.main_frame, corner_radius=15)
        frame_planilha.pack(fill="x", pady=(0, 20))

        title_planilha = ctk.CTkLabel(frame_planilha, text="📊 Importador Avançado Excel",
                                      font=ctk.CTkFont(size=20, weight="bold"))
        title_planilha.pack(pady=15)

        # Auth da planilha
        frame_auth = ctk.CTkFrame(frame_planilha)
        frame_auth.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(frame_auth, text="🔑 ApiKey Planilha:",
                     font=ctk.CTkFont(size=14)).pack(side="left", padx=10, pady=10)
        self.entry_api_auth = ctk.CTkEntry(frame_auth, width=450, show="*",
                                           placeholder_text="Cole sua ApiKey aqui...")
        self.entry_api_auth.pack(side="left", padx=10, pady=10)

        if self.api_key_auth:
            self.entry_api_auth.insert(0, self.api_key_auth[:4] + "..." + self.api_key_auth[-4:])
            self.entry_api_auth.configure(state="disabled")

        # Seleção Excel
        self.frame_excel = ctk.CTkFrame(frame_planilha)
        self.frame_excel.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(self.frame_excel, text="📈 Planilha Excel:",
                     font=ctk.CTkFont(size=14)).pack(side="left", padx=10, pady=10)
        self.entry_excel = ctk.CTkEntry(self.frame_excel, width=450,
                                        placeholder_text="Selecione arquivo Excel...")
        self.entry_excel.pack(side="left", padx=10, pady=10)

        self.btn_excel = ctk.CTkButton(self.frame_excel, text="📁 Selecionar", width=120,
                                       command=self.selecionar_excel)
        self.btn_excel.pack(side="left", padx=10, pady=10)

        frame_import = ctk.CTkFrame(frame_planilha)
        frame_import.pack(fill="x", padx=20, pady=20)

        self.btn_importar = ctk.CTkButton(frame_import, text="🚀 IMPORTAR PEDIDOS", width=300, height=60,
                                          command=self.importar_pedidos_avancado,
                                          fg_color="#2196F3", hover_color="#1976D2",
                                          font=ctk.CTkFont(size=16, weight="bold"))
        self.btn_importar.pack(pady=20)

        self.label_status = ctk.CTkLabel(frame_import, text="✅ Pronto para importar",
                                         font=ctk.CTkFont(size=14))
        self.label_status.pack(pady=5)

    def selecionar_csv(self):
        caminho = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if caminho:
            self.entry_csv.delete(0, "end")
            self.entry_csv.insert(0, caminho)

    def selecionar_excel(self):
        caminho = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx *.xls")])
        if caminho:
            self.entry_excel.delete(0, "end")
            self.entry_excel.insert(0, caminho)

    def importar_pedidos_avancado(self):
        api_key = self.entry_api_auth.get().strip()
        if not api_key:
            messagebox.showwarning("Atenção", "❌ Informe a ApiKey da planilha!")
            return

        arquivo = self.entry_excel.get().strip()
        if not os.path.exists(arquivo):
            messagebox.showerror("Erro", "❌ Selecione um arquivo Excel válido!")
            return

        try:
            requisicoes = processar_planilha(arquivo)
            if not requisicoes:
                messagebox.showinfo("Aviso", "Nenhuma requisição gerada!")
                return
            enviar_requisicoes_planilha(api_key, requisicoes, self.label_status)
            self.label_status.configure(text="✅ Importação concluída!")
        except Exception as e:
            messagebox.showerror("Erro", f"❌ Erro ao processar: {e}")


if __name__ == "__main__":
    app = App()
    app.mainloop()

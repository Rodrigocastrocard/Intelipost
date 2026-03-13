import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from tkinter import ttk
import pandas as pd
import configparser
import os
import requests
import math
import base64


CONFIG_FILE = "config.ini"


# ================== CONFIG / API KEY ==================

def get_apikey():
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
        encoded = config.get("API", "KEY", fallback=None)
        if not encoded:
            return None
        try:
            return base64.b64decode(encoded.encode("utf-8")).decode("utf-8")
        except Exception:
            # se der erro (arquivo antigo em texto puro, por exemplo),
            # retorna o valor original para manter compatibilidade
            return encoded
    return None


def set_apikey(apikey):
    encoded = base64.b64encode(apikey.encode("utf-8")).decode("utf-8")
    config = configparser.ConfigParser()
    config["API"] = {"KEY": encoded}
    with open(CONFIG_FILE, "w") as configfile:
        config.write(configfile)


# ================== CHAMADAS API ==================

def patch_pudo(pudo_id, enable, apikey):
    url = f"https://api.intelipost.com.br/api/v1/pudos/external_id/{pudo_id}/enabled"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "api-key": apikey
    }
    payload = {"value": enable}
    response = requests.patch(url, headers=headers, json=payload)
    return response


def post_pudo(data, apikey):
    url = "https://api.intelipost.com.br/api/v1/pudos"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "api-key": apikey,
        "logistic-provider-api-key": "",
        "lp-root-api-key": ""
    }
    response = requests.post(url, headers=headers, json=data)
    return response


def get_pudos(apikey):
    url = "https://api.intelipost.com.br/api/v1/pudos?all=true"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "api-key": apikey
    }
    response = requests.get(url, headers=headers, timeout=30)
    return response


def get_pudo_by_external_id(external_id, apikey):
    url = f"https://api.intelipost.com.br/api/v1/pudos/external_id/{external_id}"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "api-key": apikey
    }
    response = requests.get(url, headers=headers, timeout=30)
    return response


# ================== MONTAGEM DO JSON (PLANILHA) ==================

def montar_json(row):
    raw_dm = str(row.get("delivery_method_ids", "")).strip()
    delivery_method_ids = []
    if raw_dm:
        partes = raw_dm.split(",")
        for part in partes:
            cleaned = part.strip()
            if cleaned == "":
                continue
            try:
                num = int(cleaned)
                delivery_method_ids.append(num)
            except ValueError:
                try:
                    num = int(float(cleaned))
                    delivery_method_ids.append(num)
                except ValueError:
                    print("ERRO: delivery_method_id inválido, ignorado:", cleaned)

    pudo = {
        "external_id": row.get("external_id"),
        "delivery_method_ids": delivery_method_ids,
        "type": row.get("type"),
        "federal_tax_payer_id": row.get("federal_tax_payer_id"),
        "state_tax_payer_id": row.get("state_tax_payer_id"),
        "name": row.get("name"),
        "official_name": row.get("official_name"),
        "phone": row.get("phone"),
        "email": row.get("email"),
        "map_icon_image": row.get("map_icon_image"),
        "observation": row.get("observation"),
        "responsible_name": row.get("responsible_name"),
    }

    # instructions.*
    instructions = {}
    for campo in ["receipt", "posting_tag", "pickup"]:
        val = row.get(f"instructions.{campo}", None)
        if val is not None and val != "" and not (
            isinstance(val, float) and math.isnan(val)
        ):
            instructions[campo] = val
    if instructions:
        pudo["instructions"] = instructions

    # facilities.*
    facilities = {}
    for campo in [
        "parking",
        "accessibility",
        "air_conditioned",
        "free_parking",
        "close_to_subway",
    ]:
        val = row.get(f"facilities.{campo}", None)
        if val is not None and val != "" and not (
            isinstance(val, float) and math.isnan(val)
        ):
            facilities[campo] = str(val).strip().lower() in ["true", "1", "yes", "sim"]
    if facilities:
        pudo["facilities"] = facilities

    # location.*
    location = {}
    for campo in [
        "street",
        "reference",
        "additional_information",
        "number",
        "country",
        "state_code",
        "city",
        "quarter",
        "zip_code",
        "latitude",
        "longitude",
    ]:
        val = row.get(f"location.{campo}", None)
        if val is None or val == "" or (isinstance(val, float) and math.isnan(val)):
            continue

        if campo == "zip_code":
            cep_str = str(val).strip()
            cep_digits = "".join(ch for ch in cep_str if ch.isdigit())
            if len(cep_digits) == 7:
                cep_digits = cep_digits.zfill(8)
            if len(cep_digits) == 8:
                cep_formatado = f"{cep_digits[:5]}-{cep_digits[5:]}"
                location[campo] = cep_formatado
            else:
                location[campo] = cep_str
        else:
            location[campo] = val

    imgs = row.get("location.images", None)
    if imgs and not (isinstance(imgs, float) and math.isnan(imgs)):
        location["images"] = [x.strip() for x in str(imgs).split(",") if x.strip()]

    if location:
        pudo["location"] = location

    # working_hours via planilha (opcional)
    return pudo


# ================== APP TKINTER ==================

class PudoApp:

    def montar_json_formulario(self):
        dm_str = self.entry_dm_form.get().strip()
        dm_list = []
        if dm_str:
            for part in dm_str.split(","):
                part = part.strip()
                if not part:
                    continue
                try:
                    dm_list.append(int(part))
                except ValueError:
                    try:
                        dm_list.append(int(float(part)))
                    except ValueError:
                        print("delivery_method_id inválido no formulário:", part)

        pudo = {
            "external_id": self.entry_ext_id_form.get().strip() or None,
            "delivery_method_ids": dm_list,
            "type": self.entry_type_form.get().strip() or None,
            "federal_tax_payer_id": self.entry_federal_form.get().strip() or None,
            "state_tax_payer_id": self.entry_state_form.get().strip() or None,
            "name": self.entry_name_form.get().strip() or None,
            "official_name": self.entry_official_form.get().strip() or None,
            "phone": self.entry_phone_form.get().strip() or None,
            "email": self.entry_email_form.get().strip() or None,
            "map_icon_image": self.entry_mapicon_form.get().strip() or None,
            "observation": self.entry_obs_form.get().strip() or None,
            "responsible_name": self.entry_resp_form.get().strip() or None,
        }

        pickup = self.entry_pickup_form.get().strip()
        if pickup:
            pudo["instructions"] = {"pickup": pickup}

        def to_bool(val):
            return str(val).strip().lower() in ["true", "1", "yes", "sim"]

        facilities = {}
        val = self.entry_parking_form.get().strip()
        if val:
            facilities["parking"] = to_bool(val)
        val = self.entry_access_form.get().strip()
        if val:
            facilities["accessibility"] = to_bool(val)
        val = self.entry_air_form.get().strip()
        if val:
            facilities["air_conditioned"] = to_bool(val)
        val = self.entry_freepark_form.get().strip()
        if val:
            facilities["free_parking"] = to_bool(val)
        val = self.entry_subway_form.get().strip()
        if val:
            facilities["close_to_subway"] = to_bool(val)

        if facilities:
            pudo["facilities"] = facilities

        location = {}
        street = self.entry_street_form.get().strip()
        if street:
            location["street"] = street
        number = self.entry_number_form.get().strip()
        if number:
            location["number"] = number
        addinfo = self.entry_addinfo_form.get().strip()
        if addinfo:
            location["additional_information"] = addinfo
        ref = self.entry_ref_form.get().strip()
        if ref:
            location["reference"] = ref
        country = self.entry_country_form.get().strip()
        if country:
            location["country"] = country
        state_code = self.entry_statecode_form.get().strip()
        if state_code:
            location["state_code"] = state_code
        city = self.entry_city_form.get().strip()
        if city:
            location["city"] = city
        quarter = self.entry_quarter_form.get().strip()
        if quarter:
            location["quarter"] = quarter
        zip_code = self.entry_zip_form.get().strip()
        if zip_code:
            location["zip_code"] = zip_code
        lat = self.entry_lat_form.get().strip()
        if lat:
            location["latitude"] = lat
        lon = self.entry_lon_form.get().strip()
        if lon:
            location["longitude"] = lon

        imgs = self.entry_imgs_form.get().strip()
        if imgs:
            location["images"] = [x.strip() for x in imgs.split(",") if x.strip()]

        if location:
            pudo["location"] = location

        # ---------- working_hours ----------
        working_hours = {}

        def read_day(prefix, json_key):
            start = getattr(self, f"{prefix}_start").get().strip()
            lunch_start = getattr(self, f"{prefix}_lunch_start").get().strip()
            lunch_end = getattr(self, f"{prefix}_lunch_end").get().strip()
            end = getattr(self, f"{prefix}_end").get().strip()

            day_data = {}
            if start:
                day_data["start"] = start
            if lunch_start:
                day_data["lunch_time_start"] = lunch_start
            if lunch_end:
                day_data["lunch_time_end"] = lunch_end
            if end:
                day_data["end"] = end

            if day_data:
                working_hours[json_key] = day_data

        read_day("monday", "monday")
        read_day("tuesday", "tuesday")
        read_day("wednesday", "wednesday")
        read_day("thursday", "thursday")
        read_day("friday", "friday")
        read_day("saturday", "saturday")
        read_day("sunday", "sunday")

        if working_hours:
            pudo["working_hours"] = working_hours

        return pudo

    def __init__(self, root):
        self.root = root
        root.title("Gerenciador de Pudo")

        try:
            root.state("zoomed")
        except Exception:
            root.attributes("-zoomed", True)

        self.file_path = None
        self.data = None
        self.linhas_consulta = []
        self.last_full_response_text = None

        main_frame = tk.Frame(root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        left_frame = tk.Frame(main_frame)
        left_frame.pack(side="left", fill="y", expand=True, padx=(0, 10))

        right_frame = tk.Frame(main_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))

        self.btn_cadastro_tela = tk.Button(
            left_frame,
            text="Tela de Cadastro de Lojas",
            width=30,
            command=self.abrir_tela_cadastro,
        )
        self.btn_cadastro_tela.pack(pady=10, anchor="w")

        self.btn_consultar = tk.Button(
            left_frame,
            text="Consultar Lojas (Ativas)",
            width=30,
            command=self.consultar_pudos,
        )
        self.btn_consultar.pack(pady=10, anchor="w")

        lbl = tk.Label(left_frame, text="Consultar por external_id:")
        lbl.pack(pady=(20, 0), anchor="w")

        self.entry_external_id = tk.Entry(left_frame, width=20)
        self.entry_external_id.pack(pady=5, anchor="w")

        self.btn_consultar_unica = tk.Button(
            left_frame,
            text="Consultar loja por código",
            width=30,
            command=self.consultar_pudo_por_external_id,
        )
        self.btn_consultar_unica.pack(pady=5, anchor="w")

        top_right = tk.Frame(right_frame)
        top_right.pack(fill="x")

        self.btn_ativar = tk.Button(
            top_right,
            text="Ativar Loja",
            width=15,
            command=self.ativar_pudo,
        )
        self.btn_ativar.pack(pady=10, side="left", anchor="w")

        self.btn_inativar = tk.Button(
            top_right,
            text="Desativar Loja",
            width=15,
            command=self.inativar_pudo,
        )
        self.btn_inativar.pack(pady=10, side="left", padx=5, anchor="w")

        table_frame = tk.Frame(right_frame)
        table_frame.pack(fill="both", expand=True)

        # *** Grid com delivery_method_ids ***
        cols = ("external_id", "name", "enabled", "delivery_method_ids")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        self.tree.heading("external_id", text="external_id")
        self.tree.heading("name", text="name")
        self.tree.heading("enabled", text="enabled")
        self.tree.heading("delivery_method_ids", text="delivery_method_ids")

        self.tree.column("external_id", width=150, anchor="w")
        self.tree.column("name", width=250, anchor="w")
        self.tree.column("enabled", width=80, anchor="center")
        self.tree.column("delivery_method_ids", width=150, anchor="center")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        btn_salvar = tk.Button(
            right_frame,
            text="Salvar resultado em TXT",
            command=self.salvar_resultado_txt,
        )
        btn_salvar.pack(pady=5, anchor="e")

        self.apikey = get_apikey()
        if not self.apikey:
            self.btn_apikey = tk.Button(
                root,
                text="Informar API Key",
                width=30,
                command=self.inform_apikey,
            )
            self.btn_apikey.pack(pady=5)

    # ========== Tela de cadastro (3 colunas) ==========

    def abrir_tela_cadastro(self):
        win = tk.Toplevel(self.root)
        win.title("Cadastro de Lojas (PUDOs)")
        win.geometry("1300x650")

        main = tk.Frame(win)
        main.pack(fill="both", expand=True, padx=20, pady=20)

        btn_frame = tk.Frame(main)
        btn_frame.pack(fill="x", pady=(0, 15), anchor="w")

        btn_cadastrar_form = tk.Button(
            btn_frame,
            text="Cadastrar Loja",
            command=self.cadastrar_pudo_form,
        )
        btn_cadastrar_form.pack(side="left", padx=5)

        btn_browse = tk.Button(
            btn_frame,
            text="Selecionar Planilha Excel",
            command=self.browse_file,
        )
        btn_browse.pack(side="left", padx=5)

        btn_cadastrar_planilha = tk.Button(
            btn_frame,
            text="Cadastrar via Planilha",
            command=self.cadastrar_pudo,
        )
        btn_cadastrar_planilha.pack(side="left", padx=5)

        col1 = tk.Frame(main)
        col1.pack(side="left", fill="both", expand=True, padx=(0, 10))

        col2 = tk.Frame(main)
        col2.pack(side="left", fill="both", expand=True, padx=10)

        col3 = tk.Frame(main)
        col3.pack(side="left", fill="both", expand=True, padx=(10, 0))

        # COLUNA 1
        r1 = 0
        tk.Label(col1, text="Código: *").grid(row=r1, column=0, sticky="e", pady=2)
        self.entry_ext_id_form = tk.Entry(col1, width=30)
        self.entry_ext_id_form.grid(row=r1, column=1, sticky="w", pady=2)
        r1 += 1

        tk.Label(col1, text="Métodos de Entrega (ex: 32,374): *").grid(row=r1, column=0, sticky="e", pady=2)
        self.entry_dm_form = tk.Entry(col1, width=30)
        self.entry_dm_form.grid(row=r1, column=1, sticky="w", pady=2)
        r1 += 1

        tk.Label(col1, text="Tipo: *").grid(row=r1, column=0, sticky="e", pady=2)
        self.entry_type_form = tk.Entry(col1, width=30)
        self.entry_type_form.insert(0, "POINT")
        self.entry_type_form.grid(row=r1, column=1, sticky="w", pady=2)
        r1 += 1

        tk.Label(col1, text="CNPJ: *").grid(row=r1, column=0, sticky="e", pady=2)
        self.entry_federal_form = tk.Entry(col1, width=30)
        self.entry_federal_form.grid(row=r1, column=1, sticky="w", pady=2)
        r1 += 1

        tk.Label(col1, text="Inscrição Estadual: *").grid(row=r1, column=0, sticky="e", pady=2)
        self.entry_state_form = tk.Entry(col1, width=30)
        self.entry_state_form.grid(row=r1, column=1, sticky="w", pady=2)
        r1 += 1

        tk.Label(col1, text="Nome: *").grid(row=r1, column=0, sticky="e", pady=2)
        self.entry_name_form = tk.Entry(col1, width=30)
        self.entry_name_form.grid(row=r1, column=1, sticky="w", pady=2)
        r1 += 1

        tk.Label(col1, text="Razão Social: *").grid(row=r1, column=0, sticky="e", pady=2)
        self.entry_official_form = tk.Entry(col1, width=30)
        self.entry_official_form.grid(row=r1, column=1, sticky="w", pady=2)
        r1 += 1

        tk.Label(col1, text="Telefone:").grid(row=r1, column=0, sticky="e", pady=2)
        self.entry_phone_form = tk.Entry(col1, width=30)
        self.entry_phone_form.grid(row=r1, column=1, sticky="w", pady=2)
        r1 += 1

        tk.Label(col1, text="email:").grid(row=r1, column=0, sticky="e", pady=2)
        self.entry_email_form = tk.Entry(col1, width=30)
        self.entry_email_form.grid(row=r1, column=1, sticky="w", pady=2)
        r1 += 1

        tk.Label(col1, text="Imagem (URL):").grid(row=r1, column=0, sticky="e", pady=2)
        self.entry_mapicon_form = tk.Entry(col1, width=30)
        self.entry_mapicon_form.grid(row=r1, column=1, sticky="w", pady=2)
        r1 += 1

        tk.Label(col1, text="Observação:").grid(row=r1, column=0, sticky="e", pady=2)
        self.entry_obs_form = tk.Entry(col1, width=30)
        self.entry_obs_form.grid(row=r1, column=1, sticky="w", pady=2)
        r1 += 1

        tk.Label(col1, text="Nome do Responsável:").grid(row=r1, column=0, sticky="e", pady=2)
        self.entry_resp_form = tk.Entry(col1, width=30)
        self.entry_resp_form.grid(row=r1, column=1, sticky="w", pady=2)
        r1 += 1

        tk.Label(col1, text="Pickup:").grid(row=r1, column=0, sticky="e", pady=2)
        self.entry_pickup_form = tk.Entry(col1, width=30)
        self.entry_pickup_form.grid(row=r1, column=1, sticky="w", pady=2)
        r1 += 1

        # COLUNA 2
        r2 = 0
        tk.Label(col2, text="Estacionamento (true/false):").grid(row=r2, column=0, sticky="e", pady=2)
        self.entry_parking_form = tk.Entry(col2, width=10)
        self.entry_parking_form.insert(0, "true")
        self.entry_parking_form.grid(row=r2, column=1, sticky="w", pady=2)
        r2 += 1

        tk.Label(col2, text="Acessibilidade (true/false):").grid(row=r2, column=0, sticky="e", pady=2)
        self.entry_access_form = tk.Entry(col2, width=10)
        self.entry_access_form.insert(0, "false")
        self.entry_access_form.grid(row=r2, column=1, sticky="w", pady=2)
        r2 += 1

        tk.Label(col2, text="Ar Condicionado (true/false):").grid(row=r2, column=0, sticky="e", pady=2)
        self.entry_air_form = tk.Entry(col2, width=10)
        self.entry_air_form.insert(0, "true")
        self.entry_air_form.grid(row=r2, column=1, sticky="w", pady=2)
        r2 += 1

        tk.Label(col2, text="Estacionamento Grátis (true/false):").grid(row=r2, column=0, sticky="e", pady=2)
        self.entry_freepark_form = tk.Entry(col2, width=10)
        self.entry_freepark_form.insert(0, "false")
        self.entry_freepark_form.grid(row=r2, column=1, sticky="w", pady=2)
        r2 += 1

        tk.Label(col2, text="Perto do Metrô (true/false):").grid(row=r2, column=0, sticky="e", pady=2)
        self.entry_subway_form = tk.Entry(col2, width=10)
        self.entry_subway_form.insert(0, "true")
        self.entry_subway_form.grid(row=r2, column=1, sticky="w", pady=2)
        r2 += 1

        tk.Label(col2, text="Rua: *").grid(row=r2, column=0, sticky="e", pady=2)
        self.entry_street_form = tk.Entry(col2, width=30)
        self.entry_street_form.grid(row=r2, column=1, sticky="w", pady=2)
        r2 += 1

        tk.Label(col2, text="Numero: *").grid(row=r2, column=0, sticky="e", pady=2)
        self.entry_number_form = tk.Entry(col2, width=10)
        self.entry_number_form.grid(row=r2, column=1, sticky="w", pady=2)
        r2 += 1

        tk.Label(col2, text="Info. Adicional:").grid(row=r2, column=0, sticky="e", pady=2)
        self.entry_addinfo_form = tk.Entry(col2, width=30)
        self.entry_addinfo_form.grid(row=r2, column=1, sticky="w", pady=2)
        r2 += 1

        tk.Label(col2, text="Referencia:").grid(row=r2, column=0, sticky="e", pady=2)
        self.entry_ref_form = tk.Entry(col2, width=30)
        self.entry_ref_form.grid(row=r2, column=1, sticky="w", pady=2)
        r2 += 1

        tk.Label(col2, text="Cidade: *").grid(row=r2, column=0, sticky="e", pady=2)
        self.entry_country_form = tk.Entry(col2, width=10)
        self.entry_country_form.insert(0, "BRA")
        self.entry_country_form.grid(row=r2, column=1, sticky="w", pady=2)
        r2 += 1

        tk.Label(col2, text="Estado: *").grid(row=r2, column=0, sticky="e", pady=2)
        self.entry_statecode_form = tk.Entry(col2, width=5)
        self.entry_statecode_form.grid(row=r2, column=1, sticky="w", pady=2)
        r2 += 1

        tk.Label(col2, text="Cidade: *").grid(row=r2, column=0, sticky="e", pady=2)
        self.entry_city_form = tk.Entry(col2, width=30)
        self.entry_city_form.grid(row=r2, column=1, sticky="w", pady=2)
        r2 += 1

        tk.Label(col2, text="Bairro: *").grid(row=r2, column=0, sticky="e", pady=2)
        self.entry_quarter_form = tk.Entry(col2, width=30)
        self.entry_quarter_form.grid(row=r2, column=1, sticky="w", pady=2)
        r2 += 1

        tk.Label(col2, text="CEP: *").grid(row=r2, column=0, sticky="e", pady=2)
        self.entry_zip_form = tk.Entry(col2, width=15)
        self.entry_zip_form.grid(row=r2, column=1, sticky="w", pady=2)
        r2 += 1

        tk.Label(col2, text="Latitude: *").grid(row=r2, column=0, sticky="e", pady=2)
        self.entry_lat_form = tk.Entry(col2, width=15)
        self.entry_lat_form.grid(row=r2, column=1, sticky="w", pady=2)
        r2 += 1

        tk.Label(col2, text="Longitude: *").grid(row=r2, column=0, sticky="e", pady=2)
        self.entry_lon_form = tk.Entry(col2, width=15)
        self.entry_lon_form.grid(row=r2, column=1, sticky="w", pady=2)
        r2 += 1

        tk.Label(col2, text="Imagens (URLs separadas por vírgula):").grid(
            row=r2, column=0, sticky="e", pady=2
        )
        self.entry_imgs_form = tk.Entry(col2, width=40)
        self.entry_imgs_form.grid(row=r2, column=1, sticky="w", pady=2)
        r2 += 1

        # COLUNA 3 - working_hours
        r3 = 0
        tk.Label(col3, text="Horário de funcionamento").grid(
            row=r3, column=0, columnspan=6, sticky="w", pady=(0, 5)
        )
        r3 += 1

        def add_day_row(day_label, attr_prefix):
            nonlocal r3
            tk.Label(col3, text=day_label).grid(row=r3, column=0, sticky="e", pady=2, padx=(0, 5))

            entry_start = tk.Entry(col3, width=6)
            entry_start.grid(row=r3, column=1, sticky="w", pady=2)

            entry_lunch_start = tk.Entry(col3, width=6)
            entry_lunch_start.grid(row=r3, column=2, sticky="w", pady=2)

            entry_lunch_end = tk.Entry(col3, width=6)
            entry_lunch_end.grid(row=r3, column=3, sticky="w", pady=2)

            entry_end = tk.Entry(col3, width=6)
            entry_end.grid(row=r3, column=4, sticky="w", pady=2)

            setattr(self, f"{attr_prefix}_start", entry_start)
            setattr(self, f"{attr_prefix}_lunch_start", entry_lunch_start)
            setattr(self, f"{attr_prefix}_lunch_end", entry_lunch_end)
            setattr(self, f"{attr_prefix}_end", entry_end)

            r3 += 1

        add_day_row("Segunda", "monday")
        add_day_row("Terça", "tuesday")
        add_day_row("Quarta", "wednesday")
        add_day_row("Quinta", "thursday")
        add_day_row("Sexta", "friday")
        add_day_row("Sabado", "saturday")
        add_day_row("Domingo", "sunday")

    # ========== Planilha / Cadastro ==========

    def browse_file(self):
        self.file_path = filedialog.askopenfilename(
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        if self.file_path:
            print(f"Arquivo selecionado: {self.file_path}")
            self.data = pd.read_excel(self.file_path)
            print(self.data.head())

    def cadastrar_pudo(self):
        if not self.file_path:
            messagebox.showerror("Erro", "Selecione uma planilha antes de cadastrar.")
            return

        apikey = get_apikey()
        if not apikey:
            messagebox.showerror("Erro", "API Key não informada.")
            return

        try:
            df = pd.read_excel(
                self.file_path, converters={"delivery_method_ids": str}
            ).fillna("")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao ler planilha: {e}")
            return

        log_path = os.path.join(
            os.path.dirname(self.file_path),
            "pudos_enviados.txt",
        )

        sucesso = 0
        erro = 0

        with open(log_path, "w", encoding="utf-8") as log_file:
            log_file.write("LOG DE PUDOS ENVIADOS PARA API\n\n")

            for idx, row in df.iterrows():
                pudo_json = montar_json(row)

                log_file.write(
                    f"==== LINHA {idx + 1} | external_id={pudo_json.get('external_id')} ====\n"
                )
                log_file.write(repr(pudo_json) + "\n\n")

                resposta = post_pudo(pudo_json, apikey)

                if resposta.status_code in (200, 201):
                    sucesso += 1
                else:
                    erro += 1
                    log_file.write(
                        f"ERRO NA CRIAÇÃO (status {resposta.status_code}):\n"
                    )
                    log_file.write(resposta.text + "\n\n")
                    print(
                        f"Erro ao cadastrar loja {pudo_json.get('external_id')} "
                        f"(linha {idx + 1}):\nStatus: {resposta.status_code}\n{resposta.text}"
                    )

        messagebox.showinfo(
            "Cadastro de lojas",
            f"Cadastradas com sucesso: {sucesso}\nFalhas: {erro}\n"
            f"Detalhes gravados em: {log_path}",
        )

    # ========== Cadastro via formulário ==========

    def cadastrar_pudo_form(self):
        apikey = get_apikey()
        if not apikey:
            messagebox.showerror("Erro", "API Key não informada.")
            return

        pudo_json = self.montar_json_formulario()

        if not pudo_json.get("external_id"):
            messagebox.showwarning("Atenção", "Informe pelo menos o external_id.")
            return

        try:
            resp = post_pudo(pudo_json, apikey)
        except requests.RequestException as e:
            messagebox.showerror("Erro", f"Falha de conexão:\n{e}")
            return

        if resp.status_code in (200, 201):
            messagebox.showinfo(
                "Cadastro",
                f"Loja {pudo_json.get('external_id')} cadastrada com sucesso!",
            )
        else:
            messagebox.showerror(
                "Erro",
                f"Falha ao cadastrar loja.\nStatus Code: {resp.status_code}\n{resp.text}",
            )

    # ========== Consultas ==========

    # consulta de PUDOs (todas) preenche grid principal
    def consultar_pudos(self):
        apikey = get_apikey()
        if not apikey:
            messagebox.showerror("Erro", "API Key não informada.")
            return

        try:
            resp = get_pudos(apikey)
        except requests.RequestException as e:
            messagebox.showerror("Erro", f"Falha de conexão:\n{e}")
            return

        if resp.status_code != 200:
            messagebox.showerror(
                "Erro",
                f"Falha ao consultar lojas.\nStatus Code: {resp.status_code}\n{resp.text}",
            )
            return

        # guarda o response bruto para possível exportação
        self.last_full_response_text = resp.text

        try:
            dados = resp.json()
        except ValueError:
            messagebox.showerror("Erro", "Resposta da API não é um JSON válido.")
            return

        try:
            items = dados.get("content", {}).get("items", [])
        except AttributeError:
            messagebox.showerror("Erro", "Formato inesperado do JSON de retorno.")
            return

        # monta lista com external_id, name, enabled, delivery_method_ids
        self.linhas_consulta = []
        for item in items:
            external_id = item.get("externalid") or item.get("external_id")
            name = item.get("name")
            enabled = item.get("enabled")
            dm_ids = item.get("delivery_method_ids") or item.get("deliveryMethodIds")

            external_id_str = "" if external_id is None else str(external_id)
            name_str = "" if name is None else str(name)
            enabled_str = "" if enabled is None else str(enabled)

            # converte lista de dm_ids para string
            if isinstance(dm_ids, (list, tuple)):
                dm_str = ",".join(str(x) for x in dm_ids)
            else:
                dm_str = "" if dm_ids is None else str(dm_ids)

            self.linhas_consulta.append(
                (external_id_str, name_str, enabled_str, dm_str)
            )

        # limpa grid
        for row in self.tree.get_children():
            self.tree.delete(row)

        # preenche grid
        for ext_id, nome, enabled_str, dm_str in self.linhas_consulta:
            self.tree.insert("", "end", values=(ext_id, nome, enabled_str, dm_str))

        if not self.linhas_consulta:
            messagebox.showinfo("Consulta de lojas", "Nenhuma loja retornada.")
            return

        # pergunta se deseja exportar o response completo
        if messagebox.askyesno(
                "Exportar resultado",
                "Deseja exportar o resultado completo da consulta (json) para TXT?",
        ):
            self.exportar_ultimo_response()

    # consulta de um único PUDO por external_id
    def consultar_pudo_por_external_id(self):
        external_id = self.entry_external_id.get().strip()
        if not external_id:
            messagebox.showwarning("Atenção", "Informe um external_id.")
            return

        apikey = get_apikey()
        if not apikey:
            messagebox.showerror("Erro", "API Key não informada.")
            return

        try:
            resp = get_pudo_by_external_id(external_id, apikey)
        except requests.RequestException as e:
            messagebox.showerror("Erro", f"Falha de conexão:\n{e}")
            return

        if resp.status_code != 200:
            messagebox.showerror(
                "Erro",
                f"Falha ao consultar loja.\nStatus Code: {resp.status_code}\n{resp.text}",
            )
            return

        # guarda o response bruto
        self.last_full_response_text = resp.text

        try:
            dado = resp.json()
        except ValueError:
            messagebox.showerror("Erro", "Resposta da API não é um JSON válido.")
            return

        content = dado.get("content")
        if not content:
            messagebox.showinfo("Consulta de loja", "Nenhuma loja retornada.")
            return

        external_id_val = content.get("external_id") or external_id
        name_val = content.get("name")
        enabled_val = content.get("enabled")
        dm_ids = content.get("delivery_method_ids") or content.get("deliveryMethodIds")

        external_id_str = "" if external_id_val is None else str(external_id_val)
        name_str = "" if name_val is None else str(name_val)
        enabled_str = "" if enabled_val is None else str(enabled_val)

        if isinstance(dm_ids, (list, tuple)):
            dm_str = ",".join(str(x) for x in dm_ids)
        else:
            dm_str = "" if dm_ids is None else str(dm_ids)

        # mesma estrutura usada em consultar_pudos (todas)
        self.linhas_consulta = [(external_id_str, name_str, enabled_str, dm_str)]

        # limpa grid e mostra só essa loja
        for row in self.tree.get_children():
            self.tree.delete(row)

        self.tree.insert("", "end", values=(external_id_str, name_str, enabled_str, dm_str))

        # pergunta se deseja exportar o response completo
        if messagebox.askyesno(
                "Exportar resultado",
                "Deseja exportar o resultado completo da consulta (json) para TXT?",
        ):
            self.exportar_ultimo_response()

    # salvar o resultado atual da consulta em TXT
    def salvar_resultado_txt(self):
        if not self.linhas_consulta:
            messagebox.showinfo("Salvar", "Não há resultados para salvar.")
            return

        caminho = filedialog.asksaveasfilename(
            title="Salvar resultado",
            defaultextension=".txt",
            filetypes=[("Arquivo de texto", "*.txt"), ("Todos os arquivos", "*.*")],
        )
        if not caminho:
            return

        try:
            with open(caminho, "w", encoding="utf-8") as f:
                f.write("external_id;name;enabled;delivery_method_ids\n")
                for ext_id, nome, enabled_str, dm_str in self.linhas_consulta:
                    f.write(f"{ext_id};{nome};{enabled_str};{dm_str}\n")
            messagebox.showinfo("Salvar", f"Arquivo salvo em:\n{caminho}")
        except OSError as e:
            messagebox.showerror("Erro", f"Falha ao salvar o arquivo:\n{e}")

    def exportar_ultimo_response(self):
        if not self.last_full_response_text:
            messagebox.showinfo(
                "Exportar",
                "Não há resultado de consulta para exportar."
            )
            return

        caminho = filedialog.asksaveasfilename(
            title="Salvar response completo",
            defaultextension=".txt",
            filetypes=[("Arquivo de texto", "*.txt"), ("Todos os arquivos", "*.*")],
        )
        if not caminho:
            return

        try:
            with open(caminho, "w", encoding="utf-8") as f:
                f.write(self.last_full_response_text)
            messagebox.showinfo("Exportar", f"Arquivo salvo em:\n{caminho}")
        except OSError as e:
            messagebox.showerror("Erro", f"Falha ao salvar o arquivo:\n{e}")

    # ========== Ativar / Inativar ==========

    def ativar_pudo(self):
        self.solicitar_id_unidade(True)

    def inativar_pudo(self):
        self.solicitar_id_unidade(False)

    def solicitar_id_unidade(self, enable):
        pudo_id = simpledialog.askstring(
            "ID da Unidade", "Informe o ID da unidade (external_id):"
        )
        if pudo_id:
            confirm = messagebox.askyesno(
                "Confirmação",
                f"Confirmar {'ativação' if enable else 'desativação'} da loja {pudo_id}?",
            )
            if confirm:
                apikey = get_apikey()
                if not apikey:
                    messagebox.showerror("Erro", "API Key não informada.")
                    return
                resp = patch_pudo(pudo_id, enable, apikey)
                if resp.status_code == 200:
                    messagebox.showinfo(
                        "Sucesso",
                        f"Loja {'ativada' if enable else 'desativada'} com sucesso!",
                    )
                else:
                    messagebox.showerror(
                        "Erro",
                        f"Falha ao {'ativar' if enable else 'desativar'} loja.\n"
                        f"Status Code: {resp.status_code}\n{resp.text}",
                    )

    # ========== API key ==========

    def inform_apikey(self):
        apikey = simpledialog.askstring(
            "API Key", "Informe sua API Key:", show="*"
        )
        if apikey:
            set_apikey(apikey)
            messagebox.showinfo("API Key", "API Key salva com sucesso!")
            if hasattr(self, "btn_apikey"):
                self.btn_apikey.pack_forget()
            self.apikey = apikey


if __name__ == "__main__":
    root = tk.Tk()
    app = PudoApp(root)
    root.mainloop()

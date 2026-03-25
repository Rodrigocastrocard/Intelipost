import streamlit as st
import pandas as pd
import configparser
import os
import requests
import math
import base64
from io import StringIO

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


def put_pudo(external_id, data, apikey):
    url = f"https://api.intelipost.com.br/api/v1/pudos/external_id/{external_id}"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "api-key": apikey,
        "logistic-provider-api-key": "",
        "lp-root-api-key": ""
    }
    response = requests.put(url, headers=headers, json=data)
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

    return pudo


# ================== MONTAGEM JSON (FORM STREAMLIT) ==================

def montar_json_formulario_streamlit(form_vals):
    dm_str = form_vals["delivery_method_ids"].strip()
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
        "external_id": form_vals["external_id"] or None,
        "delivery_method_ids": dm_list,
        "type": form_vals["type"] or None,
        "federal_tax_payer_id": form_vals["federal_tax_payer_id"] or None,
        "state_tax_payer_id": form_vals["state_tax_payer_id"] or None,
        "name": form_vals["name"] or None,
        "official_name": form_vals["official_name"] or None,
        "phone": form_vals["phone"] or None,
        "email": form_vals["email"] or None,
        "map_icon_image": form_vals["map_icon_image"] or None,
        "observation": form_vals["observation"] or None,
        "responsible_name": form_vals["responsible_name"] or None,
    }

    pickup = form_vals["pickup"].strip()
    if pickup:
        pudo["instructions"] = {"pickup": pickup}

    def to_bool(val):
        return str(val).strip().lower() in ["true", "1", "yes", "sim"]

    facilities = {}
    if form_vals["parking"]:
        facilities["parking"] = to_bool(form_vals["parking"])
    if form_vals["accessibility"]:
        facilities["accessibility"] = to_bool(form_vals["accessibility"])
    if form_vals["air_conditioned"]:
        facilities["air_conditioned"] = to_bool(form_vals["air_conditioned"])
    if form_vals["free_parking"]:
        facilities["free_parking"] = to_bool(form_vals["free_parking"])
    if form_vals["close_to_subway"]:
        facilities["close_to_subway"] = to_bool(form_vals["close_to_subway"])
    if facilities:
        pudo["facilities"] = facilities

    location = {}
    if form_vals["street"]:
        location["street"] = form_vals["street"]
    if form_vals["number"]:
        location["number"] = form_vals["number"]
    if form_vals["additional_information"]:
        location["additional_information"] = form_vals["additional_information"]
    if form_vals["reference"]:
        location["reference"] = form_vals["reference"]
    if form_vals["country"]:
        location["country"] = form_vals["country"]
    if form_vals["state_code"]:
        location["state_code"] = form_vals["state_code"]
    if form_vals["city"]:
        location["city"] = form_vals["city"]
    if form_vals["quarter"]:
        location["quarter"] = form_vals["quarter"]
    if form_vals["zip_code"]:
        location["zip_code"] = form_vals["zip_code"]
    if form_vals["latitude"]:
        location["latitude"] = form_vals["latitude"]
    if form_vals["longitude"]:
        location["longitude"] = form_vals["longitude"]

    imgs = form_vals["images"].strip()
    if imgs:
        location["images"] = [x.strip() for x in imgs.split(",") if x.strip()]

    if location:
        pudo["location"] = location

    # working_hours
    working_hours = {}
    for day in ["monday", "tuesday", "wednesday", "thursday",
                "friday", "saturday", "sunday"]:
        start = form_vals[f"{day}_start"].strip()
        lunch_start = form_vals[f"{day}_lunch_start"].strip()
        lunch_end = form_vals[f"{day}_lunch_end"].strip()
        end = form_vals[f"{day}_end"].strip()
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
            working_hours[day] = day_data

    if working_hours:
        pudo["working_hours"] = working_hours

    return pudo


# ================== PÁGINAS STREAMLIT ==================

def pagina_config():
    st.header("Configuração de API Key")
    apikey_atual = get_apikey()
    if apikey_atual:
        st.success("API Key já configurada (valor oculto).")
    nova = st.text_input("API Key", type="password")
    if st.button("Salvar API Key"):
        if not nova:
            st.error("Informe um valor para a API Key.")
        else:
            set_apikey(nova)
            st.success("API Key salva com sucesso!")


def pagina_cadastro_form():
    st.header("Cadastro de Loja (Formulário)")
    apikey = get_apikey()
    if not apikey:
        st.warning("API Key não configurada. Vá na aba 'Configuração'.")
        return

    with st.form("form_cadastro"):
        col1, col2 = st.columns(2)

        with col1:
            external_id = st.text_input("Código *")
            delivery_method_ids = st.text_input("Métodos de Entrega (ex: 32,374) *")
            tipo = st.text_input("Tipo *", value="POINT")
            federal_tax_payer_id = st.text_input("CNPJ *")
            state_tax_payer_id = st.text_input("Inscrição Estadual *")
            name = st.text_input("Nome *")
            official_name = st.text_input("Razão Social *")
            phone = st.text_input("Telefone")
            email = st.text_input("Email")
            map_icon_image = st.text_input("Imagem (URL)")
            observation = st.text_input("Observação")
            responsible_name = st.text_input("Nome do Responsável")
            pickup = st.text_input("Pickup")

        with col2:
            parking = st.text_input("Estacionamento (true/false)", value="true")
            accessibility = st.text_input("Acessibilidade (true/false)", value="false")
            air_conditioned = st.text_input("Ar Condicionado (true/false)", value="true")
            free_parking = st.text_input("Estacionamento Grátis (true/false)", value="false")
            close_to_subway = st.text_input("Perto do Metrô (true/false)", value="true")
            street = st.text_input("Rua *")
            number = st.text_input("Número *")
            additional_information = st.text_input("Info. adicional")
            reference = st.text_input("Referência")
            country = st.text_input("País *", value="BRA")
            state_code = st.text_input("Estado *")
            city = st.text_input("Cidade *")
            quarter = st.text_input("Bairro *")
            zip_code = st.text_input("CEP *")
            latitude = st.text_input("Latitude *")
            longitude = st.text_input("Longitude *")
            images = st.text_input("Imagens (URLs separadas por vírgula)")

        st.markdown("### Horário de funcionamento")
        dias = ["monday", "tuesday", "wednesday", "thursday",
                "friday", "saturday", "sunday"]
        labels = ["Segunda", "Terça", "Quarta", "Quinta",
                  "Sexta", "Sábado", "Domingo"]

        wh_vals = {}
        for i, dia in enumerate(dias):
            st.write(labels[i])
            c1, c2, c3, c4 = st.columns(4)
            wh_vals[f"{dia}_start"] = c1.text_input(f"{labels[i]} início", key=f"{dia}_start")
            wh_vals[f"{dia}_lunch_start"] = c2.text_input(f"{labels[i]} almoço início", key=f"{dia}_lunch_start")
            wh_vals[f"{dia}_lunch_end"] = c3.text_input(f"{labels[i]} almoço fim", key=f"{dia}_lunch_end")
            wh_vals[f"{dia}_end"] = c4.text_input(f"{labels[i]} fim", key=f"{dia}_end")

        enviado = st.form_submit_button("Cadastrar Loja")

    if enviado:
        if not external_id:
            st.error("Informe pelo menos o external_id.")
            return

        form_vals = {
            "external_id": external_id,
            "delivery_method_ids": delivery_method_ids,
            "type": tipo,
            "federal_tax_payer_id": federal_tax_payer_id,
            "state_tax_payer_id": state_tax_payer_id,
            "name": name,
            "official_name": official_name,
            "phone": phone,
            "email": email,
            "map_icon_image": map_icon_image,
            "observation": observation,
            "responsible_name": responsible_name,
            "pickup": pickup,
            "parking": parking,
            "accessibility": accessibility,
            "air_conditioned": air_conditioned,
            "free_parking": free_parking,
            "close_to_subway": close_to_subway,
            "street": street,
            "number": number,
            "additional_information": additional_information,
            "reference": reference,
            "country": country,
            "state_code": state_code,
            "city": city,
            "quarter": quarter,
            "zip_code": zip_code,
            "latitude": latitude,
            "longitude": longitude,
            "images": images,
        }
        form_vals.update(wh_vals)

        pudo_json = montar_json_formulario_streamlit(form_vals)

        try:
            resp = post_pudo(pudo_json, apikey)
        except requests.RequestException as e:
            st.error(f"Falha de conexão: {e}")
            return

        if resp.status_code in (200, 201):
            st.success(f"Loja {external_id} cadastrada com sucesso!")
            st.json(pudo_json)
        else:
            st.error(f"Falha ao cadastrar loja. Status: {resp.status_code}")
            st.text(resp.text)


def pagina_cadastro_planilha():
    st.header("Cadastro de Lojas via Planilha Excel")
    apikey = get_apikey()
    if not apikey:
        st.warning("API Key não configurada. Vá na aba 'Configuração'.")
        return

    uploaded_file = st.file_uploader("Selecione a planilha (.xlsx / .xls)", type=["xlsx", "xls"])
    if uploaded_file is not None:
        st.write("Pré-visualização da planilha:")
        df_prev = pd.read_excel(uploaded_file).head()
        st.dataframe(df_prev)

        if st.button("Cadastrar PUDOs da Planilha"):
            try:
                df = pd.read_excel(
                    uploaded_file, converters={"delivery_method_ids": str}
                ).fillna("")
            except Exception as e:
                st.error(f"Falha ao ler planilha: {e}")
                return

            log_lines = []
            sucesso = 0
            erro = 0

            for idx, row in df.iterrows():
                pudo_json = montar_json(row)
                log_lines.append(
                    f"==== LINHA {idx + 1} | external_id={pudo_json.get('external_id')} ===="
                )
                log_lines.append(repr(pudo_json))
                try:
                    resposta = post_pudo(pudo_json, apikey)
                except requests.RequestException as e:
                    erro += 1
                    log_lines.append(f"ERRO NA CRIAÇÃO (exceção): {e}")
                    continue

                if resposta.status_code in (200, 201):
                    sucesso += 1
                else:
                    erro += 1
                    log_lines.append(
                        f"ERRO NA CRIAÇÃO (status {resposta.status_code}):\n{resposta.text}"
                    )

            st.success(f"Cadastradas com sucesso: {sucesso} | Falhas: {erro}")

            log_text = "LOG DE PUDOS ENVIADOS PARA API\n\n" + "\n\n".join(log_lines)
            st.download_button(
                "Baixar log em TXT",
                data=log_text,
                file_name="pudos_enviados.txt",
                mime="text/plain",
            )


def pagina_consulta():
    st.header("Consulta de Lojas")
    apikey = get_apikey()
    if not apikey:
        st.warning("API Key não configurada. Vá na aba 'Configuração'.")
        return

    aba = st.radio("Tipo de consulta", ["Todas as lojas", "Por external_id"])

    if "last_full_response_text" not in st.session_state:
        st.session_state.last_full_response_text = None

    if aba == "Todas as lojas":
        if st.button("Consultar lojas (todas)"):
            try:
                resp = get_pudos(apikey)
            except requests.RequestException as e:
                st.error(f"Falha de conexão: {e}")
                return

            if resp.status_code != 200:
                st.error(f"Falha ao consultar lojas. Status {resp.status_code}")
                st.text(resp.text)
                return

            st.session_state.last_full_response_text = resp.text

            try:
                dados = resp.json()
            except ValueError:
                st.error("Resposta da API não é um JSON válido.")
                return

            try:
                items = dados.get("content", {}).get("items", [])
            except AttributeError:
                st.error("Formato inesperado do JSON de retorno.")
                return

            if not items:
                st.info("Nenhuma loja retornada.")
                return

            linhas = []
            for item in items:
                external_id = item.get("externalid") or item.get("external_id")
                name = item.get("name")
                enabled = item.get("enabled")
                dm_ids = item.get("delivery_method_ids") or item.get("deliveryMethodIds")

                external_id_str = "" if external_id is None else str(external_id)
                name_str = "" if name is None else str(name)
                enabled_str = "" if enabled is None else str(enabled)

                if isinstance(dm_ids, (list, tuple)):
                    dm_str = ",".join(str(x) for x in dm_ids)
                else:
                    dm_str = "" if dm_ids is None else str(dm_ids)

                linhas.append(
                    {
                        "external_id": external_id_str,
                        "name": name_str,
                        "enabled": enabled_str,
                        "delivery_method_ids": dm_str,
                    }
                )

            df_res = pd.DataFrame(linhas)
            st.dataframe(df_res)

            txt_buffer = StringIO()
            txt_buffer.write("external_id;name;enabled;delivery_method_ids\n")
            for l in linhas:
                txt_buffer.write(
                    f"{l['external_id']};{l['name']};{l['enabled']};{l['delivery_method_ids']}\n"
                )
            st.download_button(
                "Baixar resultado em TXT",
                data=txt_buffer.getvalue(),
                file_name="consulta_pudos.txt",
                mime="text/plain",
            )

            if st.session_state.last_full_response_text:
                st.download_button(
                    "Baixar JSON completo (TXT)",
                    data=st.session_state.last_full_response_text,
                    file_name="consulta_pudos_raw.txt",
                    mime="text/plain",
                )

    else:
        external_id_in = st.text_input("Informe o external_id")
        if st.button("Consultar loja"):
            if not external_id_in:
                st.error("Informe um external_id.")
                return

            try:
                resp = get_pudo_by_external_id(external_id_in, apikey)
            except requests.RequestException as e:
                st.error(f"Falha de conexão: {e}")
                return

            if resp.status_code != 200:
                st.error(f"Falha ao consultar loja. Status {resp.status_code}")
                st.text(resp.text)
                return

            st.session_state.last_full_response_text = resp.text

            try:
                dado = resp.json()
            except ValueError:
                st.error("Resposta da API não é um JSON válido.")
                return

            content = dado.get("content")
            if not content:
                st.info("Nenhuma loja retornada.")
                return

            external_id_val = content.get("external_id") or external_id_in
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

            df_res = pd.DataFrame(
                [
                    {
                        "external_id": external_id_str,
                        "name": name_str,
                        "enabled": enabled_str,
                        "delivery_method_ids": dm_str,
                    }
                ]
            )
            st.dataframe(df_res)

            txt_buffer = StringIO()
            txt_buffer.write("external_id;name;enabled;delivery_method_ids\n")
            txt_buffer.write(
                f"{external_id_str};{name_str};{enabled_str};{dm_str}\n"
            )
            st.download_button(
                "Baixar resultado em TXT",
                data=txt_buffer.getvalue(),
                file_name=f"consulta_pudo_{external_id_str}.txt",
                mime="text/plain",
            )

            if st.session_state.last_full_response_text:
                st.download_button(
                    "Baixar JSON completo (TXT)",
                    data=st.session_state.last_full_response_text,
                    file_name=f"consulta_pudo_{external_id_str}_raw.txt",
                    mime="text/plain",
                )


def pagina_ativar_inativar():
    st.header("Ativar / Desativar Loja")
    apikey = get_apikey()
    if not apikey:
        st.warning("API Key não configurada. Vá na aba 'Configuração'.")
        return

    external_id = st.text_input("External_id da loja")
    col1, col2 = st.columns(2)
    if col1.button("Ativar"):
        if not external_id:
            st.error("Informe o external_id.")
        else:
            resp = patch_pudo(external_id, True, apikey)
            if resp.status_code == 200:
                st.success("Loja ativada com sucesso!")
            else:
                st.error(f"Falha ao ativar. Status {resp.status_code}")
                st.text(resp.text)

    if col2.button("Desativar"):
        if not external_id:
            st.error("Informe o external_id.")
        else:
            resp = patch_pudo(external_id, False, apikey)
            if resp.status_code == 200:
                st.success("Loja desativada com sucesso!")
            else:
                st.error(f"Falha ao desativar. Status {resp.status_code}")
                st.text(resp.text)


def pagina_atualizar_form():
    st.header("Atualizar Cadastro de Loja (Formulário)")
    apikey = get_apikey()
    if not apikey:
        st.warning("API Key não configurada. Vá na aba 'Configuração'.")
        return

    # External_ID que será usado na URL do PUT
    external_id_update = st.text_input("Informe o external_id da loja que deseja atualizar *")

    st.markdown("---")

    with st.form("form_atualizar"):
        col1, col2 = st.columns(2)

        with col1:
            external_id = st.text_input("Código (external_id no JSON) *")
            delivery_method_ids = st.text_input("Métodos de Entrega (ex: 32,374) *")
            tipo = st.text_input("Tipo *", value="POINT")
            federal_tax_payer_id = st.text_input("CNPJ *")
            state_tax_payer_id = st.text_input("Inscrição Estadual *")
            name = st.text_input("Nome *")
            official_name = st.text_input("Razão Social *")
            phone = st.text_input("Telefone")
            email = st.text_input("Email")
            map_icon_image = st.text_input("Imagem (URL)")
            observation = st.text_input("Observação")
            responsible_name = st.text_input("Nome do Responsável")
            pickup = st.text_input("Pickup")

        with col2:
            parking = st.text_input("Estacionamento (true/false)", value="true")
            accessibility = st.text_input("Acessibilidade (true/false)", value="false")
            air_conditioned = st.text_input("Ar Condicionado (true/false)", value="true")
            free_parking = st.text_input("Estacionamento Grátis (true/false)", value="false")
            close_to_subway = st.text_input("Perto do Metrô (true/false)", value="true")
            street = st.text_input("Rua *")
            number = st.text_input("Número *")
            additional_information = st.text_input("Info. adicional")
            reference = st.text_input("Referência")
            country = st.text_input("País *", value="BRA")
            state_code = st.text_input("Estado *")
            city = st.text_input("Cidade *")
            quarter = st.text_input("Bairro *")
            zip_code = st.text_input("CEP *")
            latitude = st.text_input("Latitude *")
            longitude = st.text_input("Longitude *")
            images = st.text_input("Imagens (URLs separadas por vírgula)")

        st.markdown("### Horário de funcionamento")
        dias = ["monday", "tuesday", "wednesday", "thursday",
                "friday", "saturday", "sunday"]
        labels = ["Segunda", "Terça", "Quarta", "Quinta",
                  "Sexta", "Sábado", "Domingo"]

        wh_vals = {}
        for i, dia in enumerate(dias):
            st.write(labels[i])
            c1, c2, c3, c4 = st.columns(4)
            wh_vals[f"{dia}_start"] = c1.text_input(f"{labels[i]} início", key=f"upd_{dia}_start")
            wh_vals[f"{dia}_lunch_start"] = c2.text_input(f"{labels[i]} almoço início", key=f"upd_{dia}_lunch_start")
            wh_vals[f"{dia}_lunch_end"] = c3.text_input(f"{labels[i]} almoço fim", key=f"upd_{dia}_lunch_end")
            wh_vals[f"{dia}_end"] = c4.text_input(f"{labels[i]} fim", key=f"upd_{dia}_end")

        enviado = st.form_submit_button("Atualizar Loja")

    if enviado:
        if not external_id_update:
            st.error("Informe o external_id da loja que deseja atualizar (campo acima do formulário).")
            return

        if not external_id:
            st.error("Informe o external_id que irá no JSON.")
            return

        form_vals = {
            "external_id": external_id,
            "delivery_method_ids": delivery_method_ids,
            "type": tipo,
            "federal_tax_payer_id": federal_tax_payer_id,
            "state_tax_payer_id": state_tax_payer_id,
            "name": name,
            "official_name": official_name,
            "phone": phone,
            "email": email,
            "map_icon_image": map_icon_image,
            "observation": observation,
            "responsible_name": responsible_name,
            "pickup": pickup,
            "parking": parking,
            "accessibility": accessibility,
            "air_conditioned": air_conditioned,
            "free_parking": free_parking,
            "close_to_subway": close_to_subway,
            "street": street,
            "number": number,
            "additional_information": additional_information,
            "reference": reference,
            "country": country,
            "state_code": state_code,
            "city": city,
            "quarter": quarter,
            "zip_code": zip_code,
            "latitude": latitude,
            "longitude": longitude,
            "images": images,
        }
        form_vals.update(wh_vals)

        pudo_json = montar_json_formulario_streamlit(form_vals)

        try:
            resp = put_pudo(external_id_update, pudo_json, apikey)
        except requests.RequestException as e:
            st.error(f"Falha de conexão: {e}")
            return

        if resp.status_code in (200, 201):
            st.success(f"Loja {external_id_update} atualizada com sucesso!")
            st.json(pudo_json)
        else:
            st.error(f"Falha ao atualizar loja. Status: {resp.status_code}")
            st.text(resp.text)


# ================== MAIN ==================

def main():
    st.set_page_config(page_title="Gerenciador de loja", layout="wide")

    st.title("Gerenciador de Loja")

    menu = st.sidebar.radio(
        "Navegação",
        [
            "Configuração",
            "Cadastro (Formulário)",
            "Cadastro (Planilha)",
            "Consulta",
            "Ativar / Desativar",
            "Atualizar cadastro",
        ],
    )

    if menu == "Configuração":
        pagina_config()
    elif menu == "Cadastro (Formulário)":
        pagina_cadastro_form()
    elif menu == "Cadastro (Planilha)":
        pagina_cadastro_planilha()
    elif menu == "Consulta":
        pagina_consulta()
    elif menu == "Ativar / Desativar":
        pagina_ativar_inativar()
    elif menu == "Atualizar cadastro":
        pagina_atualizar_form()


if __name__ == "__main__":
    main()

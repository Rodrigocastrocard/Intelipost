import os
import json
import base64
from datetime import datetime

import numpy as np
import pandas as pd
import requests
import streamlit as st

from openpyxl import load_workbook  # se realmente precisar

# ===================== CONFIGURAÇÃO BÁSICA =====================

st.set_page_config(
    page_title="🚚 Manager Pro Web",
    page_icon="🚚",
    layout="wide",
)

# ===================== FUNÇÕES INTELIPOST (AUXILIARES) =====================

def _montar_pedidos_do_df(df: pd.DataFrame):
    if "Pedido" not in df.columns:
        st.error("O CSV deve conter a coluna 'Pedido'.")
        return None
    pedidos = []
    now_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    for pedido in df["Pedido"].dropna():
        # Garantir string com zeros à esquerda preservados
        pedidos.append({"order_number": str(pedido).strip(), "event_date": now_str})
    return pedidos if pedidos else None


# ===================== FUNÇÕES INTELIPOST (AÇÕES) =====================

def enviar_pedidos(df, api_key):
    pedidos = _montar_pedidos_do_df(df)
    if pedidos is None:
        return False

    url = "https://api.intelipost.com.br/api/v1/shipment_order/multi/ready_for_shipment/with_date"
    headers = {"Content-Type": "application/json", "Api-Key": api_key}

    resp = requests.post(url, headers=headers, json=pedidos)
    if resp.status_code == 200:
        st.success("✅ Pedidos marcados como PRONTO PARA ENVIO!")
        return True
    else:
        st.error(f"❌ Status: {resp.status_code}\n{resp.text}")
        return False


def enviar_pedidos_despachado(df, api_key):
    pedidos = _montar_pedidos_do_df(df)
    if pedidos is None:
        return False

    url = "https://api.intelipost.com.br/api/v1/shipment_order/multi/shipped/with_date"
    headers = {"Content-Type": "application/json", "Api-Key": api_key}

    resp = requests.post(url, headers=headers, json=pedidos)
    if resp.status_code == 200:
        st.success("✅ Pedidos marcados como DESPACHADOS!")
        return True
    else:
        st.error(f"❌ Status: {resp.status_code}\n{resp.text}")
        return False


def enviar_pedidos_entregue(df, api_key):
    pedidos = _montar_pedidos_do_df(df)
    if pedidos is None:
        return False

    url = "https://api.intelipost.com.br/api/v1/shipment_order/multi/delivered/with_date"
    headers = {"Content-Type": "application/json", "Api-Key": api_key}

    resp = requests.post(url, headers=headers, json=pedidos)
    if resp.status_code == 200:
        st.success("✅ Pedidos marcados como ENTREGUES!")
        return True
    else:
        st.error(f"❌ Status: {resp.status_code}\n{resp.text}")
        return False


def cancelar_pedidos(df, api_key):
    if "Pedido" not in df.columns:
        st.error("❌ CSV deve conter coluna 'Pedido'.")
        return

    headers = {"Content-Type": "application/json", "Api-Key": api_key}
    base_url = "https://api.intelipost.com.br/api/v1/order/"

    total, sucesso, falhas = len(df), 0, 0
    progress = st.progress(0)
    status_text = st.empty()

    for i, pedido in enumerate(df["Pedido"].dropna(), start=1):
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
        except Exception:
            falhas += 1

        progress.progress(i / total)
        status_text.text(f"Processando {i}/{total}...")

    st.info(f"✅ Cancelamento concluído!\nSucessos: {sucesso}\nFalhas: {falhas}\nTotal: {total}")


def alterar_transportadora(df, api_key):
    if "Pedido" not in df.columns or "Transportadora" not in df.columns:
        st.error("❌ CSV deve conter colunas 'Pedido' e 'Transportadora'.")
        return

    headers = {"Content-Type": "application/json", "Api-Key": api_key}
    url_get_base = "https://api.intelipost.com.br/api/v1/shipment_order/"
    url_post = "https://api.intelipost.com.br/api/v1/shipment_order/change_delivery_method"

    total, sucesso, falhas = len(df), 0, 0
    progress = st.progress(0)
    status_text = st.empty()

    for i, (_, linha) in enumerate(df.iterrows(), start=1):
        pedido = str(linha["Pedido"]).strip()
        transportadora = linha["Transportadora"]
        if not pedido:
            continue

        try:
            resp_get = requests.get(url_get_base + pedido, headers=headers)
            if resp_get.status_code != 200:
                falhas += 1
                continue

            dados = resp_get.json()
            content = dados.get("content", {})

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

            est_date = content.get("estimated_delivery_date") or datetime.now().isoformat(timespec="seconds")
            body = {
                "quote_id": content.get("quote_id"),
                "estimated_delivery_date": est_date,
                "delivery_method_id": int(transportadora),
                "order_number": pedido,
                "volumes": volumes_body
            }

            resp_post = requests.post(url_post, headers=headers, json=body)
            if resp_post.status_code in [200, 201]:
                sucesso += 1
            else:
                falhas += 1

        except Exception:
            falhas += 1

        progress.progress(i / total)
        status_text.text(f"Processando {i}/{total}...")

    st.info(f"✅ Alteração concluída!\nSucessos: {sucesso}\nFalhas: {falhas}\nTotal: {total}")


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
            except Exception:
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
    # Mantém tudo como string para preservar zeros à esquerda
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


def enviar_requisicoes_planilha(api_key, requisicoes):
    url = "https://api.intelipost.com.br/api/v1/shipment_order"
    headers = {"Accept": "application/json",
               "Content-Type": "application/json; charset=utf-8",
               "api-key": api_key}

    total, sucesso = len(requisicoes), 0
    erros = []

    progress = st.progress(0)
    status_text = st.empty()

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

        progress.progress(i / total)
        status_text.text(f"📊 Processando... {i}/{total}")

    if sucesso == total:
        st.success(f"✅ Todos os {total} pedidos importados!")
    else:
        st.warning(f"✅ {sucesso}/{total} pedidos importados com sucesso\n❌ {len(erros)} erros")
        with st.expander("Ver erros"):
            for e in erros:
                st.write(e)


# ===================== INTERFACE STREAMLIT / API KEYS EM SESSÃO =====================

def main():
    st.title("🚚 Manager Pro - Web")

    # Inicializar chaves em session_state
    if "api_key_intelipost" not in st.session_state:
        st.session_state.api_key_intelipost = ""
    if "api_key_planilha" not in st.session_state:
        st.session_state.api_key_planilha = ""

    tab1, tab2 = st.tabs(["⚡ Operações Rápidas CSV", "📊 Importador Avançado Excel"])

    # -------- TAB 1: Operações Rápidas --------
    with tab1:
        st.subheader("⚡ Operações Rápidas CSV (5 Funções)")

        # ApiKey Intelipost (apenas na sessão)
        col1, _ = st.columns([3, 1])
        with col1:
            api_key_ip = st.text_input(
                "🔑 ApiKey Intelipost (sessão)",
                value=st.session_state.api_key_intelipost,
                type="password",
            )
        # Atualiza sessão sempre que o usuário alterar
        st.session_state.api_key_intelipost = api_key_ip.strip()

        uploaded_csv = st.file_uploader("📄 Arquivo CSV", type=["csv"])
        if uploaded_csv is not None:
            try:
                # Força leitura como texto para preservar zeros à esquerda
                df_csv = pd.read_csv(
                    uploaded_csv,
                    sep=None,
                    engine="python",
                    dtype=str
                )
                st.write("Pré-visualização do CSV:")
                st.dataframe(df_csv.head())
            except Exception as e:
                st.error(f"Erro ao ler CSV: {e}")
                df_csv = None
        else:
            df_csv = None

        st.markdown("**CSV precisa**: coluna 'Pedido' | para alterar transportadora: colunas 'Pedido' e 'Transportadora'.")

        col_a, col_b, col_c = st.columns(3)
        col_d, col_e, _ = st.columns(3)

        api_key_resolvida = st.session_state.api_key_intelipost

        with col_a:
            if st.button("✅ Pronto para Envio") and df_csv is not None:
                if not api_key_resolvida:
                    st.error("Informe a ApiKey Intelipost.")
                else:
                    enviar_pedidos(df_csv, api_key_resolvida)

        with col_b:
            if st.button("🚚 Despachado") and df_csv is not None:
                if not api_key_resolvida:
                    st.error("Informe a ApiKey Intelipost.")
                else:
                    enviar_pedidos_despachado(df_csv, api_key_resolvida)

        with col_c:
            if st.button("📦 Entregue") and df_csv is not None:
                if not api_key_resolvida:
                    st.error("Informe a ApiKey Intelipost.")
                else:
                    enviar_pedidos_entregue(df_csv, api_key_resolvida)

        with col_d:
            if st.button("❌ Cancelar Pedidos") and df_csv is not None:
                if not api_key_resolvida:
                    st.error("Informe a ApiKey Intelipost.")
                else:
                    cancelar_pedidos(df_csv, api_key_resolvida)

        with col_e:
            if st.button("🔄 Alterar Transportadora") and df_csv is not None:
                if not api_key_resolvida:
                    st.error("Informe a ApiKey Intelipost.")
                else:
                    alterar_transportadora(df_csv, api_key_resolvida)

    # -------- TAB 2: Importador Avançado Excel --------
    with tab2:
        st.subheader("📊 Importador Avançado Excel")

        col1, _ = st.columns([3, 1])
        with col1:
            api_key_auth = st.text_input(
                "🔑 ApiKey Planilha (sessão)",
                value=st.session_state.api_key_planilha,
                type="password",
            )
        st.session_state.api_key_planilha = api_key_auth.strip()

        uploaded_excel = st.file_uploader("📈 Planilha Excel", type=["xlsx", "xls"])
        if uploaded_excel is not None:
            st.info("A planilha será processada com header na linha 3 (header=2).")

        if st.button("🚀 IMPORTAR PEDIDOS"):
            if not st.session_state.api_key_planilha:
                st.warning("❌ Informe a ApiKey da planilha!")
            elif uploaded_excel is None:
                st.error("❌ Selecione um arquivo Excel válido!")
            else:
                try:
                    temp_name = "upload_temp.xlsx"
                    with open(temp_name, "wb") as f:
                        f.write(uploaded_excel.getbuffer())

                    requisicoes = processar_planilha(temp_name)
                    if not requisicoes:
                        st.info("Nenhuma requisição gerada!")
                    else:
                        enviar_requisicoes_planilha(st.session_state.api_key_planilha, requisicoes)
                        st.success("✅ Importação concluída!")

                    os.remove(temp_name)
                except Exception as e:
                    st.error(f"❌ Erro ao processar: {e}")


if __name__ == "__main__":
    main()
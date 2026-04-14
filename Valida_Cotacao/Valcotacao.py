import io
import requests
import pandas as pd
import streamlit as st

INTELIPOST_URL = "https://api.intelipost.com.br/api/v1/quote_by_product"


# ==========================
# Configuração da página
# ==========================
st.set_page_config(
    page_title="Cotação Intelipost",
    page_icon="📦",
    layout="wide"
)


# ==========================
# Estilo visual
# ==========================
def inject_css():
    st.markdown(
        """
        <style>
        .main > div {
            padding-top: 1.5rem;
        }

        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }

        .hero {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 45%, #0f766e 100%);
            border-radius: 22px;
            padding: 28px 32px;
            color: white;
            margin-bottom: 1.2rem;
            box-shadow: 0 18px 45px rgba(15, 23, 42, 0.22);
        }

        .hero h1 {
            margin: 0;
            font-size: 2rem;
            line-height: 1.15;
        }

        .hero p {
            margin: 8px 0 0 0;
            color: rgba(255,255,255,0.86);
            font-size: 0.98rem;
        }

        .metric-card {
            background: #ffffff;
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 18px;
            padding: 18px;
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
        }

        .section-card {
            background: #ffffff;
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 20px;
            padding: 18px 18px 10px 18px;
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
            margin-bottom: 1rem;
        }

        .small-muted {
            color: #64748b;
            font-size: 0.92rem;
        }

        .status-ok {
            display: inline-block;
            padding: 6px 10px;
            border-radius: 999px;
            background: rgba(16, 185, 129, 0.12);
            color: #047857;
            font-size: 0.85rem;
            font-weight: 600;
        }

        .status-warn {
            display: inline-block;
            padding: 6px 10px;
            border-radius: 999px;
            background: rgba(245, 158, 11, 0.14);
            color: #b45309;
            font-size: 0.85rem;
            font-weight: 600;
        }

        div[data-testid="stDataFrame"] {
            border-radius: 16px;
            overflow: hidden;
            border: 1px solid rgba(15, 23, 42, 0.08);
        }

        .stButton > button,
        .stDownloadButton > button {
            border-radius: 12px !important;
            font-weight: 600 !important;
            height: 42px;
        }

        .stTextInput > div > div > input,
        .stTextArea textarea,
        .stNumberInput input {
            border-radius: 12px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ==========================
# Estado da sessão
# ==========================
def init_session():
    defaults = {
        "api_key": "",
        "todas_opcoes": [],
        "ultimo_payload": None,
        "logs_execucao": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ==========================
# Regras de negócio
# ==========================
def montar_products(
    peso: float,
    largura: float,
    altura: float,
    comprimento: float,
    valor: float,
) -> list[dict]:
    return [
        {
            "weight": peso,
            "cost_of_goods": valor,
            "width": largura,
            "height": altura,
            "length": comprimento,
            "quantity": 1,
            "sku_id": "SKU123",
            "product_category": "Bebidas",
        },
        {
            "weight": peso,
            "cost_of_goods": valor,
            "width": largura,
            "height": altura,
            "length": comprimento,
            "quantity": 1,
            "sku_id": "SKU456",
            "product_category": "Bebidas",
        },
    ]


def montar_payload(
    origin_cep: str,
    dest_cep: str,
    peso: float,
    largura: float,
    altura: float,
    comprimento: float,
    valor: float,
) -> dict:
    return {
        "origin_zip_code": origin_cep,
        "destination_zip_code": dest_cep,
        "quoting_mode": "DYNAMIC_BOX_ALL_ITEMS",
        "products": montar_products(peso, largura, altura, comprimento, valor),
        "additional_information": {
            "lead_time_business_days": 1,
            "sales_channel": "meu_canal_de_vendas",
            "client_type": "gold",
            "rule_tags": ["Agendado", "Linha_Branca"],
        },
        "identification": {
            "session": "04e5bdf7ed15e571c0265c18333b6fdf1434658753",
            "ip": "000.000.000.000",
            "page_name": "carrinho",
            "url": "http://www.intelipost.com.br/checkout/cart/",
        },
    }


def cotar_frete_intelipost(
    origin_cep: str,
    dest_cep: str,
    peso: float,
    largura: float,
    altura: float,
    comprimento: float,
    valor: float,
    api_key: str,
) -> dict:
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key,
    }

    payload = montar_payload(
        origin_cep=origin_cep,
        dest_cep=dest_cep,
        peso=peso,
        largura=largura,
        altura=altura,
        comprimento=comprimento,
        valor=valor,
    )

    st.session_state["ultimo_payload"] = payload

    response = requests.post(
        INTELIPOST_URL,
        json=payload,
        headers=headers,
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def extrair_opcoes_frete(dest_cep: str, resposta: dict) -> list[dict]:
    opcoes = []
    content = resposta.get("content", {})
    delivery_options = content.get("delivery_options", [])

    for opt in delivery_options:
        transportadora = (
            opt.get("description")
            or opt.get("logistic_provider_name")
            or "N/I"
        )
        prazo_dias = (
            opt.get("delivery_estimate_business_days")
            or opt.get("delivery_time_business_days")
            or opt.get("delivery_time")
            or 0
        )
        valor_frete = (
            opt.get("final_shipping_cost")
            or opt.get("shipping_cost")
            or 0.0
        )

        opcoes.append(
            {
                "destino": dest_cep,
                "transportadora": transportadora,
                "prazo_dias": int(prazo_dias),
                "valor_frete": float(valor_frete),
            }
        )

    return opcoes


def ler_ceps_de_excel_streamlit(arquivo_excel) -> list[str]:
    df_ceps = pd.read_excel(arquivo_excel, usecols="A")
    primeira_coluna = df_ceps.columns[0]
    ceps_series = df_ceps[primeira_coluna].dropna().astype(str).str.strip()
    ceps_unicos = pd.Series(ceps_series.unique())
    return [c for c in ceps_unicos if c]


def parse_float_br(valor: str) -> float:
    return float(str(valor).replace(".", "").replace(",", ".")) if isinstance(valor, str) and valor.count(",") == 1 and valor.count(".") > 1 else float(str(valor).replace(",", "."))


def normalizar_lista_ceps(texto: str, ceps_excel: list[str]) -> list[str]:
    ceps_digitados = []
    if texto.strip():
        bruto = texto.replace("\n", ",").replace(";", ",")
        ceps_digitados = [c.strip() for c in bruto.split(",") if c.strip()]
    return list(dict.fromkeys(ceps_digitados + ceps_excel))


def gerar_excel_bytes(df: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="cotacoes")
    buffer.seek(0)
    return buffer.getvalue()


# ==========================
# Componentes visuais
# ==========================
def render_header():
    st.markdown(
        """
        <div class="hero">
            <h1>📦 Cotação de Frete Intelipost</h1>
            <p>Aplicação Streamlit com interface moderna, importação de CEPs por Excel, análise de médias e API Key mantida apenas na sessão atual do navegador.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar():
    st.sidebar.title("⚙️ Configurações")
    st.sidebar.caption("A API Key não é salva em arquivo. Ela fica apenas na sessão atual.")

    st.sidebar.text_input(
        "API Key Intelipost",
        type="password",
        key="api_key",
        help="A chave fica somente nesta sessão do navegador.",
    )

    col1, col2 = st.sidebar.columns(2)

    with col1:
        if st.button("Validar", use_container_width=True):
            if st.session_state.api_key.strip():
                st.sidebar.success("API Key disponível na sessão.")
            else:
                st.sidebar.error("Informe a API Key.")

    with col2:
        if st.button("Limpar", use_container_width=True):
            st.session_state.api_key = ""
            st.sidebar.info("API Key removida da sessão.")

    st.sidebar.markdown("---")
    if st.session_state.api_key.strip():
        st.sidebar.markdown('<span class="status-ok">API Key carregada</span>', unsafe_allow_html=True)
    else:
        st.sidebar.markdown('<span class="status-warn">API Key não informada</span>', unsafe_allow_html=True)


def render_metricas(df: pd.DataFrame):
    total_ceps = df["destino"].nunique() if not df.empty else 0
    total_opcoes = len(df)
    menor_frete = df["valor_frete"].min() if not df.empty else 0.0
    menor_prazo = df["prazo_dias"].min() if not df.empty else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("CEPs cotados", total_ceps)
    c2.metric("Opções retornadas", total_opcoes)
    c3.metric("Menor frete", f"R$ {menor_frete:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    c4.metric("Menor prazo", f"{menor_prazo} dia(s)")


def render_debug_area():
    with st.expander("Debug técnico", expanded=False):
        if st.session_state.get("ultimo_payload"):
            st.write("Último payload enviado")
            st.json(st.session_state["ultimo_payload"])
        else:
            st.info("Nenhum payload registrado ainda.")


# ==========================
# App principal
# ==========================
def main():
    inject_css()
    init_session()
    render_sidebar()
    render_header()

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("Dados da cotação")
    st.markdown("<div class='small-muted'>Preencha os dados manualmente ou envie uma planilha com CEPs na coluna A.</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1.25, 1.15, 1.0])

    with col1:
        origin_cep = st.text_input("CEP Origem", placeholder="35620-000")
        ceps_destino_str = st.text_area(
            "CEPs Destino",
            placeholder="Digite separados por vírgula, ponto e vírgula ou quebra de linha",
            height=140,
        )

    with col2:
        uploaded_excel = st.file_uploader(
            "Importar CEPs por Excel",
            type=["xlsx", "xls"],
            help="Os CEPs devem estar na coluna A.",
        )
        ceps_excel = []
        if uploaded_excel is not None:
            try:
                ceps_excel = ler_ceps_de_excel_streamlit(uploaded_excel)
                if ceps_excel:
                    st.success(f"{len(ceps_excel)} CEP(s) carregado(s) da planilha.")
                    preview = ", ".join(ceps_excel[:15])
                    if len(ceps_excel) > 15:
                        preview += " ..."
                    st.caption(preview)
                else:
                    st.warning("Nenhum CEP encontrado na coluna A.")
            except Exception as e:
                st.error(f"Erro ao ler Excel: {e}")

    with col3:
        peso = st.text_input("Peso (kg)", value="1,0")
        largura = st.text_input("Largura (cm)", value="10")
        altura = st.text_input("Altura (cm)", value="10")
        comprimento = st.text_input("Comprimento (cm)", value="10")
        valor = st.text_input("Valor do item (R$)", value="100,00")

    todos_ceps = normalizar_lista_ceps(ceps_destino_str, ceps_excel)
    st.caption(f"Total de CEPs prontos para cotação: {len(todos_ceps)}")

    cbtn1, cbtn2, cbtn3 = st.columns([1, 1, 2])

    with cbtn1:
        cotar = st.button("🚀 Cotar fretes", use_container_width=True)
    with cbtn2:
        limpar_resultados = st.button("🧹 Limpar resultados", use_container_width=True)

    if limpar_resultados:
        st.session_state.todas_opcoes = []
        st.session_state.logs_execucao = []
        st.info("Resultados removidos da sessão.")

    if cotar:
        if not st.session_state.api_key.strip():
            st.error("Informe a API Key na barra lateral antes de cotar.")
        else:
            try:
                if not origin_cep.strip():
                    raise ValueError("Informe o CEP de origem.")
                if not todos_ceps:
                    raise ValueError("Informe pelo menos um CEP de destino por texto ou Excel.")

                peso_f = parse_float_br(peso)
                largura_f = parse_float_br(largura)
                altura_f = parse_float_br(altura)
                comprimento_f = parse_float_br(comprimento)
                valor_f = parse_float_br(valor)

                st.session_state.todas_opcoes = []
                st.session_state.logs_execucao = []

                progresso = st.progress(0)
                status = st.empty()

                for idx, dest in enumerate(todos_ceps, start=1):
                    status.info(f"Consultando CEP {dest} ({idx}/{len(todos_ceps)})")
                    try:
                        resposta = cotar_frete_intelipost(
                            origin_cep=origin_cep.strip(),
                            dest_cep=dest,
                            peso=peso_f,
                            largura=largura_f,
                            altura=altura_f,
                            comprimento=comprimento_f,
                            valor=valor_f,
                            api_key=st.session_state.api_key.strip(),
                        )
                        opcoes = extrair_opcoes_frete(dest, resposta)
                        if opcoes:
                            st.session_state.todas_opcoes.extend(opcoes)
                            st.session_state.logs_execucao.append({
                                "destino": dest,
                                "status": "ok",
                                "opcoes": len(opcoes),
                            })
                        else:
                            st.session_state.logs_execucao.append({
                                "destino": dest,
                                "status": "sem_opcoes",
                                "opcoes": 0,
                            })
                    except requests.HTTPError as e:
                        resp = e.response
                        st.session_state.logs_execucao.append({
                            "destino": dest,
                            "status": f"http_{resp.status_code}",
                            "opcoes": 0,
                            "detalhe": resp.text,
                        })
                        st.error(f"Erro HTTP para {dest}: {resp.status_code} - {resp.text}")
                    except Exception as e:
                        st.session_state.logs_execucao.append({
                            "destino": dest,
                            "status": "erro",
                            "opcoes": 0,
                            "detalhe": str(e),
                        })
                        st.error(f"Erro ao cotar para {dest}: {e}")

                    progresso.progress(idx / len(todos_ceps))

                status.success("Processamento finalizado.")

            except Exception as e:
                st.error(f"Falha na validação/processamento: {e}")

    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.todas_opcoes:
        df = pd.DataFrame(st.session_state.todas_opcoes)
        df["prazo_dias"] = pd.to_numeric(df["prazo_dias"], errors="coerce")
        df["valor_frete"] = pd.to_numeric(df["valor_frete"], errors="coerce")

        render_metricas(df)

        tab1, tab2, tab3, tab4 = st.tabs([
            "Cotações",
            "Médias por transportadora",
            "Médias por CEP",
            "Execução",
        ])

        with tab1:
            st.markdown("<div class='section-card'>", unsafe_allow_html=True)
            st.subheader("Opções de frete")
            df_exibicao = df.sort_values(["destino", "valor_frete", "prazo_dias"], ascending=[True, True, True])
            st.dataframe(df_exibicao, use_container_width=True, hide_index=True)

            excel_bytes = gerar_excel_bytes(df_exibicao)
            st.download_button(
                "💾 Baixar Excel",
                data=excel_bytes,
                file_name="cotacoes_frete_intelipost.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=False,
            )
            st.markdown("</div>", unsafe_allow_html=True)

        with tab2:
            st.markdown("<div class='section-card'>", unsafe_allow_html=True)
            st.subheader("Médias por transportadora")
            df_media_transp = (
                df.groupby("transportadora", as_index=False)
                .agg(
                    media_valor=("valor_frete", "mean"),
                    media_prazo=("prazo_dias", "mean"),
                    qtd_opcoes=("transportadora", "count"),
                )
                .sort_values(["media_valor", "media_prazo"], ascending=[True, True])
            )
            df_media_transp["media_valor"] = df_media_transp["media_valor"].round(2)
            df_media_transp["media_prazo"] = df_media_transp["media_prazo"].round(2)
            st.dataframe(df_media_transp, use_container_width=True, hide_index=True)
            st.bar_chart(df_media_transp.set_index("transportadora")["media_valor"])
            st.markdown("</div>", unsafe_allow_html=True)

        with tab3:
            st.markdown("<div class='section-card'>", unsafe_allow_html=True)
            st.subheader("Médias por CEP destino")
            df_media_cep = (
                df.groupby("destino", as_index=False)
                .agg(
                    media_valor=("valor_frete", "mean"),
                    media_prazo=("prazo_dias", "mean"),
                    qtd_opcoes=("destino", "count"),
                )
                .sort_values(["media_valor", "media_prazo"], ascending=[True, True])
            )
            df_media_cep["media_valor"] = df_media_cep["media_valor"].round(2)
            df_media_cep["media_prazo"] = df_media_cep["media_prazo"].round(2)
            st.dataframe(df_media_cep, use_container_width=True, hide_index=True)
            st.bar_chart(df_media_cep.set_index("destino")["media_valor"])
            st.markdown("</div>", unsafe_allow_html=True)

        with tab4:
            st.markdown("<div class='section-card'>", unsafe_allow_html=True)
            st.subheader("Resumo da execução")
            if st.session_state.logs_execucao:
                df_logs = pd.DataFrame(st.session_state.logs_execucao)
                st.dataframe(df_logs, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhum log disponível.")
            render_debug_area()
            st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.info("Nenhuma cotação disponível ainda. Preencha os dados e clique em 'Cotar fretes'.")
        render_debug_area()


if __name__ == "__main__":
    main()

import base64
import json
import os
import requests
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

CONFIG_FILE = "config_intelipost.json"
INTELIPOST_URL = "https://api.intelipost.com.br/api/v1/quote_by_product"


def encode_api_key(api_key: str) -> str:
    return base64.b64encode(api_key.encode("utf-8")).decode("utf-8")


def decode_api_key(encoded: str) -> str:
    return base64.b64decode(encoded.encode("utf-8")).decode("utf-8")


def load_config() -> dict:
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(config: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def get_api_key_from_config() -> str | None:
    cfg = load_config()
    encoded = cfg.get("api_key_base64")
    if not encoded:
        return None
    try:
        return decode_api_key(encoded)
    except Exception:
        return None


def montar_products(peso: float,
                    largura: float,
                    altura: float,
                    comprimento: float,
                    valor: float) -> list[dict]:
    return [
        {
            "weight": peso,
            "cost_of_goods": valor,
            "width": largura,
            "height": altura,
            "length": comprimento,
            "quantity": 1,
            "sku_id": "SKU123",
            "product_category": "Bebidas"
        },
        {
            "weight": peso,
            "cost_of_goods": valor,
            "width": largura,
            "height": altura,
            "length": comprimento,
            "quantity": 1,
            "sku_id": "SKU456",
            "product_category": "Bebidas"
        }
    ]


def cotar_frete_intelipost(origin_cep: str,
                           dest_cep: str,
                           peso: float,
                           largura: float,
                           altura: float,
                           comprimento: float,
                           valor: float,
                           api_key: str) -> dict:
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }

    payload = {
        "origin_zip_code": origin_cep,
        "destination_zip_code": dest_cep,
        "quoting_mode": "DYNAMIC_BOX_ALL_ITEMS",
        "products": montar_products(peso, largura, altura, comprimento, valor),
        "additional_information": {
            "lead_time_business_days": 1,
            "sales_channel": "meu_canal_de_vendas",
            "client_type": "gold",
            "rule_tags": [
                "Agendado",
                "Linha_Branca"
            ]
        },
        "identification": {
            "session": "04e5bdf7ed15e571c0265c18333b6fdf1434658753",
            "ip": "000.000.000.000",
            "page_name": "carrinho",
            "url": "http://www.intelipost.com.br/checkout/cart/"
        }
    }

    print("=== PAYLOAD ENVIADO PARA", dest_cep, "===")
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    resp = requests.post(INTELIPOST_URL, json=payload, headers=headers, timeout=20)
    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        print("=== ERRO HTTP ===")
        print("Status:", resp.status_code)
        print("Body:", resp.text)
        raise

    print("=== RESPOSTA BRUTA PARA", dest_cep, "===")
    print(resp.text)

    return resp.json()


def extrair_opcoes_frete(dest_cep: str, resposta: dict):
    opcoes = []

    content = resposta.get("content", {})
    delivery_options = content.get("delivery_options", [])

    if not delivery_options:
        print("=== RESPOSTA SEM delivery_options PARA DESTINO", dest_cep, "===")
        print(json.dumps(resposta, ensure_ascii=False, indent=2))
        return opcoes

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

        opcoes.append({
            "destino": dest_cep,
            "transportadora": transportadora,
            "prazo_dias": int(prazo_dias),
            "valor_frete": float(valor_frete),
        })

    return opcoes


class ConfigWindow(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Configuração da API Intelipost")
        self.geometry("400x160")
        self.resizable(False, False)

        ttk.Label(self, text="API Key:").pack(padx=10, pady=(15, 5), anchor="w")
        self.entry_api_key = ttk.Entry(self, width=50, show="*")
        self.entry_api_key.pack(padx=10, pady=5, fill="x")

        api_key_atual = get_api_key_from_config()
        if api_key_atual:
            self.entry_api_key.insert(0, api_key_atual)

        frame_botoes = ttk.Frame(self)
        frame_botoes.pack(pady=15)

        btn_salvar = ttk.Button(frame_botoes, text="Salvar", command=self.salvar)
        btn_salvar.pack(side="left", padx=5)

        btn_fechar = ttk.Button(frame_botoes, text="Fechar", command=self.destroy)
        btn_fechar.pack(side="left", padx=5)

        self.transient(master)
        self.grab_set()
        self.entry_api_key.focus()

    def salvar(self):
        api_key = self.entry_api_key.get().strip()
        if not api_key:
            messagebox.showerror("Erro", "Informe a API Key.")
            return

        encoded = encode_api_key(api_key)
        cfg = load_config()
        cfg["api_key_base64"] = encoded
        save_config(cfg)
        messagebox.showinfo("Sucesso", "API Key salva com sucesso (codificada em base64).")
        self.destroy()


class DetalhesWindow(tk.Toplevel):
    def __init__(self, master,
                 df_media_transp: pd.DataFrame,
                 df_media_cep: pd.DataFrame):
        super().__init__(master)
        self.title("Detalhes (Médias)")
        self.geometry("900x600")

        if df_media_transp.empty and df_media_cep.empty:
            messagebox.showinfo(
                "Sem dados",
                "Não há dados suficientes para montar as médias."
            )
            self.destroy()
            return

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Aba 1: média por transportadora ---
        frame_transp = ttk.Frame(notebook)
        notebook.add(frame_transp, text="Médias por transportadora")

        tree_t = ttk.Treeview(
            frame_transp,
            columns=("transportadora", "media_valor", "media_prazo"),
            show="headings"
        )
        tree_t.heading("transportadora", text="Transportadora")
        tree_t.heading("media_valor", text="Média valor frete (R$)")
        tree_t.heading("media_prazo", text="Média prazo (dias úteis)")

        tree_t.column("transportadora", width=250)
        tree_t.column("media_valor", width=150, anchor="e")
        tree_t.column("media_prazo", width=150, anchor="center")

        tree_t.pack(fill="both", expand=True, side="left")

        scroll_t = ttk.Scrollbar(frame_transp, orient="vertical", command=tree_t.yview)
        tree_t.configure(yscroll=scroll_t.set)
        scroll_t.pack(side="right", fill="y")

        for _, row in df_media_transp.iterrows():
            tree_t.insert(
                "",
                "end",
                values=(
                    row["transportadora"],
                    f"{row['media_valor']:.2f}",
                    f"{row['media_prazo']:.2f}",
                )
            )

        # --- Aba 2: média por CEP destino ---
        frame_cep = ttk.Frame(notebook)
        notebook.add(frame_cep, text="Médias por CEP destino")

        tree_c = ttk.Treeview(
            frame_cep,
            columns=("destino", "media_valor", "media_prazo"),
            show="headings"
        )
        tree_c.heading("destino", text="CEP Destino")
        tree_c.heading("media_valor", text="Média valor frete (R$)")
        tree_c.heading("media_prazo", text="Média prazo (dias úteis)")

        tree_c.column("destino", width=120)
        tree_c.column("media_valor", width=150, anchor="e")
        tree_c.column("media_prazo", width=150, anchor="center")

        tree_c.pack(fill="both", expand=True, side="left")

        scroll_c = ttk.Scrollbar(frame_cep, orient="vertical", command=tree_c.yview)
        tree_c.configure(yscroll=scroll_c.set)
        scroll_c.pack(side="right", fill="y")

        for _, row in df_media_cep.iterrows():
            tree_c.insert(
                "",
                "end",
                values=(
                    row["destino"],
                    f"{row['media_valor']:.2f}",
                    f"{row['media_prazo']:.2f}",
                )
            )

        btn_fechar = ttk.Button(self, text="Fechar", command=self.destroy)
        btn_fechar.pack(pady=5)


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Cotação de Frete - Intelipost")
        self.geometry("900x520")

        self._criar_menu()
        self._criar_widgets()
        self.todas_opcoes = []

    def _criar_menu(self):
        menubar = tk.Menu(self)
        menu_config = tk.Menu(menubar, tearoff=0)
        menu_config.add_command(label="Configurar API Key", command=self.abrir_config)
        menubar.add_cascade(label="Configuração", menu=menu_config)
        self.config(menu=menubar)

    def abrir_config(self):
        ConfigWindow(self)

    def _criar_widgets(self):
        frame_dados = ttk.LabelFrame(self, text="Dados da Cotação")
        frame_dados.pack(fill="x", padx=10, pady=10)

        ttk.Label(frame_dados, text="CEP Origem:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.entry_cep_origem = ttk.Entry(frame_dados, width=15)
        self.entry_cep_origem.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(frame_dados, text="CEPs Destino (vírgula ou Excel):").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.entry_ceps_destino = ttk.Entry(frame_dados, width=40)
        self.entry_ceps_destino.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        btn_excel = ttk.Button(frame_dados, text="...", width=3, command=self.carregar_ceps_de_excel)
        btn_excel.grid(row=0, column=4, padx=5, pady=5, sticky="w")

        ttk.Label(frame_dados, text="Peso (kg):").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.entry_peso = ttk.Entry(frame_dados, width=10)
        self.entry_peso.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(frame_dados, text="Largura (cm):").grid(row=1, column=2, padx=5, pady=5, sticky="e")
        self.entry_largura = ttk.Entry(frame_dados, width=10)
        self.entry_largura.grid(row=1, column=3, padx=5, pady=5, sticky="w")

        ttk.Label(frame_dados, text="Altura (cm):").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.entry_altura = ttk.Entry(frame_dados, width=10)
        self.entry_altura.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(frame_dados, text="Comprimento (cm):").grid(row=2, column=2, padx=5, pady=5, sticky="e")
        self.entry_comprimento = ttk.Entry(frame_dados, width=10)
        self.entry_comprimento.grid(row=2, column=3, padx=5, pady=5, sticky="w")

        ttk.Label(frame_dados, text="Valor do item (R$):").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.entry_valor = ttk.Entry(frame_dados, width=10)
        self.entry_valor.grid(row=3, column=1, padx=5, pady=5, sticky="w")

        frame_botoes = ttk.Frame(self)
        frame_botoes.pack(fill="x", padx=10, pady=5)

        self.btn_cotar = ttk.Button(frame_botoes, text="Cotar frete", command=self.cotar_fretes)
        self.btn_cotar.pack(side="left", padx=5)

        self.btn_exportar = ttk.Button(frame_botoes, text="Exportar para Excel", command=self.exportar_excel)
        self.btn_exportar.pack(side="left", padx=5)

        self.btn_detalhes = ttk.Button(frame_botoes, text="Detalhes / Médias", command=self.abrir_detalhes)
        self.btn_detalhes.pack(side="left", padx=5)

        frame_tabela = ttk.LabelFrame(self, text="Opções de Frete")
        frame_tabela.pack(fill="both", expand=True, padx=10, pady=10)

        colunas = ("destino", "transportadora", "prazo_dias", "valor_frete")
        self.tree = ttk.Treeview(frame_tabela, columns=colunas, show="headings")

        self.tree.heading("destino", text="CEP Destino")
        self.tree.heading("transportadora", text="Transportadora")
        self.tree.heading("prazo_dias", text="Prazo (dias úteis)")
        self.tree.heading("valor_frete", text="Valor do frete (R$)")

        self.tree.column("destino", width=100)
        self.tree.column("transportadora", width=250)
        self.tree.column("prazo_dias", width=120, anchor="center")
        self.tree.column("valor_frete", width=120, anchor="e")

        self.tree.tag_configure(
            "separator",
            background="#e0e0e0",
            foreground="#606060"
        )

        self.tree.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(frame_tabela, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

    def carregar_ceps_de_excel(self):
        caminho = filedialog.askopenfilename(
            title="Selecione a planilha de CEPs",
            filetypes=[("Arquivos Excel", "*.xlsx;*.xls")]
        )
        if not caminho:
            return

        try:
            df_ceps = pd.read_excel(caminho, usecols="A")
            primeira_coluna = df_ceps.columns[0]
            ceps_series = df_ceps[primeira_coluna].dropna().astype(str).str.strip()

            ceps_unicos = pd.Series(ceps_series.unique())
            ceps_unicos = [c for c in ceps_unicos if c]

            if not ceps_unicos:
                messagebox.showinfo("Planilha vazia", "Nenhum CEP encontrado na coluna A.")
                return

            self.entry_ceps_destino.delete(0, tk.END)
            self.entry_ceps_destino.insert(0, ", ".join(ceps_unicos))
        except Exception as e:
            messagebox.showerror("Erro ao ler Excel", f"Não foi possível ler a planilha:\n{e}")

    def _ler_inputs(self):
        try:
            origin_cep = self.entry_cep_origem.get().strip()
            dest_ceps_str = self.entry_ceps_destino.get().strip()
            dest_ceps = [c.strip() for c in dest_ceps_str.split(",") if c.strip()]

            peso = float(self.entry_peso.get().replace(",", "."))
            largura = float(self.entry_largura.get().replace(",", "."))
            altura = float(self.entry_altura.get().replace(",", "."))
            comprimento = float(self.entry_comprimento.get().replace(",", "."))
            valor = float(self.entry_valor.get().replace(",", "."))

            if not origin_cep or not dest_ceps:
                raise ValueError("Informe CEP de origem e pelo menos um CEP de destino.")

            return origin_cep, dest_ceps, peso, largura, altura, comprimento, valor
        except ValueError as e:
            messagebox.showerror("Erro de validação", str(e))
            return None

    def cotar_fretes(self):
        api_key = get_api_key_from_config()
        if not api_key:
            messagebox.showerror(
                "API Key não configurada",
                "Configure a API Key em Configuração > Configurar API Key antes de cotar."
            )
            return

        params = self._ler_inputs()
        if params is None:
            return

        origin_cep, dest_ceps, peso, largura, altura, comprimento, valor = params

        for item in self.tree.get_children():
            self.tree.delete(item)
        self.todas_opcoes = []

        for dest in dest_ceps:
            try:
                resposta = cotar_frete_intelipost(
                    origin_cep=origin_cep,
                    dest_cep=dest,
                    peso=peso,
                    largura=largura,
                    altura=altura,
                    comprimento=comprimento,
                    valor=valor,
                    api_key=api_key
                )
                opcoes = extrair_opcoes_frete(dest, resposta)

                if not opcoes:
                    messagebox.showinfo(
                        "Aviso",
                        f"Nenhuma opção de frete retornada para {dest} (veja o console para detalhes)."
                    )
                    continue

                self.tree.insert(
                    "",
                    "end",
                    values=(f"----- CEP Destino: {dest} -----", "", "", ""),
                    tags=("separator",)
                )

                for o in opcoes:
                    self.tree.insert(
                        "",
                        "end",
                        values=(
                            o["destino"],
                            o["transportadora"],
                            o["prazo_dias"],
                            f"{o['valor_frete']:.2f}"
                        )
                    )
                self.todas_opcoes.extend(opcoes)

            except requests.HTTPError as e:
                resp = e.response
                messagebox.showerror(
                    "Erro HTTP",
                    f"Erro ao cotar para {dest}: {e}\n\nStatus: {resp.status_code}\nBody:\n{resp.text}"
                )
            except Exception as e:
                messagebox.showerror(
                    "Erro",
                    f"Erro inesperado para {dest}: {e}"
                )

        print("=== TODAS_OPCOES ===")
        print(self.todas_opcoes)

    def exportar_excel(self):
        if not self.todas_opcoes:
            messagebox.showinfo(
                "Sem dados",
                "Não há cotações para exportar."
            )
            return

        caminho = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Arquivos Excel", "*.xlsx")],
            initialfile="cotacoes_frete_intelipost.xlsx"
        )
        if not caminho:
            return

        df = pd.DataFrame(self.todas_opcoes)
        df.to_excel(caminho, index=False)
        messagebox.showinfo(
            "Exportação concluída",
            f"Arquivo salvo em:\n{caminho}"
        )

    def abrir_detalhes(self):
        if not self.todas_opcoes:
            messagebox.showinfo(
                "Sem dados",
                "Realize pelo menos uma cotação antes de abrir os detalhes."
            )
            return

        df = pd.DataFrame(self.todas_opcoes)

        print("=== DATAFRAME PARA MÉDIAS ===")
        print(df.head())
        print(df.dtypes)

        for col in ["destino", "transportadora", "prazo_dias", "valor_frete"]:
            if col not in df.columns:
                messagebox.showinfo(
                    "Sem dados",
                    f"Não foi possível montar médias: coluna '{col}' não encontrada."
                )
                return

        if df.empty:
            messagebox.showinfo(
                "Sem dados",
                "Não foi possível montar médias: DataFrame vazio."
            )
            return

        df["prazo_dias"] = pd.to_numeric(df["prazo_dias"], errors="coerce")
        df["valor_frete"] = pd.to_numeric(df["valor_frete"], errors="coerce")

        # Médias por transportadora[web:215][web:221]
        df_media_transp = df.groupby("transportadora", as_index=False).agg(
            media_valor=("valor_frete", "mean"),
            media_prazo=("prazo_dias", "mean"),
        )

        # Médias por CEP destino[web:217][web:221]
        df_media_cep = df.groupby("destino", as_index=False).agg(
            media_valor=("valor_frete", "mean"),
            media_prazo=("prazo_dias", "mean"),
        )

        DetalhesWindow(self, df_media_transp, df_media_cep)


if __name__ == "__main__":
    app = App()
    app.mainloop()

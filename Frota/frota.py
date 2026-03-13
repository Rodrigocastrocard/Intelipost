import pymysql
import tkinter as tk
from tkinter import ttk, messagebox


# =========================
# conexão com MySQL (função)
# =========================
def get_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="Janete4353",
        database="frota",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.Cursor
    )


# =========================
# Janela de cadastro empresa
# =========================
class EmpresaWindow(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Cadastro da Empresa")
        self.geometry("500x320")
        self.resizable(False, False)

        self.empresa_id = None  # para saber se é UPDATE ou INSERT

        self.nome_var = tk.StringVar()
        self.endereco_var = tk.StringVar()
        self.bairro_var = tk.StringVar()
        self.cidade_var = tk.StringVar()
        self.estado_var = tk.StringVar()
        self.cep_var = tk.StringVar()
        self.telefone_var = tk.StringVar()
        self.celular_var = tk.StringVar()
        self.email_var = tk.StringVar()

        self._build_ui()
        self.carregar_empresa_existente()

    def _build_ui(self):
        padding = {"padx": 10, "pady": 3}

        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Label(frame, text="Nome da Empresa*:").grid(row=0, column=0, sticky="w", **padding)
        ttk.Entry(frame, textvariable=self.nome_var, width=40).grid(
            row=0, column=1, columnspan=3, sticky="w", **padding
        )

        ttk.Label(frame, text="Endereço*:").grid(row=1, column=0, sticky="w", **padding)
        ttk.Entry(frame, textvariable=self.endereco_var, width=40).grid(
            row=1, column=1, columnspan=3, sticky="w", **padding
        )

        ttk.Label(frame, text="Bairro:").grid(row=2, column=0, sticky="w", **padding)
        ttk.Entry(frame, textvariable=self.bairro_var, width=25).grid(
            row=2, column=1, sticky="w", **padding
        )

        ttk.Label(frame, text="Cidade:").grid(row=2, column=2, sticky="w", **padding)
        ttk.Entry(frame, textvariable=self.cidade_var, width=20).grid(
            row=2, column=3, sticky="w", **padding
        )

        ttk.Label(frame, text="Estado:").grid(row=3, column=0, sticky="w", **padding)
        ttk.Entry(frame, textvariable=self.estado_var, width=5).grid(
            row=3, column=1, sticky="w", **padding
        )

        ttk.Label(frame, text="CEP:").grid(row=3, column=2, sticky="w", **padding)
        ttk.Entry(frame, textvariable=self.cep_var, width=15).grid(
            row=3, column=3, sticky="w", **padding
        )

        ttk.Label(frame, text="Telefone:").grid(row=4, column=0, sticky="w", **padding)
        ttk.Entry(frame, textvariable=self.telefone_var, width=20).grid(
            row=4, column=1, sticky="w", **padding
        )

        ttk.Label(frame, text="Celular*:").grid(row=4, column=2, sticky="w", **padding)
        ttk.Entry(frame, textvariable=self.celular_var, width=20).grid(
            row=4, column=3, sticky="w", **padding
        )

        ttk.Label(frame, text="E-mail:").grid(row=5, column=0, sticky="w", **padding)
        ttk.Entry(frame, textvariable=self.email_var, width=40).grid(
            row=5, column=1, columnspan=3, sticky="w", **padding
        )

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=6, column=0, columnspan=4, pady=15)

        ttk.Button(btn_frame, text="Salvar", command=self.salvar_empresa).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Fechar", command=self.destroy).pack(side="left", padx=5)

        for col in range(4):
            frame.columnconfigure(col, weight=1)

    def carregar_empresa_existente(self):
        """Carrega o primeiro registro da tabela empresa, se existir, e preenche o formulário."""
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT empresa_id, nome, endereco, bairro, cidade, estado,
                       cep, telefone, celular, email
                FROM empresa
                ORDER BY empresa_id ASC
                LIMIT 1
                """
            )
            row = cur.fetchone()
            cur.close()
            conn.close()

            if row:
                (self.empresa_id,
                 nome, endereco, bairro, cidade, estado,
                 cep, telefone, celular, email) = row

                self.nome_var.set(nome or "")
                self.endereco_var.set(endereco or "")
                self.bairro_var.set(bairro or "")
                self.cidade_var.set(cidade or "")
                self.estado_var.set(estado or "")
                self.cep_var.set(cep or "")
                self.telefone_var.set(telefone or "")
                self.celular_var.set(celular or "")
                self.email_var.set(email or "")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar dados da empresa:\n{e}")

    def salvar_empresa(self):
        nome = self.nome_var.get().strip()
        endereco = self.endereco_var.get().strip()
        bairro = self.bairro_var.get().strip()
        cidade = self.cidade_var.get().strip()
        estado = self.estado_var.get().strip()
        cep = self.cep_var.get().strip()
        telefone = self.telefone_var.get().strip() or None
        celular = self.celular_var.get().strip()
        email = self.email_var.get().strip() or None

        if not nome:
            messagebox.showwarning("Aviso", "Informe o nome da empresa.")
            return
        if not endereco:
            messagebox.showwarning("Aviso", "Informe o endereço da empresa.")
            return
        if not celular:
            messagebox.showwarning("Aviso", "Informe o celular da empresa.")
            return

        try:
            conn = get_connection()
            cur = conn.cursor()

            if self.empresa_id is None:
                sql = """
                    INSERT INTO empresa
                        (nome, endereco, bairro, cidade, estado, cep,
                         telefone, celular, email)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                valores = (nome, endereco, bairro, cidade, estado, cep,
                           telefone, celular, email)
            else:
                sql = """
                    UPDATE empresa
                    SET nome=%s,
                        endereco=%s,
                        bairro=%s,
                        cidade=%s,
                        estado=%s,
                        cep=%s,
                        telefone=%s,
                        celular=%s,
                        email=%s
                    WHERE empresa_id=%s
                """
                valores = (nome, endereco, bairro, cidade, estado, cep,
                           telefone, celular, email, self.empresa_id)

            cur.execute(sql, valores)
            conn.commit()
            cur.close()
            conn.close()

            messagebox.showinfo("Sucesso", "Dados da empresa salvos com sucesso.")
            self.destroy()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar empresa no banco de dados:\n{e}")


# =====================
# Janela de configurações
# =====================
class ConfigWindow(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Configurações")
        self.geometry("400x200")
        self.resizable(False, False)
        self._build_ui()

    def _build_ui(self):
        padding = {"padx": 10, "pady": 5}
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True, **padding)

        ttk.Label(
            frame,
            text="Configurações do sistema",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", **padding)

        ttk.Label(
            frame,
            text="- Parâmetros de integração\n- Caminhos\n- Dados da Empresa",
            justify="left"
        ).pack(anchor="w", **padding)

        ttk.Button(frame, text="Cadastro da Empresa", command=self.abrir_cadastro_empresa).pack(
            anchor="w", pady=(10, 5), padx=10
        )

        ttk.Button(frame, text="Fechar", command=self.destroy).pack(pady=10)

    def abrir_cadastro_empresa(self):
        EmpresaWindow(self)

# =====================
# Janela de Veículos (CRUD + busca por placa)
# =====================
class VeiculosWindow(tk.Toplevel):
    def __init__(self, master=None, placa_inicial=None):
        super().__init__(master)
        self.title("Cadastro e Consulta de Veículos")
        self.geometry("950x550")
        self.resizable(True, True)

        self.veiculo_id = None
        self.placa_var = tk.StringVar()
        self.marca_var = tk.StringVar()
        self.modelo_var = tk.StringVar()
        self.ano_fab_var = tk.StringVar()
        self.ano_mod_var = tk.StringVar()
        self.cor_var = tk.StringVar()
        self.quilometragem_var = tk.StringVar()
        self.combustivel_var = tk.StringVar()
        self.status_var = tk.StringVar(value="DISPONIVEL")
        self.valor_aluguel_var = tk.StringVar()

        # filtros
        self.busca_placa_var = tk.StringVar()
        self.busca_status_var = tk.StringVar()

        self._build_ui()

        if placa_inicial:
            self.busca_placa_var.set(placa_inicial)
            self.carregar_veiculos(filtro_placa=placa_inicial)
        else:
            self.carregar_veiculos()

    def _build_ui(self):
        padding = {"padx": 5, "pady": 3}

        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # ----------------- filtros (placa + status) -----------------
        busca_frame = ttk.Frame(main_frame)
        busca_frame.pack(fill="x", padx=5, pady=(0, 5))

        ttk.Label(busca_frame, text="Placa:").pack(side="left", **padding)
        ttk.Entry(busca_frame, textvariable=self.busca_placa_var, width=15).pack(side="left", **padding)

        ttk.Label(busca_frame, text="Status:").pack(side="left", **padding)
        self.cb_busca_status = ttk.Combobox(
            busca_frame,
            textvariable=self.busca_status_var,
            width=15,
            state="readonly",
            values=["", "DISPONIVEL", "LOCADO", "MANUTENCAO"]
        )
        self.cb_busca_status.pack(side="left", **padding)

        ttk.Button(busca_frame, text="Pesquisar", command=self.buscar).pack(side="left", **padding)
        ttk.Button(busca_frame, text="Limpar filtros", command=self.limpar_filtros).pack(side="left", **padding)

        # ----------------- formulário -----------------
        form_frame = ttk.LabelFrame(main_frame, text="Dados do Veículo")
        form_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(form_frame, text="Placa*:").grid(row=0, column=0, sticky="w", **padding)
        ttk.Entry(form_frame, textvariable=self.placa_var, width=12).grid(row=0, column=1, **padding)

        ttk.Label(form_frame, text="Marca:").grid(row=0, column=2, sticky="w", **padding)
        ttk.Entry(form_frame, textvariable=self.marca_var, width=15).grid(row=0, column=3, **padding)

        ttk.Label(form_frame, text="Modelo:").grid(row=0, column=4, sticky="w", **padding)
        ttk.Entry(form_frame, textvariable=self.modelo_var, width=20).grid(row=0, column=5, **padding)

        ttk.Label(form_frame, text="Ano Fab.:").grid(row=1, column=0, sticky="w", **padding)
        ttk.Entry(form_frame, textvariable=self.ano_fab_var, width=8).grid(row=1, column=1, **padding)

        ttk.Label(form_frame, text="Ano Mod.:").grid(row=1, column=2, sticky="w", **padding)
        ttk.Entry(form_frame, textvariable=self.ano_mod_var, width=8).grid(row=1, column=3, **padding)

        ttk.Label(form_frame, text="Cor:").grid(row=1, column=4, sticky="w", **padding)
        ttk.Entry(form_frame, textvariable=self.cor_var, width=12).grid(row=1, column=5, **padding)

        ttk.Label(form_frame, text="KM Atual:").grid(row=2, column=0, sticky="w", **padding)
        ttk.Entry(form_frame, textvariable=self.quilometragem_var, width=10).grid(row=2, column=1, **padding)

        ttk.Label(form_frame, text="Combustível:").grid(row=2, column=2, sticky="w", **padding)
        ttk.Entry(form_frame, textvariable=self.combustivel_var, width=12).grid(row=2, column=3, **padding)

        ttk.Label(form_frame, text="Status:").grid(row=2, column=4, sticky="w", **padding)
        self.cb_status = ttk.Combobox(
            form_frame,
            textvariable=self.status_var,
            width=12,
            state="readonly",
            values=["DISPONIVEL", "LOCADO", "MANUTENCAO"]
        )
        self.cb_status.grid(row=2, column=5, **padding)
        self.status_var.set("DISPONIVEL")  # valor padrão

        ttk.Label(form_frame, text="Valor Mensal (R$):").grid(row=3, column=0, sticky="w", **padding)
        ttk.Entry(form_frame, textvariable=self.valor_aluguel_var, width=10).grid(row=3, column=1, **padding)

        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=4, column=0, columnspan=6, pady=10)

        ttk.Button(btn_frame, text="Novo", command=self.limpar_formulario).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Salvar", command=self.salvar_veiculo).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Excluir", command=self.excluir_veiculo).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Recarregar", command=self.carregar_veiculos).pack(side="left", padx=5)

        for c in range(6):
            form_frame.columnconfigure(c, weight=1)

        # ----------------- lista (Treeview) -----------------
        list_frame = ttk.LabelFrame(main_frame, text="Veículos Cadastrados")
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)

        colunas = (
            "veiculo_id", "placa", "marca", "modelo",
            "ano", "cor", "km_atual", "combustivel",
            "status", "valor"
        )
        self.tree = ttk.Treeview(list_frame, columns=colunas, show="headings", height=10)

        self.tree.heading("veiculo_id", text="ID")
        self.tree.heading("placa", text="Placa")
        self.tree.heading("marca", text="Marca")
        self.tree.heading("modelo", text="Modelo")
        self.tree.heading("ano", text="Ano")
        self.tree.heading("cor", text="Cor")
        self.tree.heading("km_atual", text="KM Atual")
        self.tree.heading("combustivel", text="Combustível")
        self.tree.heading("status", text="Status")
        self.tree.heading("valor", text="Valor Mensal")

        self.tree.column("veiculo_id", width=50, anchor="center")
        self.tree.column("placa", width=80, anchor="center")
        self.tree.column("marca", width=100)
        self.tree.column("modelo", width=150)
        self.tree.column("ano", width=70, anchor="center")
        self.tree.column("cor", width=80)
        self.tree.column("km_atual", width=90, anchor="center")
        self.tree.column("combustivel", width=100, anchor="center")
        self.tree.column("status", width=90)
        self.tree.column("valor", width=100, anchor="e")

        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

    # ----------------- filtros -----------------
    def buscar(self):
        placa = self.busca_placa_var.get().strip().upper() or None
        status = self.busca_status_var.get().strip() or None
        self.carregar_veiculos(filtro_placa=placa, filtro_status=status)

    def limpar_filtros(self):
        self.busca_placa_var.set("")
        self.busca_status_var.set("")
        self.carregar_veiculos()

    # ----------------- CRUD -----------------
    def limpar_formulario(self):
        self.veiculo_id = None
        self.placa_var.set("")
        self.marca_var.set("")
        self.modelo_var.set("")
        self.ano_fab_var.set("")
        self.ano_mod_var.set("")
        self.cor_var.set("")
        self.quilometragem_var.set("")
        self.combustivel_var.set("")
        self.status_var.set("DISPONIVEL")
        self.valor_aluguel_var.set("")

    def carregar_veiculos(self, filtro_placa=None, filtro_status=None):
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            conn = get_connection()
            cur = conn.cursor()

            base_sql = """
                SELECT veiculo_id,
                       placa,
                       marca,
                       modelo,
                       COALESCE(ano_modelo, ano_fabricacao) AS ano,
                       cor,
                       quilometragem_atual,
                       combustivel,
                       status,
                       valor_aluguel_mensal
                FROM veiculos
            """
            where_clauses = []
            params = []

            if filtro_placa:
                where_clauses.append("placa LIKE %s")
                params.append(filtro_placa + "%")

            if filtro_status:
                where_clauses.append("status = %s")
                params.append(filtro_status)

            if where_clauses:
                base_sql += " WHERE " + " AND ".join(where_clauses)

            base_sql += " ORDER BY veiculo_id DESC"

            cur.execute(base_sql, tuple(params))
            rows = cur.fetchall()
            cur.close()
            conn.close()

            for r in rows:
                (vid, placa, marca, modelo, ano,
                 cor, km_atual, combustivel, status, valor) = r
                valor_fmt = f"{valor:.2f}" if valor is not None else ""
                self.tree.insert(
                    "", "end",
                    values=(
                        vid,
                        placa,
                        marca,
                        modelo,
                        ano or "",
                        cor or "",
                        km_atual or "",
                        combustivel or "",
                        status or "",
                        valor_fmt
                    )
                )

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar veículos:\n{e}")

    def on_tree_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        item = self.tree.item(sel[0])
        (vid, placa, marca, modelo, ano,
         cor, km_atual, combustivel, status, valor) = item["values"]

        self.veiculo_id = int(vid)
        self.placa_var.set(placa)
        self.marca_var.set(marca or "")
        self.modelo_var.set(modelo or "")
        self.cor_var.set(cor or "")
        self.status_var.set(status or "")
        self.valor_aluguel_var.set(valor or "")

        self.ano_fab_var.set(ano or "")
        self.ano_mod_var.set(ano or "")

        self.quilometragem_var.set(km_atual or "")
        self.combustivel_var.set(combustivel or "")

    def salvar_veiculo(self):
        placa = self.placa_var.get().strip().upper()
        marca = self.marca_var.get().strip()
        modelo = self.modelo_var.get().strip()
        ano_fab = self.ano_fab_var.get().strip()
        ano_mod = self.ano_mod_var.get().strip()
        cor = self.cor_var.get().strip()
        km = self.quilometragem_var.get().strip()
        combustivel = self.combustivel_var.get().strip()
        status = self.status_var.get().strip() or "DISPONIVEL"
        valor = self.valor_aluguel_var.get().strip()

        if not placa:
            messagebox.showwarning("Aviso", "Informe a placa do veículo.")
            return

        try:
            ano_fab_int = int(ano_fab) if ano_fab else None
            ano_mod_int = int(ano_mod) if ano_mod else None
        except ValueError:
            messagebox.showwarning("Aviso", "Ano de fabricação/modelo inválido.")
            return

        try:
            km_int = int(km) if km else None
        except ValueError:
            messagebox.showwarning("Aviso", "Quilometragem inválida.")
            return

        try:
            valor_dec = float(valor.replace(",", ".")) if valor else None
        except ValueError:
            messagebox.showwarning("Aviso", "Valor de aluguel inválido.")
            return

        try:
            conn = get_connection()
            cur = conn.cursor()

            if self.veiculo_id is None:
                sql = """
                    INSERT INTO veiculos
                        (placa, marca, modelo, ano_fabricacao, ano_modelo,
                         cor, quilometragem_atual, combustivel, status,
                         valor_aluguel_mensal)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                valores = (
                    placa, marca or None, modelo or None,
                    ano_fab_int, ano_mod_int,
                    cor or None, km_int, combustivel or None, status or None,
                    valor_dec
                )
            else:
                sql = """
                    UPDATE veiculos
                    SET placa=%s, marca=%s, modelo=%s,
                        ano_fabricacao=%s, ano_modelo=%s,
                        cor=%s, quilometragem_atual=%s,
                        combustivel=%s, status=%s,
                        valor_aluguel_mensal=%s
                    WHERE veiculo_id=%s
                """
                valores = (
                    placa, marca or None, modelo or None,
                    ano_fab_int, ano_mod_int,
                    cor or None, km_int, combustivel or None, status or None,
                    valor_dec, self.veiculo_id
                )

            cur.execute(sql, valores)
            conn.commit()
            cur.close()
            conn.close()

            messagebox.showinfo("Sucesso", "Veículo salvo com sucesso.")
            self.limpar_formulario()
            self.carregar_veiculos()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar veículo:\n{e}")

    def excluir_veiculo(self):
        if self.veiculo_id is None:
            messagebox.showwarning("Aviso", "Selecione um veículo para excluir.")
            return

        if not messagebox.askyesno("Confirmação", "Deseja realmente excluir este veículo?"):
            return

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM veiculos WHERE veiculo_id=%s", (self.veiculo_id,))
            conn.commit()
            cur.close()
            conn.close()

            messagebox.showinfo("Sucesso", "Veículo excluído com sucesso.")
            self.limpar_formulario()
            self.carregar_veiculos()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao excluir veículo:\n{e}")

# =====================
# Janela de Clientes
# =====================
class ClientesWindow(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Cadastro de Clientes")
        self.geometry("900x550")
        self.resizable(True, True)

        self.cliente_id = None
        self.nome_var = tk.StringVar()
        self.cpf_var = tk.StringVar()
        self.telefone_var = tk.StringVar()
        self.telefone2_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.endereco_var = tk.StringVar()
        self.bairro_var = tk.StringVar()
        self.cidade_var = tk.StringVar()
        self.estado_var = tk.StringVar()
        self.cep_var = tk.StringVar()
        self.status_var = tk.StringVar(value="ATIVO")
        self.placa_var = tk.StringVar()

        # NOVO: campo de busca por nome
        self.busca_nome_var = tk.StringVar()

        self._build_ui()
        self.carregar_placas()
        self.carregar_clientes()

    def _build_ui(self):
        padding = {"padx": 5, "pady": 3}

        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # ----------------- Linha de busca por nome -----------------
        busca_frame = ttk.Frame(main_frame)
        busca_frame.pack(fill="x", padx=5, pady=(0, 5))

        ttk.Label(busca_frame, text="Buscar por nome:").pack(side="left", **padding)
        ttk.Entry(busca_frame, textvariable=self.busca_nome_var, width=30).pack(side="left", **padding)
        ttk.Button(busca_frame, text="Pesquisar", command=self.buscar_por_nome).pack(side="left", **padding)
        ttk.Button(busca_frame, text="Limpar busca", command=self.limpar_busca).pack(side="left", **padding)
        # -----------------------------------------------------------

        form_frame = ttk.LabelFrame(main_frame, text="Dados do Cliente")
        form_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(form_frame, text="Nome*:").grid(row=0, column=0, sticky="w", **padding)
        ttk.Entry(form_frame, textvariable=self.nome_var, width=30).grid(
            row=0, column=1, columnspan=3, sticky="w", **padding
        )

        ttk.Label(form_frame, text="CPF*:").grid(row=0, column=4, sticky="w", **padding)
        ttk.Entry(form_frame, textvariable=self.cpf_var, width=18).grid(
            row=0, column=5, sticky="w", **padding
        )

        ttk.Label(form_frame, text="Telefone:").grid(row=1, column=0, sticky="w", **padding)
        ttk.Entry(form_frame, textvariable=self.telefone_var, width=18).grid(
            row=1, column=1, sticky="w", **padding
        )

        ttk.Label(form_frame, text="Telefone 2:").grid(row=1, column=2, sticky="w", **padding)
        ttk.Entry(form_frame, textvariable=self.telefone2_var, width=18).grid(
            row=1, column=3, sticky="w", **padding
        )

        ttk.Label(form_frame, text="E-mail:").grid(row=1, column=4, sticky="w", **padding)
        ttk.Entry(form_frame, textvariable=self.email_var, width=25).grid(
            row=1, column=5, sticky="w", **padding
        )

        ttk.Label(form_frame, text="Endereço:").grid(row=2, column=0, sticky="w", **padding)
        ttk.Entry(form_frame, textvariable=self.endereco_var, width=30).grid(
            row=2, column=1, columnspan=3, sticky="w", **padding
        )

        ttk.Label(form_frame, text="Bairro:").grid(row=3, column=0, sticky="w", **padding)
        ttk.Entry(form_frame, textvariable=self.bairro_var, width=20).grid(
            row=3, column=1, sticky="w", **padding
        )

        ttk.Label(form_frame, text="Cidade:").grid(row=3, column=2, sticky="w", **padding)
        ttk.Entry(form_frame, textvariable=self.cidade_var, width=20).grid(
            row=3, column=3, sticky="w", **padding
        )

        ttk.Label(form_frame, text="Estado:").grid(row=3, column=4, sticky="w", **padding)
        ttk.Entry(form_frame, textvariable=self.estado_var, width=4).grid(
            row=3, column=5, sticky="w", **padding
        )

        ttk.Label(form_frame, text="CEP:").grid(row=4, column=0, sticky="w", **padding)
        ttk.Entry(form_frame, textvariable=self.cep_var, width=15).grid(
            row=4, column=1, sticky="w", **padding
        )

        ttk.Label(form_frame, text="Status:").grid(row=4, column=2, sticky="w", **padding)
        ttk.Entry(form_frame, textvariable=self.status_var, width=10).grid(
            row=4, column=3, sticky="w", **padding
        )

        ttk.Label(form_frame, text="Placa do Veículo:").grid(row=5, column=0, sticky="w", **padding)
        self.cb_placa = ttk.Combobox(form_frame, textvariable=self.placa_var, width=15, state="readonly")
        self.cb_placa.grid(row=5, column=1, sticky="w", **padding)

        ttk.Button(form_frame, text="Abrir Veículo", command=self.abrir_veiculo_selecionado).grid(
            row=5, column=2, sticky="w", **padding
        )

        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=6, column=0, columnspan=6, pady=10)

        ttk.Button(btn_frame, text="Novo", command=self.limpar_formulario).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Salvar", command=self.salvar_cliente).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Excluir", command=self.excluir_cliente).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Recarregar", command=self.carregar_clientes).pack(side="left", padx=5)

        for c in range(6):
            form_frame.columnconfigure(c, weight=1)

        list_frame = ttk.LabelFrame(main_frame, text="Clientes Cadastrados")
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)

        colunas = ("cliente_id", "nome", "cpf", "telefone", "placa", "status")
        self.tree = ttk.Treeview(list_frame, columns=colunas, show="headings", height=10)
        self.tree.heading("cliente_id", text="ID")
        self.tree.heading("nome", text="Nome")
        self.tree.heading("cpf", text="CPF")
        self.tree.heading("telefone", text="Telefone")
        self.tree.heading("placa", text="Placa Veículo")
        self.tree.heading("status", text="Status")

        self.tree.column("cliente_id", width=50, anchor="center")
        self.tree.column("nome", width=200)
        self.tree.column("cpf", width=110, anchor="center")
        self.tree.column("telefone", width=110)
        self.tree.column("placa", width=100, anchor="center")
        self.tree.column("status", width=80, anchor="center")

        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

    # ------- busca por nome (novo) -------
    def buscar_por_nome(self):
        nome = self.busca_nome_var.get().strip()
        self.carregar_clientes(filtro_nome=nome if nome else None)

    def limpar_busca(self):
        self.busca_nome_var.set("")
        self.carregar_clientes()
    # -------------------------------------

    def carregar_placas(self):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT placa FROM veiculos ORDER BY placa")
            rows = cur.fetchall()
            cur.close()
            conn.close()
            placas = [r[0] for r in rows]
            self.cb_placa["values"] = placas
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar placas de veículos:\n{e}")

    def limpar_formulario(self):
        self.cliente_id = None
        self.nome_var.set("")
        self.cpf_var.set("")
        self.telefone_var.set("")
        self.telefone2_var.set("")
        self.email_var.set("")
        self.endereco_var.set("")
        self.bairro_var.set("")
        self.cidade_var.set("")
        self.estado_var.set("")
        self.cep_var.set("")
        self.status_var.set("ATIVO")
        self.placa_var.set("")

    def carregar_clientes(self, filtro_nome=None):
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            conn = get_connection()
            cur = conn.cursor()

            if filtro_nome:
                cur.execute(
                    """
                    SELECT c.cliente_id, c.nome, c.cpf, c.telefone,
                           v.placa, c.status
                    FROM clientes c
                    LEFT JOIN veiculos v ON v.veiculo_id = c.veiculo_id
                    WHERE c.nome LIKE %s
                    ORDER BY c.cliente_id DESC
                    """,
                    ("%" + filtro_nome + "%",)
                )
            else:
                cur.execute(
                    """
                    SELECT c.cliente_id, c.nome, c.cpf, c.telefone,
                           v.placa, c.status
                    FROM clientes c
                    LEFT JOIN veiculos v ON v.veiculo_id = c.veiculo_id
                    ORDER BY c.cliente_id DESC
                    """
                )

            rows = cur.fetchall()
            cur.close()
            conn.close()

            for r in rows:
                cid, nome, cpf, tel, placa, status = r
                self.tree.insert(
                    "", "end",
                    values=(cid, nome, cpf, tel or "", placa or "", status or "")
                )
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar clientes:\n{e}")

    # (mantenha on_tree_select, salvar_cliente, excluir_cliente, abrir_veiculo_selecionado iguais)

    def on_tree_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        item = self.tree.item(sel[0])
        cid, nome, cpf, tel, placa, status = item["values"]

        self.cliente_id = cid
        self.nome_var.set(nome or "")
        self.cpf_var.set(cpf or "")
        self.telefone_var.set(tel or "")
        self.status_var.set(status or "")
        self.placa_var.set(placa or "")

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT telefone2, email, endereco, bairro, cidade, estado, cep
                FROM clientes
                WHERE cliente_id = %s
                """,
                (cid,)
            )
            row = cur.fetchone()
            cur.close()
            conn.close()

            if row:
                tel2, email, end, bairro, cidade, estado, cep = row
                self.telefone2_var.set(tel2 or "")
                self.email_var.set(email or "")
                self.endereco_var.set(end or "")
                self.bairro_var.set(bairro or "")
                self.cidade_var.set(cidade or "")
                self.estado_var.set(estado or "")
                self.cep_var.set(cep or "")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar detalhes do cliente:\n{e}")

    def salvar_cliente(self):
        nome = self.nome_var.get().strip()
        cpf = self.cpf_var.get().strip()
        telefone = self.telefone_var.get().strip() or None
        telefone2 = self.telefone2_var.get().strip() or None
        email = self.email_var.get().strip() or None
        endereco = self.endereco_var.get().strip() or None
        bairro = self.bairro_var.get().strip() or None
        cidade = self.cidade_var.get().strip() or None
        estado = self.estado_var.get().strip() or None
        cep = self.cep_var.get().strip() or None
        status = self.status_var.get().strip() or "ATIVO"
        placa = self.placa_var.get().strip().upper() or None

        if not nome:
            messagebox.showwarning("Aviso", "Informe o nome do cliente.")
            return
        if not cpf:
            messagebox.showwarning("Aviso", "Informe o CPF do cliente.")
            return

        veiculo_id = None
        if placa:
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("SELECT veiculo_id FROM veiculos WHERE placa=%s", (placa,))
                row = cur.fetchone()
                cur.close()
                conn.close()
                if row:
                    veiculo_id = row[0]
                else:
                    if not messagebox.askyesno(
                        "Placa não encontrada",
                        "Nenhum veículo com essa placa foi encontrado.\nDeseja salvar o cliente mesmo assim (sem vínculo)?"
                    ):
                        return
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao buscar veículo pela placa:\n{e}")
                return

        try:
            conn = get_connection()
            cur = conn.cursor()

            if self.cliente_id is None:
                sql = """
                    INSERT INTO clientes
                        (nome, cpf, telefone, telefone2, email,
                         endereco, bairro, cidade, estado, cep,
                         status, veiculo_id)
                    VALUES (%s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s,
                            %s, %s)
                """
                valores = (
                    nome, cpf, telefone, telefone2, email,
                    endereco, bairro, cidade, estado, cep,
                    status, veiculo_id
                )
            else:
                sql = """
                    UPDATE clientes
                    SET nome=%s, cpf=%s, telefone=%s, telefone2=%s, email=%s,
                        endereco=%s, bairro=%s, cidade=%s, estado=%s, cep=%s,
                        status=%s, veiculo_id=%s
                    WHERE cliente_id=%s
                """
                valores = (
                    nome, cpf, telefone, telefone2, email,
                    endereco, bairro, cidade, estado, cep,
                    status, veiculo_id, self.cliente_id
                )

            cur.execute(sql, valores)
            conn.commit()
            cur.close()
            conn.close()

            messagebox.showinfo("Sucesso", "Cliente salvo com sucesso.")
            self.limpar_formulario()
            self.carregar_clientes()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar cliente:\n{e}")

    def excluir_cliente(self):
        if self.cliente_id is None:
            messagebox.showwarning("Aviso", "Selecione um cliente para excluir.")
            return

        if not messagebox.askyesno("Confirmação", "Deseja realmente excluir este cliente?"):
            return

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM clientes WHERE cliente_id=%s", (self.cliente_id,))
            conn.commit()
            cur.close()
            conn.close()

            messagebox.showinfo("Sucesso", "Cliente excluído com sucesso.")
            self.limpar_formulario()
            self.carregar_clientes()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao excluir cliente:\n{e}")

    def abrir_veiculo_selecionado(self):
        placa = self.placa_var.get().strip().upper()
        if not placa:
            messagebox.showwarning("Aviso", "Selecione uma placa para abrir o veículo.")
            return
        VeiculosWindow(self, placa_inicial=placa)


# =====================
# Janela principal (pós-login)
# =====================
class MainWindow(tk.Toplevel):
    def __init__(self, master=None, usuario_id=None, login=None):
        super().__init__(master)
        self.title("Sistema de Gestão de Locações - Principal")
        self.geometry("700x400")
        self.resizable(True, True)

        self.usuario_id = usuario_id
        self.login = login

        self._build_ui()

    def _build_ui(self):
        padding = {"padx": 10, "pady": 5}

        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True, **padding)

        ttk.Label(
            frame,
            text=f"Bem-vindo, {self.login}!",
            font=("Segoe UI", 12, "bold")
        ).grid(row=0, column=0, sticky="w", **padding)

        ttk.Button(frame, text="Cadastro de Veículos", command=self.abrir_veiculos).grid(
            row=1, column=0, sticky="w", **padding
        )
        ttk.Button(frame, text="Cadastro de Clientes", command=self.abrir_clientes).grid(
            row=2, column=0, sticky="w", **padding
        )
        ttk.Button(frame, text="Manutenções").grid(row=3, column=0, sticky="w", **padding)
        ttk.Button(frame, text="Recebimentos").grid(row=4, column=0, sticky="w", **padding)

        ttk.Button(frame, text="Sair do Sistema", command=self.fechar_sistema).grid(
            row=5, column=0, sticky="w", pady=(20, 5), padx=10
        )

        frame.columnconfigure(0, weight=1)

    def abrir_veiculos(self):
        VeiculosWindow(self)

    def abrir_clientes(self):
        ClientesWindow(self)

    def fechar_sistema(self):
        self.destroy()
        if self.master is not None:
            self.master.destroy()


# =====================
# Janela de Login
# =====================
class LoginApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Controle de Locação de Veículos - Login")
        self.geometry("450x300")
        self.resizable(False, False)

        self.usuario_var = tk.StringVar()
        self.senha_var = tk.StringVar()

        self._build_ui()

    def _build_ui(self):
        padding = {"padx": 10, "pady": 5}

        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True, **padding)

        titulo = ttk.Label(frame, text="Sistema de Gestão de Locações", font=("Segoe UI", 12, "bold"))
        titulo.grid(row=0, column=0, columnspan=3, pady=(15, 20))

        # REMOVIDO: botão Cadastro da Empresa aqui

        btn_cfg = ttk.Button(frame, text="Configurações", command=self.abrir_configuracoes)
        btn_cfg.grid(row=1, column=2, sticky="e", **padding)

        ttk.Separator(frame, orient="horizontal").grid(row=2, column=0, columnspan=3, sticky="ew", pady=(10, 15))

        ttk.Label(frame, text="Usuário:").grid(row=3, column=0, sticky="e", **padding)
        ttk.Entry(frame, textvariable=self.usuario_var, width=30).grid(
            row=3, column=1, columnspan=2, sticky="w", **padding
        )

        ttk.Label(frame, text="Senha:").grid(row=4, column=0, sticky="e", **padding)
        ttk.Entry(frame, textvariable=self.senha_var, show="*", width=30).grid(
            row=4, column=1, columnspan=2, sticky="w", **padding
        )

        btn_login = ttk.Button(frame, text="Entrar", command=self.fazer_login)
        btn_login.grid(row=5, column=1, sticky="e", pady=(15, 5), padx=5)

        btn_sair = ttk.Button(frame, text="Sair", command=self.destroy)
        btn_sair.grid(row=5, column=2, sticky="w", pady=(15, 5), padx=5)

        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=1)


    def abrir_configuracoes(self):
        ConfigWindow(self)

    def fazer_login(self):
        usuario = self.usuario_var.get().strip()
        senha = self.senha_var.get().strip()

        if not usuario or not senha:
            messagebox.showwarning("Aviso", "Informe usuário e senha.")
            return

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT usuario_id, login
                FROM usuarios
                WHERE login = %s
                  AND senha_hash = %s
                  AND ativo = 1
                """,
                (usuario, senha)
            )
            row = cur.fetchone()
            cur.close()
            conn.close()

            if not row:
                messagebox.showerror("Erro", "Usuário ou senha inválidos.")
                return

            usuario_id, login = row

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao validar login no banco de dados:\n{e}")
            return

        main_win = MainWindow(master=self, usuario_id=usuario_id, login=login)
        main_win.grab_set()
        self.withdraw()


if __name__ == "__main__":
    app = LoginApp()
    app.mainloop()

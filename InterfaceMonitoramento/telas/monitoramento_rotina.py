# monitoramento_rotina.py
import tkinter as tk
from tkinter import ttk, messagebox

class JanelaMonitoramentoRotina(tk.Toplevel):
    def __init__(self, master, model):
        super().__init__(master)
        self.title("Monitoramento Rotina")
        self.geometry("800x600")
        self.resizable(True, True)
        self.model = model

        self.dedicated_urs = [
            "1BFC3BFA-D454-4123-84DD-B6DD9F2C0F08",
            "1D8AA8E2-408D-4946-87FF-52849F80DEC5",
            "298D95CA-6E34-47A5-8C9A-6D73E4EA5A1D",
            "41A3FD3A-470C-4CBA-A7CF-6C1F8BAC29D5",
            "8C863D87-8420-43B1-A2C9-7B3DEB8DE30E",
            "CE42094B-E45C-4D75-AA24-A57DD3AF5E21"
        ]

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill='both')

        self.frames = {}
        self.create_tabs()

    def create_tabs(self):
        tabs_info = {
            'Geral 24h': self.exibir_geral24h,
            'Clientes Dedicados 24h': self.exibir_clientes_dedicados,
            'Expediente 6h': self.exibir_expediente,
            'Consulta Pública': self.exibir_consulta_publica
        }

        for tab_name, tab_method in tabs_info.items():
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=tab_name)
            self.frames[tab_name] = frame
            tab_method(frame)

    def exibir_geral24h(self, frame):
        try:
            resultados = self.model.get_query_geral24h()
            self.criar_tabela(frame, resultados)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao obter dados: {e}")

    def exibir_clientes_dedicados(self, frame):
        try:
            resultados = self.model.get_query_clientes_dedicados_24h(self.dedicated_urs)
            self.criar_tabela(frame, resultados)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao obter dados: {e}")

    def exibir_expediente(self, frame):
        try:
            resultados = self.model.get_query_expediente_6h()
            self.criar_tabela(frame, resultados)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao obter dados: {e}")

    def exibir_consulta_publica(self, frame):
        # Implementação semelhante à anterior, ajustada para o novo modelo
        controls_frame = ttk.Frame(frame)
        controls_frame.pack(pady=10)

        ttk.Label(controls_frame, text="Selecione o intervalo de tempo:").pack(side=tk.LEFT, padx=5)

        self.range_var = tk.StringVar(value='24h')

        range_options = ['24h', '48h', 'semana', 'mes']
        self.range_combo = ttk.Combobox(controls_frame, textvariable=self.range_var, values=range_options, state='readonly')
        self.range_combo.pack(side=tk.LEFT, padx=5)

        btn_atualizar = ttk.Button(controls_frame, text="Atualizar", command=self.atualizar_consulta_publica)
        btn_atualizar.pack(side=tk.LEFT, padx=5)

        self.result_frame = ttk.Frame(frame)
        self.result_frame.pack(expand=True, fill='both')

        self.atualizar_consulta_publica()

    def atualizar_consulta_publica(self):
        for widget in self.result_frame.winfo_children():
            widget.destroy()

        range_value = self.range_var.get()
        dados = self.model.get_dados_api(range_value)

        if dados:
            lbl_data_criacao = ttk.Label(self.result_frame, text=f"Data de Criação: {dados.get('data_criacao', 'N/A')}")
            lbl_data_criacao.pack(pady=5)

            lbl_percentual = ttk.Label(self.result_frame, text=f"Percentual de Processos Atualizados ({range_value}): {dados.get('percentual_processos_atualizados_24h', 'N/A')}")
            lbl_percentual.pack(pady=5)

            status = dados.get('status', 'OK')
            lbl_status = ttk.Label(self.result_frame, text=f"Status: {status}")
            lbl_status.pack(pady=5)

            lbl_status.config(foreground='red' if status == 'fudeu' else 'green')
        else:
            lbl_erro = ttk.Label(self.result_frame, text="Não foi possível obter os dados da API.", foreground='red')
            lbl_erro.pack(pady=5)

    def criar_tabela(self, parent_frame, data):
        colunas = ('_id', 'sql_ur', 'dataDeAlteracao', 'dataDoSql')
        tree = ttk.Treeview(parent_frame, columns=colunas, show='headings')

        scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        for coluna in colunas:
            tree.heading(coluna, text=coluna)
            tree.column(coluna, width=200)

        for item in data:
            valores = (
                str(item.get('_id')),
                item.get('sql', {}).get('ur', ''),
                item.get('dataDeAlteracao').strftime('%Y-%m-%d %H:%M:%S') if item.get('dataDeAlteracao') else '',
                item.get('dataDoSql').strftime('%Y-%m-%d %H:%M:%S') if item.get('dataDoSql') else ''
            )
            tree.insert('', tk.END, values=valores)

        tree.pack(expand=True, fill='both')


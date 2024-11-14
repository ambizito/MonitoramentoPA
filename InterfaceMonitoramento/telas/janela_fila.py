import tkinter as tk
from tkinter import ttk, messagebox
import threading
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import subprocess
import re
import time
from collections import defaultdict

class JanelaFila(tk.Toplevel):
    def __init__(self, master, model, controller):
        super().__init__(master)
        self.title("Fila de Processos")
        self.geometry("800x600")
        self.model = model
        self.controller = controller
        self.fila_processos = self.controller.fila_processos
        self.fila_processos.registrar_observador(self.atualizar_interface)
        self.create_widgets()

        # Dicionário para controlar tokens por tribunal
        self.tokens_por_tribunal = defaultdict(set)

    def create_widgets(self):
        print("Criando widgets da JanelaFila")

        # Cria o Notebook para as abas
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill='both')

        # Frame principal para a lista de tribunais
        self.frame_principal = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_principal, text="Tribunais")

        # Exibir a lista de processos na fila agrupados por tribunal
        colunas = ('tribunal', 'percentual', 'quantidade')
        self.tree = ttk.Treeview(self.frame_principal, columns=colunas, show='headings')

        for coluna in colunas:
            self.tree.heading(coluna, text=coluna.title())
            self.tree.column(coluna, width=200)

        self.tree.pack(expand=True, fill='both')

        # Botão para rodar a fila
        btn_rodar_fila = ttk.Button(self.frame_principal, text="Rodar Fila", command=self.rodar_fila)
        btn_rodar_fila.pack(pady=10)

        # Bind para detectar clique duplo em um tribunal
        self.tree.bind('<Double-1>', self.on_item_double_clicked)

        # Popula o Treeview
        self.populate_treeview()

    def on_item_double_clicked(self, event):
        selected_item = self.tree.selection()
        if selected_item:
            item = self.tree.item(selected_item)
            tribunal = item['values'][0]
            self.abrir_aba_tribunal(tribunal)

    def abrir_aba_tribunal(self, tribunal):
        # Verifica se a aba já existe
        for tab in self.notebook.tabs():
            if self.notebook.tab(tab, "text") == tribunal:
                self.notebook.select(tab)
                return

        # Cria um novo frame para o tribunal
        frame_tribunal = ttk.Frame(self.notebook)
        self.notebook.add(frame_tribunal, text=tribunal)
        self.notebook.select(frame_tribunal)

        # Chama o método para criar os widgets da aba do tribunal
        self.criar_aba_tribunal(frame_tribunal, tribunal)

    def criar_aba_tribunal(self, frame, tribunal):
        # Divide o frame em duas partes
        frame_esquerda = ttk.Frame(frame)
        frame_direita = ttk.Frame(frame)

        frame_esquerda.pack(side='left', expand=True, fill='both')
        frame_direita.pack(side='left', expand=True, fill='both')

        # Treeview para listar os processos
        colunas = ('numero', 'status')
        tree_processos = ttk.Treeview(frame_esquerda, columns=colunas, show='headings')

        for coluna in colunas:
            tree_processos.heading(coluna, text=coluna.title())
            tree_processos.column(coluna, width=150)

        tree_processos.pack(expand=True, fill='both')

        # Obter os processos do tribunal
        processos = self.obter_processos_por_tribunal(tribunal)

        # Popula o treeview
        for processo in processos:
            status = processo.get('status', 'Pendente')
            valores = (
                processo.get('numero', ''),
                status,
            )
            tree_processos.insert('', tk.END, values=valores)

        # Armazena referências aos widgets para atualização
        frame.tree_processos = tree_processos
        frame.fig = Figure(figsize=(5, 4), dpi=100)
        self.criar_graficos(frame.fig, processos)

        # Embutir a figura no Tkinter
        frame.canvas = FigureCanvasTkAgg(frame.fig, master=frame_direita)
        frame.canvas.draw()
        frame.canvas.get_tk_widget().pack(expand=True, fill='both')

    def obter_processos_por_tribunal(self, tribunal):
        tribunal_normalizado = tribunal.strip().lower()
        return [proc for proc in self.fila_processos.obter_fila() if proc['tribunal'].strip().lower() == tribunal_normalizado]

    def populate_treeview(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        status_por_tribunal = self.obter_status_por_tribunal()
        print(f"Status por tribunal: {status_por_tribunal}")
        for tribunal, info in status_por_tribunal.items():
            total_processos = len(info['processos'])
            concluidos = info['concluidos']
            percentual = (concluidos / total_processos) * 100 if total_processos > 0 else 0
            valores = (
                tribunal,
                f"{percentual:.2f}%",  # Porcentagem processada
                f"{concluidos}/{total_processos}",  # Quantidade de processos processados / total
            )
            self.tree.insert('', tk.END, values=valores)

    def rodar_fila(self):
        # Agrupar processos por tribunal e tokens
        processos_por_tribunal = defaultdict(lambda: defaultdict(list))

        for processo in self.fila_processos.obter_fila():
            tribunal = processo['tribunal'].strip().lower()
            token_id = processo['token_id']
            processos_por_tribunal[tribunal][token_id].append(processo)

        # Iniciar a execução por tribunal
        for tribunal, tokens in processos_por_tribunal.items():
            threading.Thread(target=self.executar_tribunal, args=(tribunal, tokens), daemon=True).start()


        for processo in self.fila_processos.obter_fila():
            tribunal = processo['tribunal'].strip().lower()  # Normalizar o nome do tribunal
            token_id = processo['token_id']
            processos_por_tribunal[tribunal][token_id].append(processo)

        # Iniciar a execução por tribunal
        for tribunal, tokens in processos_por_tribunal.items():
            threading.Thread(target=self.executar_tribunal, args=(tribunal, tokens), daemon=True).start()

    def executar_tribunal(self, tribunal, tokens):
        for token_id, processos in tokens.items():
            # Executar processos do token
            self.executar_processos(tribunal, token_id, processos)
            # Aguarda a conclusão antes de iniciar o próximo token
            while any(processo.get('status') != 'Concluído' and processo.get('status') != 'Erro' for processo in processos):
                time.sleep(1)

    def executar_processos(self, tribunal, token_id, processos):
        def processamento():
            try:
                # Verificar se o token já está sendo processado neste tribunal
                if token_id in self.tokens_por_tribunal[tribunal]:
                    print(f"Token {token_id} já está sendo processado no tribunal {tribunal}.")
                    return
                else:
                    self.tokens_por_tribunal[tribunal].add(token_id)

                # Chamar o Logins para o token
                executable_path = r"C:\Users\AndreAzevedo\Source\Repos\ProcessoAgil\ProcessoAgil.Logins\bin\Debug\ProcessoAgil.Logins.exe"
                working_dir = r"C:\Users\AndreAzevedo\Source\Repos\ProcessoAgil\ProcessoAgil.Logins\bin\Debug"

                comando = [executable_path, "-id", token_id, "--rodar"]

                process = subprocess.Popen(
                    comando,
                    cwd=working_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )

                for line in process.stdout:
                    print(line, end='')
                    line = line.strip()
                    self.processar_linha_log(line, processos)
                    self.fila_processos.notificar_observadores()

                process.wait()

                # Remover o token do conjunto após a conclusão
                self.tokens_por_tribunal[tribunal].remove(token_id)

            except Exception as e:
                print(f"Erro ao executar o Logins: {e}")
                # Remover o token em caso de erro
                self.tokens_por_tribunal[tribunal].discard(token_id)

        threading.Thread(target=processamento, daemon=True).start()

    def processar_linha_log(self, line, processos_token):
        match_sucesso = re.search(r'advogado\s+([\d.-]+)\s+>>\s+Processo com', line)
        match_erro_processo = re.search(r'advogado\s+([\d.-]+)\s+>>\s+(.*)', line)
        match_erro_geral = re.search(r'^.*Erro no acesso:\s+(.*)$', line)

        if match_sucesso:
            numero_processo = match_sucesso.group(1)
            for processo in processos_token:
                if processo['numero'] == numero_processo:
                    processo['status'] = 'Concluído'
                    processo['tempo_conclusao'] = time.time()
                    break
        elif match_erro_processo:
            numero_processo = match_erro_processo.group(1)
            mensagem = match_erro_processo.group(2)
            for processo in processos_token:
                if processo['numero'] == numero_processo:
                    processo['status'] = 'Erro'
                    processo['mensagem_erro'] = mensagem
                    processo['tempo_conclusao'] = time.time()
                    break
        elif match_erro_geral:
            mensagem = match_erro_geral.group(1)
            for processo in processos_token:
                processo['status'] = 'Erro'
                processo['mensagem_erro'] = mensagem
                processo['tempo_conclusao'] = time.time()

    def atualizar_interface(self):
        print("Atualizando interface da JanelaFila")
        # Atualizar a Treeview principal
        self.atualizar_treeview_principal()
        # Atualiza as abas abertas
        for tab_id in self.notebook.tabs():
            tab_text = self.notebook.tab(tab_id, "text")
            if tab_text != "Tribunais":
                # Atualizar apenas os processos modificados na aba
                frame = self.notebook.nametowidget(tab_id)
                self.atualizar_aba_tribunal(frame, tab_text)

    def atualizar_treeview_principal(self):
        status_por_tribunal = self.obter_status_por_tribunal()
        for item_id in self.tree.get_children():
            item = self.tree.item(item_id)
            tribunal = item['values'][0]
            info = status_por_tribunal.get(tribunal)
            if info:
                total_processos = len(info['processos'])
                concluidos = info['concluidos']
                percentual = (concluidos / total_processos) * 100 if total_processos > 0 else 0
                novos_valores = (
                    tribunal,
                    f"{percentual:.2f}%",
                    f"{concluidos}/{total_processos}",
                )
                self.tree.item(item_id, values=novos_valores)

    def atualizar_aba_tribunal(self, frame, tribunal):
        # Encontrar o Treeview dentro do frame
        tree_processos = getattr(frame, 'tree_processos', None)
        if not tree_processos:
            return

        # Obter os processos do tribunal
        processos = self.obter_processos_por_tribunal(tribunal)

        # Atualizar os itens no Treeview
        for item_id in tree_processos.get_children():
            item = tree_processos.item(item_id)
            numero_processo = item['values'][0]
            # Encontrar o processo correspondente
            processo = next((p for p in processos if p.get('numero') == numero_processo), None)
            if processo:
                status = processo.get('status', 'Pendente')
                if status != item['values'][1]:
                    # Atualizar o status no Treeview
                    tree_processos.item(item_id, values=(numero_processo, status))

        # Atualizar o gráfico
        self.atualizar_graficos(frame, processos)

    def atualizar_graficos(self, frame, processos):
        fig = frame.fig
        self.criar_graficos(fig, processos)
        frame.canvas.draw()

    def destroy(self):
        self.fila_processos.remover_observador(self.atualizar_interface)
        super().destroy()

    def obter_status_por_tribunal(self):
        status_por_tribunal = defaultdict(lambda: {'processos': [], 'concluidos': 0})
        for processo in self.fila_processos.obter_fila():
            tribunal = processo['tribunal'].strip().lower()  # Normalizar o nome do tribunal
            status_por_tribunal[tribunal]['processos'].append(processo)
            if processo.get('status') == 'Concluído':
                status_por_tribunal[tribunal]['concluidos'] += 1
        return status_por_tribunal

    def criar_graficos(self, fig, processos):
        # Limpa a figura
        fig.clear()

        # Lista de tempos de conclusão dos processos
        tempos_conclusao = [proc.get('tempo_conclusao') for proc in processos if proc.get('tempo_conclusao')]
        if not tempos_conclusao:
            tempos_conclusao = [0]

        # Ordena os tempos
        tempos_conclusao.sort()
        tempos_relativos = [t - tempos_conclusao[0] for t in tempos_conclusao]

        # Gráfico de Processos Concluídos ao longo do tempo
        ax = fig.add_subplot(111)
        ax.plot(tempos_relativos, range(1, len(tempos_relativos) + 1), marker='o')
        ax.set_xlabel('Tempo (s) desde o início')
        ax.set_ylabel('Processos Concluídos')
        ax.set_title('Velocidade de Processamento')
        ax.grid(True)

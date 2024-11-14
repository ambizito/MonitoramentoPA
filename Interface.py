# app.py
import re
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from TasksMongoDB import (
    query_geral24h,
    query_clientes_dedicados_24h,
    query_expediente_6h
)
from TasksMongoDB import obter_detalhes_ur as obter_detalhes_ur_mongo
from TasksApis import obter_dados_api, obter_tabela_tokens
from db_connection import get_mongo_client
from logging_config import logger

class Aplicacao(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Aplicação de Monitoramento")
        self.geometry("400x300")
        self.resizable(True, True)
        self.criar_botoes_principais()

    def criar_botoes_principais(self):
        frame_botoes = ttk.Frame(self)
        frame_botoes.pack(expand=True)

        btn_rotina = ttk.Button(
            frame_botoes,
            text="Monitoramento Rotina",
            command=self.janela_rotina
        )
        btn_rotina.pack(pady=10)

        btn_pendentes = ttk.Button(
            frame_botoes,
            text="Monitoramento Pendentes",
            command=self.janela_pendentes
        )
        btn_pendentes.pack(pady=10)

        btn_acervo = ttk.Button(
            frame_botoes,
            text="Monitoramento Acervo",
            command=self.janela_acervo
        )
        btn_acervo.pack(pady=10)

    def janela_rotina(self):
        janela = JanelaMonitoramentoRotina(self)

    def janela_pendentes(self):
        janela = JanelaSecundaria(self, "Monitoramento Pendentes")

    def janela_acervo(self):
        janela = JanelaMonitoramentoAcervo(self)

class JanelaMonitoramentoRotina(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Monitoramento Rotina")
        self.geometry("800x600")
        self.resizable(True, True)

        # Não é mais necessário obter 'mongoTribunalFila' aqui
        # Remova a chamada a 'get_mongo_client()' neste ponto

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

        self.frame_geral24h = ttk.Frame(self.notebook)
        self.frame_clientes_dedicados = ttk.Frame(self.notebook)
        self.frame_expediente = ttk.Frame(self.notebook)
        self.frame_consulta_publica = ttk.Frame(self.notebook)

        self.notebook.add(self.frame_geral24h, text='Geral 24h')
        self.notebook.add(self.frame_clientes_dedicados, text='Clientes Dedicados 24h')
        self.notebook.add(self.frame_expediente, text='Expediente 6h')
        self.notebook.add(self.frame_consulta_publica, text='Consulta Pública')

        self.exibir_geral24h()
        self.exibir_clientes_dedicados()
        self.exibir_expediente()
        self.exibir_consulta_publica()

    def exibir_geral24h(self):
        try:
            resultados = query_geral24h()
            self.criar_tabela(self.frame_geral24h, resultados)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao obter dados: {e}")

    def exibir_clientes_dedicados(self):
        try:
            resultados = query_clientes_dedicados_24h(self.dedicated_urs)
            self.criar_tabela(self.frame_clientes_dedicados, resultados)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao obter dados: {e}")

    def exibir_expediente(self):
        try:
            resultados = query_expediente_6h()
            self.criar_tabela(self.frame_expediente, resultados)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao obter dados: {e}")

    def exibir_consulta_publica(self):
        # Frame para os controles
        controls_frame = ttk.Frame(self.frame_consulta_publica)
        controls_frame.pack(pady=10)

        ttk.Label(controls_frame, text="Selecione o intervalo de tempo:").pack(side=tk.LEFT, padx=5)

        self.range_var = tk.StringVar(value='24h')

        range_options = ['24h', '48h', 'semana', 'mes']
        self.range_combo = ttk.Combobox(controls_frame, textvariable=self.range_var, values=range_options, state='readonly')
        self.range_combo.pack(side=tk.LEFT, padx=5)

        btn_atualizar = ttk.Button(controls_frame, text="Atualizar", command=self.atualizar_consulta_publica)
        btn_atualizar.pack(side=tk.LEFT, padx=5)

        # Frame para exibir os resultados
        self.result_frame = ttk.Frame(self.frame_consulta_publica)
        self.result_frame.pack(expand=True, fill='both')

        # Exibir os dados iniciais
        self.atualizar_consulta_publica()

    def atualizar_consulta_publica(self):
        # Limpar o frame de resultados anterior
        for widget in self.result_frame.winfo_children():
            widget.destroy()

        range_value = self.range_var.get()
        dados = obter_dados_api(range_value)

        if dados:
            # Exibir os dados
            lbl_data_criacao = ttk.Label(self.result_frame, text=f"Data de Criação: {dados.get('data_criacao', 'N/A')}")
            lbl_data_criacao.pack(pady=5)

            lbl_percentual = ttk.Label(self.result_frame, text=f"Percentual de Processos Atualizados ({range_value}): {dados.get('percentual_processos_atualizados_24h', 'N/A')}")
            lbl_percentual.pack(pady=5)

            status = dados.get('status', 'OK')
            lbl_status = ttk.Label(self.result_frame, text=f"Status: {status}")
            lbl_status.pack(pady=5)

            if status == 'fudeu':
                lbl_status.config(foreground='red')
            else:
                lbl_status.config(foreground='green')
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

class JanelaSecundaria(tk.Toplevel):
    def __init__(self, master, titulo):
        super().__init__(master)
        self.title(titulo)
        self.geometry("500x400")
        self.resizable(True, True)

        lbl_exemplo = ttk.Label(self, text=f"Bem-vindo à tela de {titulo}")
        lbl_exemplo.pack(pady=20)

class JanelaMonitoramentoAcervo(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Monitoramento Acervo")
        self.geometry("1000x600")
        self.resizable(True, True)

        try:
            connections = get_mongo_client()
            self.mongo_bigtable_analise = connections['mongo_bigtable_analise']
            self.mongo_token_contador_processo = connections['mongo_token_contador_processo']
        except Exception as e:
            messagebox.showerror("Erro de Conexão", f"Não foi possível conectar ao banco de dados: {e}")
            self.destroy()
            return

        self.criar_widgets()

    def criar_widgets(self):
        # Obter os dados do banco de dados
        tabela_tokens = self.obter_tabela_tokens()

        # Preencher a tabela
        self.exibir_tabela(tabela_tokens)

    def obter_tabela_tokens(self):
        # Chama a função existente em TasksApis.py
        tabela_tokens = obter_tabela_tokens()

        # Atualizar os dados de exibição
        self.dados_exibicao = []

        for item in tabela_tokens:
            ur = item.get('ur', '')
            usuario = item.get('usuario', '')
            percentual_token_ativo = item.get('processos_no_acervo_com_token_ativo_percentual', '')
            percentual_atualizados = item.get('processos_no_acervo_atualizados_no_acervo_percentual', '')

            self.dados_exibicao.append({
                'ur': ur,
                'usuario': usuario,
                'percentual_token_ativo': percentual_token_ativo,
                'percentual_atualizados': percentual_atualizados
            })

        return self.dados_exibicao

    def exibir_tabela(self, dados_exibicao):
        # Criar uma tabela para exibir os dados
        colunas = ('ur', 'usuario', 'percentual_token_ativo', 'percentual_atualizados')
        self.tree = ttk.Treeview(self, columns=colunas, show='headings')

        # Scrollbar vertical
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        # Dicionário para armazenar a ordem de classificação de cada coluna
        self.sort_orders = {col: False for col in colunas}

        for coluna in colunas:
            self.tree.heading(coluna, text=coluna.title(), command=lambda _col=coluna: self.sort_by(_col))
            self.tree.column(coluna, width=200)

        # Preencher a tabela
        self.populate_treeview(dados_exibicao)

        self.tree.pack(expand=True, fill='both')

        # Evento ao dar duplo clique em uma linha
        self.tree.bind('<Double-1>', self.on_item_double_clicked)

    def populate_treeview(self, data):
        # Limpa o Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
        # Insere os novos dados
        for item in data:
            valores = (
                item['ur'],
                item['usuario'],
                item['percentual_token_ativo'],
                item['percentual_atualizados']
            )
            self.tree.insert('', tk.END, values=valores)

    def sort_by(self, coluna):
        # Alterna a ordem de classificação
        self.sort_orders[coluna] = not self.sort_orders.get(coluna, False)
        reverse = self.sort_orders[coluna]

        # Ordena os dados
        if coluna == 'percentual_atualizados':
            # Ordenação personalizada para 'percentual atualizado'
            def custom_sort(item):
                valor_str = str(item[coluna]).replace(',', '.')
                try:
                    valor = float(valor_str)
                except ValueError:
                    valor = -1  # Valor padrão para não numéricos

                if valor == 100:
                    grupo = 2
                elif valor == 0:
                    grupo = 3
                else:
                    grupo = 1

                if reverse:
                    # Ordem reversa
                    if grupo == 1:
                        return (grupo, valor)  # Ordena crescentemente dentro do grupo 1
                    else:
                        return (grupo, 0)  # Mantém a ordem dos grupos
                else:
                    # Ordem normal
                    if grupo == 1:
                        return (grupo, -valor)  # Ordena decrescentemente dentro do grupo 1
                    else:
                        return (grupo, 0)  # Mantém a ordem dos grupos

            self.dados_exibicao.sort(key=custom_sort)
        else:
            try:
                # Tenta converter para float para ordenar percentuais ou números
                self.dados_exibicao.sort(key=lambda x: float(str(x[coluna]).replace(',', '.')), reverse=reverse)
            except ValueError:
                # Ordena como string
                self.dados_exibicao.sort(key=lambda x: x[coluna], reverse=reverse)

        # Atualiza o Treeview
        self.populate_treeview(self.dados_exibicao)

    def obter_detalhes_ur(self, ur):
        detalhes = obter_detalhes_ur_mongo(ur)
        return detalhes

    def on_item_double_clicked(self, event):
        selected_item = self.tree.identify_row(event.y)
        if selected_item:
            item_data = self.tree.item(selected_item)
            ur = item_data['values'][0]  # A UR está na primeira coluna

            # Obter detalhes da UR
            detalhes = self.obter_detalhes_ur(ur)

            if detalhes is None:
                messagebox.showerror("Erro", f"Não foi possível obter detalhes para a UR {ur}.")
                return

            if not detalhes:
                messagebox.showinfo("Informação", f"Nenhum processo encontrado para a UR {ur}.")
                return

            # Criar uma nova janela para exibir os processos (acervos)
            janela_processos = JanelaDetalhesUR(self, ur, detalhes)

class JanelaDetalhesUR(tk.Toplevel):
    def __init__(self, master, ur, detalhes):
        super().__init__(master)
        self.title(f"Processos da UR {ur}")
        self.geometry("800x600")
        self.resizable(True, True)

        self.ur = ur  # Armazenar o UR
        self.detalhes = detalhes
        self.sort_orders = {}  # Dicionário para armazenar a ordem de classificação
        self.create_widgets()

    def create_widgets(self):
        # Frame para os botões no topo
        frame_botoes = ttk.Frame(self)
        frame_botoes.pack(fill='x')

        btn_atualizar = ttk.Button(frame_botoes, text="Atualizar", command=self.atualizar_detalhes)
        btn_atualizar.pack(side='left', padx=5, pady=5)

        # Dicionário para armazenar as barras de progresso por token_id
        self.progress_bars = {}

        # Frame para as barras de progresso
        self.frame_progress = ttk.Frame(self)
        self.frame_progress.pack(fill='x', padx=5, pady=5)

        # Criar um Treeview para exibir os processos
        colunas = ('numero', 'token_id', 'tipo', 'tribunal', 'drive', 'resultado')
        self.tree = ttk.Treeview(self, columns=colunas, show='headings')

        # Scrollbar vertical
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        # Inicializar o dicionário de ordens de classificação
        self.sort_orders = {col: False for col in colunas}

        for coluna in colunas:
            self.tree.heading(coluna, text=coluna.title(), command=lambda _col=coluna: self.sort_by(_col))
            self.tree.column(coluna, width=150)

        # Preencher a tabela com os dados dos processos
        self.populate_treeview(self.detalhes)

        self.tree.pack(expand=True, fill='both')

        # Evento ao clicar com o botão direito
        self.tree.bind('<Button-3>', self.on_right_click)

    def atualizar_detalhes(self):
        # Exibir uma mensagem de carregamento (opcional)
        self.title(f"Processos da UR {self.ur} - Atualizando...")
        self.update_idletasks()

        # Re-obter os detalhes da UR
        try:
            novos_detalhes = obter_detalhes_ur_mongo(self.ur)
            if novos_detalhes is None:
                messagebox.showerror("Erro", f"Não foi possível obter detalhes para a UR {self.ur}.")
                return

            self.detalhes = novos_detalhes

            # Atualizar a tabela
            self.populate_treeview(self.detalhes)

            # Restaurar o título original
            self.title(f"Processos da UR {self.ur}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao atualizar os detalhes: {e}")
            self.title(f"Processos da UR {self.ur}")

    def populate_treeview(self, data):
        # Limpa o Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
        # Insere os novos dados
        for processo in data:
            numero = processo.get('numero', '')
            token_id = processo.get('token_id', '')
            tipo = processo.get('tipo', '')
            tribunal = processo.get('tribunal', '')
            drive = processo.get('drive', '')
            resultado = processo.get('resultado', '')  # Usar o valor armazenado em self.detalhes

            self.tree.insert('', tk.END, values=(numero, token_id, tipo, tribunal, drive, resultado))

    def sort_by(self, coluna):
        # Alterna a ordem de classificação
        self.sort_orders[coluna] = not self.sort_orders[coluna]
        reverse = self.sort_orders[coluna]

        # Ordena os dados
        try:
            # Tenta converter para valores numéricos (se aplicável)
            if coluna in ['numero', 'token_id']:
                # Remover possíveis caracteres não numéricos
                self.detalhes.sort(key=lambda x: int(''.join(filter(str.isdigit, str(x.get(coluna, '')))) or 0), reverse=reverse)
            else:
                self.detalhes.sort(key=lambda x: x.get(coluna, '').lower(), reverse=reverse)
        except ValueError:
            # Ordena como string se não puder converter
            self.detalhes.sort(key=lambda x: x.get(coluna, '').lower(), reverse=reverse)

        # Atualiza o Treeview
        self.populate_treeview(self.detalhes)

    def on_right_click(self, event):
        # Identificar a linha clicada
        row_id = self.tree.identify_row(event.y)
        if row_id:
            # Seleciona o item
            self.tree.selection_set(row_id)
            # Cria o menu de contexto
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="Chamar Logins", command=lambda: self.chamar_logins(row_id))
            # Exibe o menu de contexto
            menu.post(event.x_root, event.y_root)

    def chamar_logins(self, row_id):
        # Obter os valores da linha selecionada
        item = self.tree.item(row_id)
        values = item['values']
        token_id = values[1]  # token_id está na segunda coluna

        # Chamar executar_logins com token_id
        self.executar_logins(token_id, None)

    def update_resultado(self, row_id, token_id, text):
        # Atualizar na interface
        self.tree.set(row_id, column='resultado', value=text)
        # Atualizar em self.detalhes
        for processo in self.detalhes:
            if processo['token_id'] == token_id and self.tree.item(row_id)['values'][0] == processo['numero']:
                processo['resultado'] = text
                break

    def update_resultado_por_numero(self, numero_processo, token_id, text):
        for item_id in self.tree.get_children():
            item = self.tree.item(item_id)
            values = item['values']
            if values[0] == numero_processo and values[1] == token_id:
                self.update_resultado(item_id, token_id, text)
                break

    def executar_logins(self, token_id, _):
        def run():
            try:
                # Caminho para o executável
                executable_path = r"C:\Users\AndreAzevedo\Source\Repos\ProcessoAgil\ProcessoAgil.Logins\bin\Debug\ProcessoAgil.Logins.exe"

                # Diretório de trabalho
                working_dir = r"C:\Users\AndreAzevedo\Source\Repos\ProcessoAgil\ProcessoAgil.Logins\bin\Debug"

                # Monta o comando
                comando = [executable_path, "-id", token_id, "--rodar"]

                # Obter a lista de processos atrasados associados ao token_id
                processos_atrasados = [proc for proc in self.detalhes if proc['token_id'] == token_id]
                total_processos_atrasados = len(processos_atrasados)
                numeros_processos_atrasados = set(proc['numero'] for proc in processos_atrasados)

                # Função para inicializar a barra de progresso
                def init_progress_bar():
                    if token_id not in self.progress_bars:
                        progress_bar = ttk.Progressbar(self.frame_progress, maximum=total_processos_atrasados)
                        label = ttk.Label(self.frame_progress, text=f"Token ID: {token_id}")
                        label.pack(fill='x', padx=5)
                        progress_bar.pack(fill='x', padx=5, pady=2)
                        self.progress_bars[token_id] = progress_bar
                    else:
                        progress_bar = self.progress_bars[token_id]
                        progress_bar['value'] = 0  # Resetar a barra

                self.tree.after(0, init_progress_bar)

                # Atualiza o campo 'resultado' para 'Processando' para todos os processos atrasados com o mesmo token_id
                def update_processando():
                    for item_id in self.tree.get_children():
                        item = self.tree.item(item_id)
                        values = item['values']
                        if values[1] == token_id and values[0] in numeros_processos_atrasados:
                            self.update_resultado(item_id, token_id, 'Processando')

                self.tree.after(0, update_processando)

                # Conjunto para rastrear processos atrasados já atualizados
                processos_atualizados = set()

                # Inicia o processo usando Popen
                process = subprocess.Popen(
                    comando,
                    cwd=working_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )

                # Lê a saída em tempo real
                for line in process.stdout:
                    print(line, end='')  # Imprime a saída no console
                    line = line.strip()
                    # Processar a linha imediatamente
                    self.processar_linha_log(line, token_id, processos_atualizados, numeros_processos_atrasados, process)
                    self.tree.update_idletasks()  # Atualizar a interface gráfica

                # Aguarda o processo terminar
                process.wait()

            except Exception as e:
                # Atualizar o campo 'resultado' na linha correspondente
                def update_erro():
                    for item_id in self.tree.get_children():
                        item = self.tree.item(item_id)
                        values = item['values']
                        if values[1] == token_id:
                            self.update_resultado(item_id, token_id, 'Erro')

                self.tree.after(0, update_erro)
                messagebox.showerror("Erro", f"Erro ao executar o Logins: {e}")

        # Iniciar a thread para não bloquear a interface
        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()

    def processar_linha_log(self, line, token_id, processos_atualizados, numeros_processos_atrasados, process):
        # Verifica se a linha indica sucesso no processamento
        match_sucesso = re.search(r'advogado\s+([\d.-]+)\s+>>\s+Processo com', line)
        if match_sucesso:
            numero_processo = match_sucesso.group(1)
            def update():
                if numero_processo in numeros_processos_atrasados and numero_processo not in processos_atualizados:
                    self.update_resultado_por_numero(numero_processo, token_id, 'OK')
                    processos_atualizados.add(numero_processo)
                    self.atualizar_progress_bar(token_id, len(processos_atualizados))
                    # Verifica se todos os processos atrasados foram atualizados
                    if len(processos_atualizados) == len(numeros_processos_atrasados):
                        # Remover a barra de progresso
                        self.remover_progress_bar(token_id)
            self.tree.after(0, update)
            return

        # Verifica se a linha indica erro no processamento
        match_erro_processo = re.search(r'advogado\s+([\d.-]+)\s+>>\s+(.*)', line)
        if match_erro_processo:
            numero_processo = match_erro_processo.group(1)
            mensagem_erro = match_erro_processo.group(2)
            def update():
                if numero_processo in numeros_processos_atrasados and numero_processo not in processos_atualizados:
                    self.update_resultado_por_numero(numero_processo, token_id, mensagem_erro)
                    processos_atualizados.add(numero_processo)
                    self.atualizar_progress_bar(token_id, len(processos_atualizados))
            self.tree.after(0, update)
            return

        # Verifica se a linha indica erro geral (sem número de processo)
        match_erro_geral = re.search(r'^.*Erro no acesso:\s+(.*)$', line)
        if match_erro_geral:
            mensagem_erro = match_erro_geral.group(1)
            def update():
                for processo in self.detalhes:
                    numero_processo = processo['numero']
                    if processo['token_id'] == token_id and numero_processo in numeros_processos_atrasados and numero_processo not in processos_atualizados:
                        self.update_resultado_por_numero(processo['numero'], token_id, mensagem_erro)
                        processos_atualizados.add(processo['numero'])
                        self.atualizar_progress_bar(token_id, len(processos_atualizados))
                # Verifica se todos os processos atrasados foram atualizados
                if len(processos_atualizados) == len(numeros_processos_atrasados):
                    self.encerrar_processamento(token_id, process)
            self.tree.after(0, update)
            return

    def atualizar_progress_bar(self, token_id, valor):
        progress_bar = self.progress_bars.get(token_id)
        if progress_bar:
            progress_bar['value'] = valor

    def remover_progress_bar(self, token_id):
        progress_bar = self.progress_bars.get(token_id)
        if progress_bar:
            progress_bar.destroy()
            # Remover o label associado
            for widget in self.frame_progress.winfo_children():
                if isinstance(widget, ttk.Label) and widget.cget("text") == f"Token ID: {token_id}":
                    widget.destroy()
                    break
            del self.progress_bars[token_id]



if __name__ == "__main__":
    app = Aplicacao()
    app.mainloop()

# monitoramento_acervo.py
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import subprocess
import re

class JanelaMonitoramentoAcervo(tk.Toplevel):
    def __init__(self, master, model, controller):
        super().__init__(master)
        self.title("Monitoramento Acervo")
        self.geometry("1000x600")
        self.resizable(True, True)
        self.model = model
        self.controller = controller

        self.create_widgets()

    def create_widgets(self):
        tabela_tokens = self.model.get_tabela_tokens()
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

        self.exibir_tabela()

    def exibir_tabela(self):
        colunas = ('ur', 'usuario', 'percentual_token_ativo', 'percentual_atualizados')
        self.tree = ttk.Treeview(self, columns=colunas, show='headings')

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        self.sort_orders = {col: False for col in colunas}

        for coluna in colunas:
            self.tree.heading(coluna, text=coluna.title(), command=lambda _col=coluna: self.sort_by(_col))
            self.tree.column(coluna, width=200)

        self.populate_treeview()
        self.tree.pack(expand=True, fill='both')
        self.tree.bind('<Double-1>', self.on_item_double_clicked)
        self.tree.bind('<Button-3>', self.on_right_click)

    def on_right_click(self, event):
        row_id = self.tree.identify_row(event.y)
        if row_id:
            self.tree.selection_set(row_id)
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="Copiar UR", command=lambda: self.copiar_ur(row_id))
            menu.add_command(label="Adicionar UR à Fila", command=lambda: self.adicionar_ur_a_fila(row_id))
            menu.post(event.x_root, event.y_root)

    def copiar_ur(self, row_id):
        item = self.tree.item(row_id)
        ur = item['values'][0]  # UR está na primeira coluna
        self.clipboard_clear()
        self.clipboard_append(ur)
        messagebox.showinfo("Copiado", f"UR '{ur}' copiada para a área de transferência.")

    def adicionar_ur_a_fila(self, row_id):
        item = self.tree.item(row_id)
        ur = item['values'][0]
        detalhes = self.model.get_detalhes_ur(ur)

        if detalhes is None:
            messagebox.showerror("Erro", f"Não foi possível obter detalhes para a UR {ur}.")
            return

        if not detalhes:
            messagebox.showinfo("Informação", f"Nenhum processo encontrado para a UR {ur}.")
            return

        # Filtrar processos pendentes associados aos tokens do tipo 'a1x' ou 'login'
        processos_pendentes = [
            proc for proc in detalhes
            if proc.get('tipo') in ['a1x', 'login'] and not proc.get('status') == 'Concluído'
        ]

        # Adicionar os processos à fila
        for processo in processos_pendentes:
            processo['tribunal'] = processo['tribunal'].strip().lower()  # Normalizar o tribunal
            self.controller.fila_processos.adicionar_processo(processo)

        messagebox.showinfo("Fila", f"{len(processos_pendentes)} processos adicionados à fila para a UR '{ur}'.")

    def populate_treeview(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for item in self.dados_exibicao:
            valores = (
                item['ur'],
                item['usuario'],
                item['percentual_token_ativo'],
                item['percentual_atualizados']
            )
            self.tree.insert('', tk.END, values=valores)

    def sort_by(self, coluna):
        self.sort_orders[coluna] = not self.sort_orders.get(coluna, False)
        reverse = self.sort_orders[coluna]

        if coluna in ['percentual_atualizados', 'percentual_token_ativo']:
            def custom_sort(item):
                valor_str = str(item[coluna]).replace(',', '.')
                try:
                    valor = float(valor_str)
                except ValueError:
                    valor = -1

                if valor == 100:
                    grupo = 2
                elif valor == 0:
                    grupo = 3
                else:
                    grupo = 1

                if reverse:
                    if grupo == 1:
                        return (grupo, valor)
                    else:
                        return (grupo, 0)
                else:
                    if grupo == 1:
                        return (grupo, -valor)
                    else:
                        return (grupo, 0)

            self.dados_exibicao.sort(key=custom_sort)
        else:
            self.dados_exibicao.sort(key=lambda x: x[coluna], reverse=reverse)

        self.populate_treeview()

    def on_item_double_clicked(self, event):
        selected_item = self.tree.identify_row(event.y)
        if selected_item:
            item_data = self.tree.item(selected_item)
            ur = item_data['values'][0]
            usuario = item_data['values'][1]
            detalhes = self.model.get_detalhes_ur(ur)

            if detalhes is None:
                messagebox.showerror("Erro", f"Não foi possível obter detalhes para a UR {ur}.")
                return

            if not detalhes:
                messagebox.showinfo("Informação", f"Nenhum processo encontrado para a UR {ur}.")
                return

            JanelaDetalhesUR(self, ur, usuario, detalhes, self.controller)


class JanelaDetalhesUR(tk.Toplevel):
    def __init__(self, master, ur, usuario, detalhes, controller):
        super().__init__(master)
        self.title(f"Processos do usuário {usuario}")
        self.geometry("800x600")
        self.resizable(True, True)
        self.controller = controller

        self.ur = ur
        self.usuario = usuario
        self.detalhes = detalhes
        self.sort_orders = {}
        self.create_widgets()

        # Mapeamento de (numero_processo, token_id) para tribunal
        self.mapeamento_processo_tribunal = {
            (proc['numero'], proc['token_id']): proc['tribunal']
            for proc in self.detalhes
        }

    def create_widgets(self):
        frame_botoes = ttk.Frame(self)
        frame_botoes.pack(fill='x')

        btn_atualizar = ttk.Button(frame_botoes, text="Atualizar", command=self.atualizar_detalhes)
        btn_atualizar.pack(side='left', padx=5, pady=5)

        self.progress_bars = {}
        self.frame_progress = ttk.Frame(self)
        self.frame_progress.pack(fill='x', padx=5, pady=5)

        colunas = ('numero', 'token_id', 'tipo', 'tribunal', 'drive', 'resultado')
        self.tree = ttk.Treeview(self, columns=colunas, show='headings')

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        self.sort_orders = {col: False for col in colunas}

        for coluna in colunas:
            self.tree.heading(coluna, text=coluna.title(), command=lambda _col=coluna: self.sort_by(_col))
            self.tree.column(coluna, width=150)

        self.populate_treeview()
        self.tree.pack(expand=True, fill='both')
        self.tree.bind('<Button-3>', self.on_right_click)

    def atualizar_detalhes(self):
        self.title(f"Processos da UR {self.ur} - Atualizando...")
        self.update_idletasks()

        try:
            novos_detalhes = self.master.model.get_detalhes_ur(self.ur)
            if novos_detalhes is None:
                messagebox.showerror("Erro", f"Não foi possível obter detalhes para a UR {self.ur}.")
                return

            self.detalhes = novos_detalhes
            self.populate_treeview()
            self.title(f"Processos da UR {self.ur}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao atualizar os detalhes: {e}")
            self.title(f"Processos da UR {self.ur}")

    def populate_treeview(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for processo in self.detalhes:
            valores = (
                processo.get('numero', ''),
                processo.get('token_id', ''),
                processo.get('tipo', ''),
                processo.get('tribunal', ''),
                processo.get('drive', ''),
                processo.get('resultado', '')
            )
            self.tree.insert('', tk.END, values=valores)

    def sort_by(self, coluna):
        self.sort_orders[coluna] = not self.sort_orders.get(coluna, False)
        reverse = self.sort_orders[coluna]

        try:
            if coluna in ['numero', 'token_id']:
                self.detalhes.sort(key=lambda x: int(''.join(filter(str.isdigit, str(x.get(coluna, '')))) or 0), reverse=reverse)
            else:
                self.detalhes.sort(key=lambda x: x.get(coluna, '').lower(), reverse=reverse)
        except ValueError:
            self.detalhes.sort(key=lambda x: x.get(coluna, '').lower(), reverse=reverse)

        self.populate_treeview()

    def on_right_click(self, event):
        row_id = self.tree.identify_row(event.y)
        if row_id:
            self.tree.selection_set(row_id)
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="Chamar Logins", command=lambda: self.chamar_logins(row_id))
            menu.add_separator()
            menu.add_command(label="Copiar Número do Processo", command=lambda: self.copiar_numero_processo(row_id))
            menu.add_command(label="Copiar Token ID", command=lambda: self.copiar_token_id(row_id))
            menu.add_command(label="Adicionar Token à Fila", command=lambda: self.adicionar_token_a_fila(row_id))
            menu.post(event.x_root, event.y_root)

    def chamar_logins(self, row_id):
        item = self.tree.item(row_id)
        values = item['values']
        token_id = values[1]
        self.executar_logins(token_id)

    def copiar_numero_processo(self, row_id):
        item = self.tree.item(row_id)
        numero_processo = item['values'][0]  # Número do processo está na primeira coluna
        self.clipboard_clear()
        self.clipboard_append(numero_processo)
        messagebox.showinfo("Copiado", f"Número do processo '{numero_processo}' copiado para a área de transferência.")


    def copiar_token_id(self, row_id):
        item = self.tree.item(row_id)
        values = item['values']
        token_id = values[1]
        tipo = values[2]
        tribunal = values[3].strip().lower()  # Normalizar o nome do tribunal

        # Filtrar apenas tokens do tipo 'a1x' ou 'login'
        if tipo not in ['a1x', 'login']:
            messagebox.showinfo("Aviso", f"Tipo de token '{tipo}' não é suportado.")
            return

        # Obter todos os processos pendentes associados a este token
        processos_pendentes = [proc for proc in self.detalhes if proc['token_id'] == token_id]

        # Verificar se já existem processos deste token na fila
        processos_existentes = [proc for proc in self.controller.fila_processos.obter_fila() if proc['token_id'] == token_id]
        numeros_existentes = set(proc['numero'] for proc in processos_existentes)

        novos_processos = [proc for proc in processos_pendentes if proc['numero'] not in numeros_existentes]

        if novos_processos:
            # Adicionar os novos processos à fila
            for processo in novos_processos:
                processo['tribunal'] = tribunal  # Assegurar que o tribunal está normalizado
                self.controller.fila_processos.adicionar_processo(processo)
            messagebox.showinfo("Fila", f"Novos processos adicionados para o token '{token_id}'.")
        else:
            messagebox.showinfo("Fila", f"Não há novos processos para o token '{token_id}'.")

    def executar_logins(self, token_id):
        def run():
            try:
                executable_path = r"C:\Users\AndreAzevedo\Source\Repos\ProcessoAgil\ProcessoAgil.Logins\bin\Debug\ProcessoAgil.Logins.exe"
                working_dir = r"C:\Users\AndreAzevedo\Source\Repos\ProcessoAgil\ProcessoAgil.Logins\bin\Debug"

                comando = [executable_path, "-id", token_id, "--rodar"]

                processos_atrasados = [proc for proc in self.detalhes if proc['token_id'] == token_id]
                total_processos_atrasados = len(processos_atrasados)
                numeros_processos_atrasados = set(proc['numero'] for proc in processos_atrasados)

                # Atualize processos_atualizados
                processos_atualizados = set()

                self.init_progress_bar(token_id, total_processos_atrasados)

                self.update_processando(token_id, numeros_processos_atrasados)

                processos_atualizados = set()

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
                    self.processar_linha_log(line, token_id, processos_atualizados, numeros_processos_atrasados)
                    self.tree.update_idletasks()

                process.wait()

            except Exception as e:
                self.update_erro(token_id)
                messagebox.showerror("Erro", f"Erro ao executar o Logins: {e}")

        threading.Thread(target=run, daemon=True).start()

    def init_progress_bar(self, token_id, total):
        def init_bar():
            if token_id not in self.progress_bars:
                progress_bar = ttk.Progressbar(self.frame_progress, maximum=total)
                label = ttk.Label(self.frame_progress, text=f"Token ID: {token_id}")
                label.pack(fill='x', padx=5)
                progress_bar.pack(fill='x', padx=5, pady=2)
                self.progress_bars[token_id] = progress_bar
            else:
                self.progress_bars[token_id]['value'] = 0

        self.tree.after(0, init_bar)

    def update_processando(self, token_id, numeros_processos_atrasados):
        def update():
            for item_id in self.tree.get_children():
                item = self.tree.item(item_id)
                values = item['values']
                if values[1] == token_id and values[0] in numeros_processos_atrasados:
                    self.tree.set(item_id, column='resultado', value='Processando')

        self.tree.after(0, update)

    def processar_linha_log(self, line, token_id, processos_atualizados, numeros_processos_atrasados):
        match_sucesso = re.search(r'advogado\s+([\d.-]+)\s+>>\s+Processo com', line)
        match_erro_processo = re.search(r'advogado\s+([\d.-]+)\s+>>\s+(.*)', line)
        match_erro_geral = re.search(r'^.*Erro no acesso:\s+(.*)$', line)

        if match_sucesso:
            numero_processo = match_sucesso.group(1)
            tribunal = self.mapeamento_processo_tribunal.get((numero_processo, token_id))
            mensagem = 'OK'
            self.atualizar_processo(numero_processo, token_id, tribunal, mensagem, processos_atualizados, numeros_processos_atrasados)
        elif match_erro_processo:
            numero_processo = match_erro_processo.group(1)
            tribunal = self.mapeamento_processo_tribunal.get((numero_processo, token_id))
            mensagem = match_erro_processo.group(2)
            self.atualizar_processo(numero_processo, token_id, tribunal, mensagem, processos_atualizados, numeros_processos_atrasados)
        elif match_erro_geral:
            mensagem = match_erro_geral.group(1)
            for processo in self.detalhes:
                numero_processo = processo['numero']
                tribunal = processo['tribunal']
                if processo['token_id'] == token_id:
                    self.atualizar_processo(numero_processo, token_id, tribunal, mensagem, processos_atualizados, numeros_processos_atrasados)

    def update_resultado(self, item_id, token_id, tribunal, text):
        self.tree.set(item_id, column='resultado', value=text)
        for processo in self.detalhes:
            if (processo['token_id'] == token_id and
                processo['tribunal'] == tribunal and
                self.tree.item(item_id)['values'][0] == processo['numero']):
                processo['resultado'] = text
                break

    def update_resultado_por_numero_tribunal(self, numero_processo, token_id, tribunal, text):
        for item_id in self.tree.get_children():
            item = self.tree.item(item_id)
            values = item['values']
            if (values[0] == numero_processo and
                values[1] == token_id and
                values[3] == tribunal):
                self.update_resultado(item_id, token_id, tribunal, text)
                break

    def atualizar_processo(self, numero_processo, token_id, tribunal, mensagem, processos_atualizados, numeros_processos_atrasados):
        chave_processo = (numero_processo, tribunal)
        if chave_processo in numeros_processos_atrasados and chave_processo not in processos_atualizados:
            def update():
                self.update_resultado_por_numero_tribunal(numero_processo, token_id, tribunal, mensagem)
                processos_atualizados.add(chave_processo)
                self.atualizar_progress_bar(token_id, len(processos_atualizados))
                if len(processos_atualizados) == len(numeros_processos_atrasados):
                    self.remover_progress_bar(token_id)
            self.tree.after(0, update)

    def atualizar_progress_bar(self, token_id, valor):
        progress_bar = self.progress_bars.get(token_id)
        if progress_bar:
            progress_bar['value'] = valor

    def remover_progress_bar(self, token_id):
        progress_bar = self.progress_bars.get(token_id)
        if progress_bar:
            progress_bar.destroy()
            for widget in self.frame_progress.winfo_children():
                if isinstance(widget, ttk.Label) and widget.cget("text") == f"Token ID: {token_id}":
                    widget.destroy()
                    break
            del self.progress_bars[token_id]

    def update_erro(self, token_id):
        def update():
            for item_id in self.tree.get_children():
                item = self.tree.item(item_id)
                values = item['values']
                if values[1] == token_id:
                    self.tree.set(item_id, column='resultado', value='Erro')
        self.tree.after(0, update)


class FilaProcessos:
    def __init__(self):
        self.fila = []  # Lista de dicionários com informações dos processos
        self.callbacks = []  # Lista de funções de callback

    def adicionar_processo(self, processo):
        # Verificar se o processo já está na fila
        if not any(p['numero'] == processo['numero'] and p['token_id'] == processo['token_id'] for p in self.fila):
            self.fila.append(processo)
            print(f"Processo adicionado: {processo}")
            print(f"Fila atual: {self.fila}")
            self.notificar_observadores()
        else:
            print(f"Processo {processo['numero']} já está na fila.")

    def remover_processo(self, processo):
        self.fila.remove(processo)
        self.notificar_observadores()

    def obter_fila(self):
        return self.fila

    def limpar_fila(self):
        self.fila.clear()
        self.notificar_observadores()

    def registrar_observador(self, callback):
        if callback not in self.callbacks:
            self.callbacks.append(callback)

    def remover_observador(self, callback):
        if callback in self.callbacks:
            self.callbacks.remove(callback)

    def notificar_observadores(self):
        for callback in self.callbacks:
            callback()
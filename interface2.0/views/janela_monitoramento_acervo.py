# views/janela_monitoramento_acervo.py

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from views.base_treeview import BaseTreeview
from views.janela_detalhes_ur import JanelaDetalhesUR

class JanelaMonitoramentoAcervo(ttk.Frame):  # Alterado para herdar de ttk.Frame
    def __init__(self, master, model, controller, notebook_acervo):
        super().__init__(master)
        self.model = model  # self.model é um dicionário
        self.controller = controller
        self.notebook_acervo = notebook_acervo  # Armazenamos o notebook_acervo
        self.create_widgets()

    def create_widgets(self):
        colunas = ('ur', 'usuario', 'percentual_token_ativo', 'percentual_atualizados')
        self.treeview_frame = BaseTreeview(self, colunas)
        self.treeview_frame.pack(expand=True, fill='both')
        self.pack(expand=True, fill='both')  # Certifique-se de que o frame principal também está sendo expandido

        # Vincular eventos
        self.treeview_frame.tree.bind('<Double-1>', self.on_item_double_clicked)
        self.treeview_frame.tree.bind('<Button-3>', self.on_right_click)

        # Iniciar a obtenção de dados em uma thread separada
        threading.Thread(target=self.obter_dados_thread).start()

    def obter_dados_thread(self):
        print("Iniciando obtenção de dados...")
        try:
            tabela_tokens = self.model['mongodb'].get_tabela_tokens()
            print(f"Quantidade de tokens obtidos: {len(tabela_tokens)}")
            data = []

            for idx, item in enumerate(tabela_tokens):
                ur = item.get('ur', '')
                usuario = item.get('usuario', '')
                percentual_token_ativo = item.get('processos_no_acervo_com_token_ativo_percentual', '')
                percentual_atualizados = item.get('processos_no_acervo_atualizados_no_acervo_percentual', '')

                data.append({
                    'ur': ur,
                    'usuario': usuario,
                    'percentual_token_ativo': percentual_token_ativo,
                    'percentual_atualizados': percentual_atualizados
                })

                if idx >= 99:  # Limitar a 100 registros
                    break

            print(f"Quantidade de registros processados: {len(data)}")
            # Agendar a atualização da UI na thread principal
            self.after(0, self.update_treeview_data, data)
        except Exception as e:
            print(f"Erro ao obter dados: {e}")
            self.after(0, lambda: messagebox.showerror("Erro", f"Erro ao obter dados: {e}"))

    def update_treeview_data(self, data):
        print(f"Chamando update_treeview_data com {len(data)} registros.")
        if not data:
            print("Nenhum dado disponível. Adicionando entrada de teste.")
            data = [{
                'ur': 'Teste UR',
                'usuario': 'Teste Usuário',
                'percentual_token_ativo': '0%',
                'percentual_atualizados': '0%'
            }]
        self.treeview_frame.data = data
        self.treeview_frame.populate_treeview()

    def on_item_double_clicked(self, event):
        selected_item = self.treeview_frame.tree.identify_row(event.y)
        if selected_item:
            item_data = self.treeview_frame.tree.item(selected_item)
            ur = item_data['values'][0]
            usuario = item_data['values'][1]

            # Iniciar a obtenção dos detalhes em uma thread separada
            threading.Thread(target=self.get_detalhes_ur_thread, args=(ur, usuario)).start()

    def get_detalhes_ur_thread(self, ur, usuario):
        detalhes = self.model['mongodb'].get_detalhes_ur(ur)

        if detalhes is None:
            # Agendar a exibição da mensagem de erro na thread principal
            self.after(0, lambda: messagebox.showerror("Erro", f"Não foi possível obter detalhes para a UR {ur}."))
            return

        if not detalhes:
            # Agendar a exibição da mensagem informativa na thread principal
            self.after(0, lambda: messagebox.showinfo("Informação", f"Nenhum processo encontrado para a UR {ur}."))
            return

        # Abrir a janela de detalhes na thread principal
        self.after(0, self.open_detalhes_ur_tab, ur, usuario, detalhes)

    def open_detalhes_ur_tab(self, ur, usuario, detalhes):
        # Criar um novo frame para a aba
        detalhes_frame = JanelaDetalhesUR(self.notebook_acervo, ur, usuario, detalhes, self.controller, self.model, self.notebook_acervo)
        # Adicionar a nova aba ao notebook
        self.notebook_acervo.add(detalhes_frame, text=f"UR {ur}")
        self.notebook_acervo.select(detalhes_frame)

    def on_right_click(self, event):
        row_id = self.treeview_frame.tree.identify_row(event.y)
        if row_id:
            self.treeview_frame.tree.selection_set(row_id)
            menu = tk.Menu(self.treeview_frame.tree, tearoff=0)
            menu.add_command(label="Copiar UR", command=lambda: self.copiar_ur(row_id))
            menu.add_command(label="Adicionar UR à Fila", command=lambda: self.adicionar_ur_a_fila(row_id))
            menu.post(event.x_root, event.y_root)


    def copiar_ur(self, row_id):
        item = self.treeview_frame.tree.item(row_id)
        ur = item['values'][0]
        self.clipboard_clear()
        self.clipboard_append(ur)
        messagebox.showinfo("Copiado", f"UR '{ur}' copiada para a área de transferência.")

    def adicionar_ur_a_fila(self, row_id):
        item = self.treeview_frame.tree.item(row_id)
        ur = item['values'][0]
        detalhes = self.model['mongodb'].get_detalhes_ur(ur)

        if detalhes is None:
            messagebox.showerror("Erro", f"Não foi possível obter detalhes para a UR {ur}.")
            return

        if not detalhes:
            messagebox.showinfo("Informação", f"Nenhum processo encontrado para a UR {ur}.")
            return

        # Filtrar processos pendentes associados aos tokens do tipo 'a1x' ou 'login'
        processos_pendentes = [
            proc for proc in detalhes
            if proc.get('tipo') in ['a1x', 'login'] and proc.get('status') != 'Concluído'
        ]

        # Adicionar os processos à fila
        for processo in processos_pendentes:
            processo['tribunal'] = processo['tribunal'].strip().lower()  # Normalizar o tribunal
            self.controller.fila_processos.adicionar_processo(processo)

        messagebox.showinfo("Fila", f"{len(processos_pendentes)} processos adicionados à fila para a UR '{ur}'.")


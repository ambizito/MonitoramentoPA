# views/janela_detalhes_ur.py

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from views.base_treeview import BaseTreeview

class JanelaDetalhesUR(ttk.Frame):
    def __init__(self, master, ur, usuario, detalhes, controller, model, notebook_acervo):
        super().__init__(master)
        self.ur = ur
        self.usuario = usuario
        self.controller = controller
        self.model = model
        self.notebook_acervo = notebook_acervo
        self.detalhes = detalhes

        self.create_widgets()

    def create_widgets(self):
        frame_botoes = ttk.Frame(self)
        frame_botoes.pack(fill='x')

        btn_atualizar = ttk.Button(frame_botoes, text="Atualizar", command=self.atualizar_detalhes)
        btn_atualizar.pack(side='left', padx=5, pady=5)

        btn_fechar = ttk.Button(frame_botoes, text="Fechar Aba", command=self.fechar_aba)
        btn_fechar.pack(side='left', padx=5, pady=5)

        colunas = ('numero', 'token_id', 'tipo', 'tribunal', 'drive', 'resultado')
        self.treeview_frame = BaseTreeview(self, colunas)
        self.treeview_frame.pack(expand=True, fill='both')

        self.obter_dados()
        self.treeview_frame.populate_treeview()

    def obter_dados(self):
        self.treeview_frame.data = self.detalhes

    def atualizar_detalhes(self):
        threading.Thread(target=self.atualizar_detalhes_thread).start()

    def atualizar_detalhes_thread(self):
        novos_detalhes = self.model['mongodb'].get_detalhes_ur(self.ur)
        if novos_detalhes is None:
            self.after(0, lambda: messagebox.showerror("Erro", f"Não foi possível obter detalhes para a UR {self.ur}."))
            return

        self.detalhes = novos_detalhes
        self.after(0, self.update_treeview_data)

    def update_treeview_data(self, data):
        print(f"Atualizando treeview com {len(data)} registros.")
        self.treeview_frame.data = data
        self.treeview_frame.populate_treeview()

    def fechar_aba(self):
        # Remover a aba atual do notebook
        for tab_id in self.notebook_acervo.tabs():
            if self.notebook_acervo.nametowidget(tab_id) == self:
                self.notebook_acervo.forget(tab_id)
                break

    # Implementar métodos específicos como `chamar_logins`, `copiar_numero_processo`, etc.

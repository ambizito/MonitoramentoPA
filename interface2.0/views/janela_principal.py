# views/janela_principal.py

import tkinter as tk
from tkinter import ttk
from views.janela_monitoramento_rotina import JanelaMonitoramentoRotina
from views.janela_monitoramento_acervo import JanelaMonitoramentoAcervo

class JanelaPrincipal(tk.Tk):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.title("Aplicativo Principal")
        self.geometry("1024x768")
        self.create_widgets()

    def create_widgets(self):
        self.notebook_principal = ttk.Notebook(self)
        self.notebook_principal.pack(expand=True, fill='both')

        # Criar a aba "Rotina"
        frame_rotina = ttk.Frame(self.notebook_principal)
        self.notebook_principal.add(frame_rotina, text="Rotina")

        # Instanciar a JanelaMonitoramentoRotina dentro do frame_rotina
        self.monitoramento_rotina = JanelaMonitoramentoRotina(frame_rotina, self.controller.model)

        # Criar a aba "Acervo"
        frame_acervo = ttk.Frame(self.notebook_principal)
        self.notebook_principal.add(frame_acervo, text='Acervo')

        # Criar um Notebook dentro da aba "Acervo"
        self.notebook_acervo = ttk.Notebook(frame_acervo)
        self.notebook_acervo.pack(expand=True, fill='both')

        # Inicializar o JanelaMonitoramentoAcervo dentro do notebook_acervo
        self.monitoramento_acervo = JanelaMonitoramentoAcervo(self.notebook_acervo, self.controller.model, self.controller, self.notebook_acervo)
        self.notebook_acervo.add(self.monitoramento_acervo, text='Monitoramento Acervo')


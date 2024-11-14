# views.py
import tkinter as tk
from tkinter import ttk

class AplicacaoView(tk.Tk):
    def __init__(self, controller):
        super().__init__()
        self.title("Aplicação de Monitoramento")
        self.geometry("400x300")
        self.resizable(True, True)
        self.controller = controller
        self.create_main_buttons()

    def create_main_buttons(self):
        frame_buttons = ttk.Frame(self)
        frame_buttons.pack(expand=True)

        btn_rotina = ttk.Button(
            frame_buttons,
            text="Monitoramento Rotina",
            command=self.controller.open_monitoramento_rotina
        )
        btn_rotina.pack(pady=10)

        btn_pendentes = ttk.Button(
            frame_buttons,
            text="Monitoramento Pendentes",
            command=self.controller.open_monitoramento_pendentes
        )
        btn_pendentes.pack(pady=10)

        btn_acervo = ttk.Button(
            frame_buttons,
            text="Monitoramento Acervo",
            command=self.controller.open_monitoramento_acervo
        )
        btn_acervo.pack(pady=10)
        
        btn_fila = ttk.Button(
            frame_buttons, 
            text="Fila", 
            command=self.controller.open_fila)
        btn_fila.pack(pady=10)
            


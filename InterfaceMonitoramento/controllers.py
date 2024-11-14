# controllers.py
from views import AplicacaoView
from models import DataModel
from telas.monitoramento_rotina import JanelaMonitoramentoRotina
from telas.monitoramento_acervo import JanelaMonitoramentoAcervo
from telas.monitoramento_acervo import FilaProcessos
from telas.janela_fila import JanelaFila
from tkinter import messagebox

class AplicacaoController:
    def __init__(self):
        self.model = DataModel()
        self.view = AplicacaoView(self)
        self.fila_processos = FilaProcessos()

    def run(self):
        self.view.mainloop()

    def open_monitoramento_rotina(self):
        JanelaMonitoramentoRotina(self.view, self.model)

    def open_monitoramento_pendentes(self):
        messagebox.showinfo("Monitoramento Pendentes", "Funcionalidade ainda não implementada.")

    def open_monitoramento_acervo(self):
        JanelaMonitoramentoAcervo(self.view, self.model, self)

    def open_fila(self):
        JanelaFila(self.view, self.model, self)


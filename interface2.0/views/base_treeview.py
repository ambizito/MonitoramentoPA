# views/base_treeview.py

import tkinter as tk
from tkinter import ttk, messagebox

class BaseTreeview(ttk.Frame):
    def __init__(self, master, colunas):
        super().__init__(master)
        self.colunas = colunas
        self.data = []
        self.tree = ttk.Treeview(self, columns=colunas, show='headings')
        for coluna in colunas:
            self.tree.heading(coluna, text=coluna.title())
            self.tree.column(coluna, anchor='center', width=150)  # Ajuste o tamanho e alinhamento das colunas
        self.tree.pack(expand=True, fill='both')

    def create_widgets(self):
        self.tree = ttk.Treeview(self, columns=self.colunas, show='headings')

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        for coluna in self.colunas:
            self.tree.heading(coluna, text=coluna.title(), command=lambda _col=coluna: self.sort_by(_col))
            self.tree.column(coluna, width=150)

        self.tree.pack(expand=True, fill='both')
        self.tree.bind('<Button-3>', self.on_right_click)

    def populate_treeview(self):
        print(f"Populando treeview com {len(self.data)} registros.")
        try:
            # Limpar o treeview existente
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Inserir novos dados
            for idx, row in enumerate(self.data):
                values = [row.get(col, '') for col in self.colunas]
                self.tree.insert('', 'end', values=values)
                
                # Opcional: Limitar o número de registros para teste
                # if idx >= 1000:
                #     break
        except Exception as e:
            print(f"Erro ao popular o treeview: {e}")

    def sort_by(self, coluna):
        self.sort_orders[coluna] = not self.sort_orders.get(coluna, False)
        reverse = self.sort_orders[coluna]
        self.data.sort(key=lambda x: x.get(coluna, ''), reverse=reverse)
        self.populate_treeview()

    def on_right_click(self, event):
        pass  # Será implementado nas classes filhas

    # Métodos auxiliares que podem ser compartilhados
    def copiar_para_clipboard(self, texto):
        self.clipboard_clear()
        self.clipboard_append(texto)
        messagebox.showinfo("Copiado", f"'{texto}' copiado para a área de transferência.")

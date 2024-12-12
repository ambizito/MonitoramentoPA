import tkinter as tk
from tkinter import ttk
from Graficos import carregar_logs, gerar_grafico

def criar_filtros(parent, frame_grafico, df):
    """
    Cria os filtros para alterar dinamicamente o gráfico.

    Args:
        parent (tk.Widget): Widget pai onde os filtros serão exibidos.
        frame_grafico (tk.Widget): Frame onde o gráfico é exibido.
        df (pd.DataFrame): DataFrame com os dados dos logs.
    """
    filtros = ttk.Frame(parent)
    filtros.pack(fill="x", pady=10)

    servidores = df["Servidor"].unique()
    combo_servidor = ttk.Combobox(filtros, values=["Todos"] + list(servidores), state="readonly")
    combo_servidor.set("Todos")
    combo_servidor.pack(side="left", padx=10)

    btn_aplicar = ttk.Button(
        filtros,
        text="Aplicar",
        command=lambda: gerar_grafico(
            frame_grafico, df, None if combo_servidor.get() == "Todos" else combo_servidor.get(), "Servidor"
        )
    )
    btn_aplicar.pack(side="left")

def criar_abas(parent, nomes_abas):
    """
    Cria um Notebook com abas principais.

    Args:
        parent (tk.Widget): Widget pai onde o Notebook será criado.
        nomes_abas (list): Lista com os nomes das abas principais.

    Returns:
        ttk.Notebook: O Notebook criado.
        dict: Dicionário com os frames das abas principais.
    """
    notebook = ttk.Notebook(parent)
    notebook.pack(expand=True, fill='both')

    abas = {}
    for nome in nomes_abas:
        frame = ttk.Frame(notebook)
        notebook.add(frame, text=nome)
        abas[nome] = frame

    return notebook, abas

def adicionar_label(parent, texto, fonte=("Arial", 12)):
    """
    Adiciona um rótulo a uma aba ou frame.

    Args:
        parent (tk.Widget): Widget pai onde o rótulo será adicionado.
        texto (str): Texto do rótulo.
        fonte (tuple): Fonte e tamanho do texto (nome, tamanho).
    """
    label = tk.Label(parent, text=texto, font=fonte)
    label.pack(pady=20)

# Código principal
def main():
    janela = tk.Tk()
    janela.title("Sistema de Monitoramento")
    janela.geometry("800x600")

    nomes_abas = ["Monitoramento Pendente", "Logs", "BigTable", "Atividades de Rotina", "Logs by Server"]
    notebook_principal, abas_principais = criar_abas(janela, nomes_abas)

    caminho_logs = "./Graficos Logs"
    dados = carregar_logs(caminho_logs)

    frame_grafico = ttk.Frame(abas_principais["Logs by Server"])
    frame_grafico.pack(expand=True, fill="both")

    gerar_grafico(frame_grafico, dados)
    criar_filtros(abas_principais["Logs by Server"], frame_grafico, dados)

    janela.mainloop()

if __name__ == "__main__":
    main()
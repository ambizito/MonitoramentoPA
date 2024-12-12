import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def carregar_logs(caminho_logs):
    """
    Carrega e organiza os logs da pasta especificada.

    Args:
        caminho_logs (str): Caminho da pasta que contém os logs organizados por servidor.

    Returns:
        pd.DataFrame: DataFrame contendo os dados dos logs estruturados.
    """
    registros = []
    for servidor in os.listdir(caminho_logs):
        caminho_servidor = os.path.join(caminho_logs, servidor)
        if os.path.isdir(caminho_servidor):
            for arquivo in os.listdir(caminho_servidor):
                if arquivo.endswith(".txt"):
                    caminho_arquivo = os.path.join(caminho_servidor, arquivo)
                    with open(caminho_arquivo, "r", encoding="utf-8") as f:
                        for linha in f:
                            registro = processar_log(linha.strip(), servidor)
                            if registro:
                                registros.append(registro)
    return pd.DataFrame(registros)

def processar_log(linha, servidor):
    """
    Processa uma linha de log e extrai suas informações.

    Args:
        linha (str): Linha de log no formato especificado.
        servidor (str): Nome do servidor de onde veio o log.

    Returns:
        dict: Dicionário contendo os dados estruturados do log.
    """
    try:
        partes = linha.split("_")
        tribunal = partes[1]  # Exemplo: t_401pje1
        sistema = partes[2]  # Exemplo: ur_3A2011D7-FD14-4F56-B1E3-CF2CB7ABB312
        usuario = partes[3]  # Exemplo: usu_1E9F2B18-FDB8-4DEA-BFD0-DE484BA10F8D_a1

        return {
            "Servidor": servidor,
            "Tribunal": tribunal,
            "UR": sistema,
            "Usuário": usuario
        }
    except IndexError:
        return None

def gerar_grafico(parent, df, filtro=None, categoria=None):
    """
    Gera e exibe o gráfico com base no filtro aplicado.

    Args:
        parent (tk.Widget): Widget pai onde o gráfico será exibido.
        df (pd.DataFrame): DataFrame com os dados dos logs.
        filtro (str): Valor para filtrar o DataFrame (opcional).
        categoria (str): Categoria para aplicar o filtro (opcional).
    """
    for widget in parent.winfo_children():
        widget.destroy()

    if filtro and categoria:
        df = df[df[categoria] == filtro]

    agrupado = df.groupby("Servidor").size().sort_values(ascending=False)

    fig, ax = plt.subplots()
    agrupado.plot(kind='bar', ax=ax)
    ax.set_title("Análise de Servidores")
    ax.set_xlabel("Servidor")
    ax.set_ylabel("Frequência")
    ax.set_xticklabels(agrupado.index, rotation=45, ha="right")
    fig.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    canvas.get_tk_widget().pack(expand=True, fill="both")

import os
import re
import pandas as pd
from datetime import datetime
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def load_logs(log_directory="logsgraficos"):
    data = []
    for file_name in os.listdir(log_directory):
        if file_name.endswith(".txt"):
            file_path = os.path.join(log_directory, file_name)
            with open(file_path, 'r', encoding='utf-8') as file:
                current_user = None
                for line in file:
                    if '@' in line and 'em' in line:
                        current_user = parse_login_info(line)
                    else:
                        if current_user:
                            event = parse_log_event(line, current_user)
                            if event:
                                data.append(event)
        else:
            print(f"{file_name} não é um arquivo de log válido (não termina em .txt).")
    return pd.DataFrame(data)

def parse_login_info(line):
    match = re.match(r"(.+?)@.+?@([A-F0-9-]+)@.+ em (\d+\.\d+\.pje\.\d+)", line.strip())
    if match:
        login = match.group(1)
        ur_id = match.group(2)  # Extrai o identificador UR
        sistema_info = match.group(3)
        login_type = "login" if login.isdigit() else "a1x"
        oab_estado, oab_numero = (login[:2], login[2:]) if login_type == "a1x" else (None, None)

        return {
            "login": login,
            "login_type": login_type,
            "oab_estado": oab_estado,
            "oab_numero": oab_numero,
            "sistema_info": sistema_info,
            "ur_id": ur_id  # Adiciona a UR ao dicionário
        }
    return None

def parse_log_event(line, user_info):
    match = re.match(r"(\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}): (.+)", line.strip())
    if match:
        timestamp = datetime.strptime(match.group(1), "%d/%m/%Y %H:%M:%S")
        action = match.group(2)
        event_type = "Acesso" if "Acessou" in action else \
                     "Login" if "Logou" in action else \
                     "Entrou" if "Entrou" in action else \
                     "Total" if "Total" in action else \
                     "Processo Atualizado" if "Processo" in action else \
                     "Outro"
        return {
            **user_info,
            "timestamp": timestamp,
            "event_type": event_type,
            "action": action
        }
    return None


def plot_performance_metrics(activity_df, canvas_frame):
    # Remove gráficos antigos
    for widget in canvas_frame.winfo_children():
        widget.destroy()

    # Configura o gráfico de atividade ao longo do tempo
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(activity_df['time_period'], activity_df['event_count'])
    ax.set_title("Atividade ao Longo do Tempo")
    ax.set_xlabel("Tempo")
    ax.set_ylabel("Contagem de Eventos")

    # Adiciona o gráfico ao Tkinter com FigureCanvasTkAgg
    canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
    canvas.draw()
    canvas.get_tk_widget().pack()

def calculate_performance_metrics(log_df, tribunal_filter=None, ur_filter=None, token_filter=None, event_type_filter=None):
    # Aplica os filtros conforme os parâmetros passados
    if tribunal_filter and tribunal_filter != "Todos":
        log_df = log_df[log_df['sistema_info'].str.contains(tribunal_filter)]
    if ur_filter and ur_filter != "Todos":
        log_df = log_df[log_df['ur_id'] == ur_filter]  # Filtra pela UR correta
    if token_filter and token_filter != "Todos":
        log_df = log_df[log_df['login_type'] == token_filter]
    if event_type_filter and event_type_filter != "Todos":
        log_df = log_df[log_df['event_type'] == event_type_filter]
    
    # Contagem de eventos ao longo do tempo (por minuto)
    log_df['time_period'] = log_df['timestamp'].dt.floor('min')
    events_over_time = log_df.groupby('time_period').size().reset_index(name='event_count')
    
    return events_over_time


# Função para aplicar filtros e atualizar gráficos
def atualizar_graficos():
    tribunal_filter = tribunal_var.get()
    ur_filter = ur_var.get()
    token_filter = token_var.get()
    event_type_filter = event_type_var.get()
    
    activity_df = calculate_performance_metrics(log_df, tribunal_filter, ur_filter, token_filter, event_type_filter)

    plot_performance_metrics( activity_df, canvas_frame)

# Carrega os dados de log
log_df = load_logs("logsgraficos")

# Configuração da Interface com tkinter
root = tk.Tk()
root.title("Filtro de Logs e Visualização")
root.geometry("800x600")

# Carrega as opções de filtros
tribunais_disponiveis = ["Todos"] + sorted(log_df['sistema_info'].unique())
urs_disponiveis = ["Todos"] + sorted(log_df['ur_id'].unique())  # Corrige para usar ur_id
tokens_disponiveis = ["Todos", "login", "a1x"]  # "login" para CPF, "a1x" para OAB
eventos_disponiveis = ["Todos"] + sorted(log_df['event_type'].unique())

# Widgets de Seleção para Filtros
tribunal_var = tk.StringVar(value="Todos")
ur_var = tk.StringVar(value="Todos")
token_var = tk.StringVar(value="Todos")
event_type_var = tk.StringVar(value="Todos")

ttk.Label(root, text="Selecione o Tribunal:").pack(pady=5)
tribunal_menu = ttk.Combobox(root, textvariable=tribunal_var, values=tribunais_disponiveis)
tribunal_menu.pack()

ttk.Label(root, text="Selecione a UR (Sistema):").pack(pady=5)
ur_menu = ttk.Combobox(root, textvariable=ur_var, values=urs_disponiveis)
ur_menu.pack()

ttk.Label(root, text="Selecione o Tipo de Token (CPF/OAB):").pack(pady=5)
token_menu = ttk.Combobox(root, textvariable=token_var, values=tokens_disponiveis)
token_menu.pack()

ttk.Label(root, text="Selecione o Tipo de Evento:").pack(pady=5)
event_type_menu = ttk.Combobox(root, textvariable=event_type_var, values=eventos_disponiveis)
event_type_menu.pack()

# Botão para Atualizar Gráficos
atualizar_button = ttk.Button(root, text="Atualizar Gráficos", command=atualizar_graficos)
atualizar_button.pack(pady=20)

# Frame para o Canvas onde o gráfico será exibido
canvas_frame = tk.Frame(root)
canvas_frame.pack(fill=tk.BOTH, expand=True)

root.mainloop()

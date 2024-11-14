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
        ur_id = match.group(2)
        sistema_info = match.group(3)
        login_type = "login" if login.isdigit() else "a1x"
        oab_estado, oab_numero = (login[:2], login[2:]) if login_type == "a1x" else (None, None)

        return {
            "login": login,
            "login_type": login_type,
            "oab_estado": oab_estado,
            "oab_numero": oab_numero,
            "sistema_info": sistema_info,
            "ur_id": ur_id
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

def calculate_performance_metrics(log_df, tribunal_filter=None, ur_filter=None, token_filter=None, event_type_filter=None, start_datetime=None, end_datetime=None):
    if tribunal_filter and tribunal_filter != "Todos":
        log_df = log_df[log_df['sistema_info'].str.contains(tribunal_filter)]
    if ur_filter and ur_filter != "Todos":
        log_df = log_df[log_df['ur_id'] == ur_filter]
    if token_filter and token_filter != "Todos":
        log_df = log_df[log_df['login_type'] == token_filter]
    if event_type_filter and event_type_filter != "Todos":
        log_df = log_df[log_df['event_type'] == event_type_filter]

    if start_datetime:
        log_df = log_df[log_df['timestamp'] >= start_datetime]
    if end_datetime:
        log_df = log_df[log_df['timestamp'] <= end_datetime]
    
    log_df['time_period'] = log_df['timestamp'].dt.floor('min')
    events_over_time = log_df.groupby('time_period').size().reset_index(name='event_count')
    
    return events_over_time

def plot_performance_metrics(activity_df, canvas_frame):
    for widget in canvas_frame.winfo_children():
        widget.destroy()

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(activity_df['time_period'], activity_df['event_count'])
    ax.set_title("Atividade ao Longo do Tempo")
    ax.set_xlabel("Tempo")
    ax.set_ylabel("Contagem de Eventos")
    ax.tick_params(axis='x', rotation=45)
    fig.autofmt_xdate()

    canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

def atualizar_graficos():
    tribunal_filter = tribunal_var.get()
    ur_filter = ur_var.get()
    token_filter = token_var.get()
    event_type_filter = event_type_var.get()
    
    start_datetime = pd.to_datetime(f"{start_date_var.get()} {start_hour_var.get()}", errors='coerce')
    end_datetime = pd.to_datetime(f"{end_date_var.get()} {end_hour_var.get()}", errors='coerce')
    
    activity_df = calculate_performance_metrics(log_df, tribunal_filter, ur_filter, token_filter, event_type_filter, start_datetime, end_datetime)
    plot_performance_metrics(activity_df, canvas_frame)

log_df = load_logs("logsgraficos")

root = tk.Tk()
root.title("Filtro de Logs e Visualização")
root.geometry("1000x700")

# Frame para os filtros
filter_frame = tk.Frame(root)
filter_frame.pack(fill=tk.X, padx=10, pady=10)

# Frame para o gráfico
canvas_frame = tk.Frame(root)
canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

tribunais_disponiveis = ["Todos"] + sorted(log_df['sistema_info'].unique())
urs_disponiveis = ["Todos"] + sorted(log_df['ur_id'].unique())
tokens_disponiveis = ["Todos", "login", "a1x"]
eventos_disponiveis = ["Todos"] + sorted(log_df['event_type'].unique())

tribunal_var = tk.StringVar(value="Todos")
ur_var = tk.StringVar(value="Todos")
token_var = tk.StringVar(value="Todos")
event_type_var = tk.StringVar(value="Todos")

start_date_var = tk.StringVar(value=log_df['timestamp'].min().strftime('%Y-%m-%d'))
start_hour_var = tk.StringVar(value="00:00")
end_date_var = tk.StringVar(value=log_df['timestamp'].max().strftime('%Y-%m-%d'))
end_hour_var = tk.StringVar(value="23:59")

# Configura os widgets dos filtros em uma grade horizontal
ttk.Label(filter_frame, text="Tribunal:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
tribunal_menu = ttk.Combobox(filter_frame, textvariable=tribunal_var, values=tribunais_disponiveis)
tribunal_menu.grid(row=0, column=1, padx=5, pady=5, sticky="w")

ttk.Label(filter_frame, text="UR:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
ur_menu = ttk.Combobox(filter_frame, textvariable=ur_var, values=urs_disponiveis)
ur_menu.grid(row=0, column=3, padx=5, pady=5, sticky="w")

ttk.Label(filter_frame, text="Token:").grid(row=0, column=4, padx=5, pady=5, sticky="w")
token_menu = ttk.Combobox(filter_frame, textvariable=token_var, values=tokens_disponiveis)
token_menu.grid(row=0, column=5, padx=5, pady=5, sticky="w")

ttk.Label(filter_frame, text="Evento:").grid(row=0, column=6, padx=5, pady=5, sticky="w")
event_type_menu = ttk.Combobox(filter_frame, textvariable=event_type_var, values=eventos_disponiveis)
event_type_menu.grid(row=0, column=7, padx=5, pady=5, sticky="w")

ttk.Label(filter_frame, text="Data Início:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
start_date_entry = ttk.Entry(filter_frame, textvariable=start_date_var, width=12)
start_date_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

ttk.Label(filter_frame, text="Hora Início:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
start_hour_entry = ttk.Entry(filter_frame, textvariable=start_hour_var, width=6)
start_hour_entry.grid(row=1, column=3, padx=5, pady=5, sticky="w")

ttk.Label(filter_frame, text="Data Fim:").grid(row=1, column=4, padx=5, pady=5, sticky="w")
end_date_entry = ttk.Entry(filter_frame, textvariable=end_date_var, width=12)
end_date_entry.grid(row=1, column=5, padx=5, pady=5, sticky="w")

ttk.Label(filter_frame, text="Hora Fim:").grid(row=1, column=6, padx=5, pady=5, sticky="w")
end_hour_entry = ttk.Entry(filter_frame, textvariable=end_hour_var, width=6)
end_hour_entry.grid(row=1, column=7, padx=5, pady=5, sticky="w")

atualizar_button = ttk.Button(filter_frame, text="Atualizar Gráficos", command=atualizar_graficos)
atualizar_button.grid(row=1, column=8, padx=10, pady=5)

root.mainloop()

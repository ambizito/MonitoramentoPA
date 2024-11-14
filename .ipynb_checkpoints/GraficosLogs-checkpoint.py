import os
import re
import pandas as pd
from datetime import datetime
import plotly.express as px
from ipywidgets import interact, Dropdown
import ipywidgets as widgets
from IPython.display import display

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
    match = re.match(r"(.+?)@.+? em (\d+\.\d+\.pje\.\d+)", line.strip())
    if match:
        login = match.group(1)
        sistema_info = match.group(2)
        login_type = "login" if login.isdigit() else "a1x"
        oab_estado, oab_numero = (login[:2], login[2:]) if login_type == "a1x" else (None, None)

        return {
            "login": login,
            "login_type": login_type,
            "oab_estado": oab_estado,
            "oab_numero": oab_numero,
            "sistema_info": sistema_info
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

def calculate_performance_metrics(log_df, tribunal_filter=None, ur_filter=None, event_type_filter=None):
    # Aplica os filtros conforme os parâmetros passados
    if tribunal_filter and tribunal_filter != "Todos":
        log_df = log_df[log_df['sistema_info'].str.contains(tribunal_filter)]
    if ur_filter and ur_filter != "Todos":
        log_df = log_df[log_df['login'].str.contains(ur_filter)]
    if event_type_filter and event_type_filter != "Todos":
        log_df = log_df[log_df['event_type'] == event_type_filter]
    
    log_df = log_df.sort_values(['login', 'timestamp']).reset_index(drop=True)
    log_df['time_diff'] = log_df.groupby('login')['timestamp'].diff().dt.total_seconds()
    latency_by_event = log_df.groupby('event_type')['time_diff'].mean().reset_index()
    latency_by_event.columns = ['event_type', 'average_latency']
    
    log_df['time_period'] = log_df['timestamp'].dt.floor('min')
    events_over_time = log_df.groupby('time_period').size().reset_index(name='event_count')
    
    return latency_by_event, events_over_time

def plot_performance_metrics(latency_df, activity_df):
    fig_latency = px.bar(
        latency_df,
        x='event_type',
        y='average_latency',
        title="Latência Média entre Eventos",
        labels={'average_latency': 'Latência Média (segundos)', 'event_type': 'Tipo de Evento'}
    )
    fig_latency.show()

    fig_activity = px.line(
        activity_df,
        x='time_period',
        y='event_count',
        title="Atividade ao Longo do Tempo",
        labels={'time_period': 'Tempo', 'event_count': 'Contagem de Eventos'}
    )
    fig_activity.show()

# Carrega os dados de log
log_df = load_logs("logsgraficos")

# Configura os widgets para filtragem
tribunais_disponiveis = ["Todos"] + sorted(log_df['sistema_info'].unique())
urs_disponiveis = ["Todos"] + sorted(log_df['login'].unique())
eventos_disponiveis = ["Todos"] + sorted(log_df['event_type'].unique())

tribunal_widget = Dropdown(options=tribunais_disponiveis, description="Tribunal:")
ur_widget = Dropdown(options=urs_disponiveis, description="UR:")
event_type_widget = Dropdown(options=eventos_disponiveis, description="Tipo de Evento:")

def atualiza_graficos(tribunal, ur, event_type):
    if not log_df.empty:
        latency_df, activity_df = calculate_performance_metrics(log_df, tribunal, ur, event_type)
        plot_performance_metrics(latency_df, activity_df)
    else:
        print("Nenhum dado foi carregado dos arquivos de log.")

# Cria uma interface interativa
interact(atualiza_graficos, tribunal=tribunal_widget, ur=ur_widget, event_type=event_type_widget)

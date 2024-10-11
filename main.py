# main.py
from tasks import tasks
from logging_config import logger
from datetime import datetime, timedelta, time as dt_time
import threading
import time

# Eventos para comunicação entre threads
forcar_execucao_event = threading.Event()
status_request_event = threading.Event()
run_specific_task_event = threading.Event()
command_queue = []

# Variáveis globais para armazenar os próximos horários de execução
proximas_execucoes = {}

# Definir os horários das tarefas no main.py
schedule = {
    "task_queries_9am": dt_time(hour=9, minute=0),
    "task_bigtable_dominios": dt_time(hour=11, minute=0),
    # Adicione mais tarefas e horários conforme necessário
}

# Função para aguardar até um horário específico
def aguardar_ate(hora_alvo):
    agora = datetime.now()
    horario_alvo = datetime.combine(agora.date(), hora_alvo)
    if horario_alvo <= agora:
        # Se o horário já passou, agendar para o dia seguinte
        horario_alvo += timedelta(days=1)
    tempo_espera = (horario_alvo - agora).total_seconds()
    # Removendo a data da mensagem
    logger.info(f"Aguardando até {horario_alvo.strftime('%H:%M:%S')} para executar a próxima tarefa")
    return tempo_espera, horario_alvo

# Função para exibir o status
def exibir_status():
    logger.info("Status atual do script:")
    for task_name, exec_time in proximas_execucoes.items():
        logger.info(f"Próxima execução de {task_name}: {exec_time.strftime('%d/%m/%Y %H:%M:%S')}")

# Thread para comandos do usuário
def comandos_usuario():
    while True:
        comando = input().strip()
        if comando.lower() == 'run':
            logger.info("Comando 'run' recebido: forçando execução de todas as tarefas")
            forcar_execucao_event.set()
        elif comando.lower().startswith('run task'):
            _, _, task_name = comando.partition(' ')
            task_name = task_name.strip()
            if task_name in tasks:
                command_queue.append(task_name)
                run_specific_task_event.set()
                logger.info(f"Comando recebido: Executando tarefa '{task_name}'")
            else:
                logger.warning(f"Tarefa '{task_name}' não encontrada.")
        elif comando.lower() == 'tasklist':
            logger.info("Tarefas disponíveis:")
            for task_name in tasks.keys():
                logger.info(f"- {task_name}")
        elif comando.lower() == 'status':
            logger.info("Comando 'status' recebido")
            status_request_event.set()
        elif comando.lower() == 'help':
            logger.info("Comandos disponíveis:")
            logger.info("- run: Executa todas as tarefas imediatamente")
            logger.info("- run task <nome_da_tarefa>: Executa a tarefa especificada")
            logger.info("- tasklist: Lista todas as tarefas disponíveis")
            logger.info("- status: Exibe o status atual e próximos horários de execução")
            logger.info("- help: Exibe esta mensagem de ajuda")
        else:
            logger.warning(f"Comando desconhecido: '{comando}'. Digite 'help' para ver os comandos disponíveis.")

# Função para esperar por um tempo determinado, podendo ser interrompida por eventos
def esperar(tempo_espera):
    inicio = time.time()
    while time.time() - inicio < tempo_espera:
        if forcar_execucao_event.is_set():
            forcar_execucao_event.clear()
            logger.info("Forçando execução de todas as tarefas")
            for task_name, task_func in tasks.items():
                try:
                    logger.info(f"Executando {task_name}")
                    task_func()
                except Exception as e:
                    logger.error(f"Erro ao executar {task_name}: {e}")
            break  # Saia do loop após a execução forçada
        if run_specific_task_event.is_set():
            run_specific_task_event.clear()
            while command_queue:
                task_name = command_queue.pop(0)
                try:
                    task_func = tasks.get(task_name)
                    if task_func:
                        logger.info(f"Executando tarefa {task_name}")
                        task_func()
                    else:
                        logger.warning(f"Tarefa {task_name} não encontrada")
                except Exception as e:
                    logger.error(f"Erro ao executar {task_name}: {e}")
        if status_request_event.is_set():
            status_request_event.clear()
            exibir_status()
        time.sleep(1)

def main():
    global proximas_execucoes

    # Iniciar a thread para escutar comandos do usuário
    threading.Thread(target=comandos_usuario, daemon=True).start()

    # Inicializar os próximos horários de execução
    proximas_execucoes = {}
    for task_name, task_time in schedule.items():
        _, proxima_execucao = aguardar_ate(task_time)
        proximas_execucoes[task_name] = proxima_execucao

    while True:
        agora = datetime.now()
        # Encontrar a próxima tarefa a ser executada
        proxima_tarefa = None
        tempo_ate_proxima_tarefa = None

        for task_name, exec_time in proximas_execucoes.items():
            tempo_ate_execucao = (exec_time - agora).total_seconds()
            if tempo_ate_execucao < 0:
                # Hora da tarefa já passou, pode executar imediatamente
                tempo_ate_execucao = 0
            if tempo_ate_proxima_tarefa is None or tempo_ate_execucao < tempo_ate_proxima_tarefa:
                tempo_ate_proxima_tarefa = tempo_ate_execucao
                proxima_tarefa = task_name

        if proxima_tarefa is None:
            logger.info("Nenhuma tarefa agendada.")
            # Aguardar um tempo padrão antes de verificar novamente
            esperar(60)
            continue

        logger.info(f"Próxima tarefa: {proxima_tarefa} em {tempo_ate_proxima_tarefa} segundos.")
        esperar(tempo_ate_proxima_tarefa)

        # Executar a próxima tarefa
        task_func = tasks.get(proxima_tarefa)
        if task_func:
            logger.info(f"Iniciando a execução de {proxima_tarefa}")
            try:
                task_func()
                logger.info(f"Tarefa {proxima_tarefa} concluída")
            except Exception as e:
                logger.error(f"Erro durante a execução de {proxima_tarefa}: {e}")
        else:
            logger.error(f"Tarefa {proxima_tarefa} não encontrada no módulo tasks.")

        # Atualizar o próximo horário de execução da tarefa
        _, proxima_execucao = aguardar_ate(schedule[proxima_tarefa])
        proximas_execucoes[proxima_tarefa] = proxima_execucao

if __name__ == "__main__":
    main()

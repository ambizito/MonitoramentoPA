from datetime import datetime, timedelta
from bson import ObjectId
from collections import defaultdict
from util import bigtable_credenciais, tokens, bigtable_dominios
import subprocess
import threading
import os
import re

def consultar_credenciais_pendentes():
    # Calcula a data das últimas 24 horas
    data_24h_atras = datetime.now() - timedelta(days=1)

    # Passo 1: Obter todos os 'sistema' ativos da coleção 'bigtable_dominios'
    sistemas_ativos_cursor = bigtable_dominios.find({
        "sistema": { "$ne": "erro" },
        "servidor": { "$ne": "erro" }
    })
    sistemas_ativos = [doc["sistema"] for doc in sistemas_ativos_cursor]

    # Passo 2: Usar os 'sistema' ativos para filtrar os documentos da coleção 'bigtable_credenciais'
    query = {
        "avaliacao": "pendente",
        "tipo": {"$in": ["a1x", "credencial"]},
        "ultima_atualizacao": {"$gte": data_24h_atras},
        "sistema": {"$in": sistemas_ativos}
    }

    # Busca os documentos na coleção bigtable_credenciais
    resultados = list(bigtable_credenciais.find(query))

    # Exibe o número de documentos encontrados
    total_documentos = len(resultados)
    print(f"Total de documentos encontrados: {total_documentos}")

    if total_documentos == 0:
        print("Nenhum documento pendente encontrado. Encerrando o script.")
        return

    # Pergunta ao usuário quantos processos deseja executar em paralelo
    while True:
        try:
            max_threads_input = input("Quantos processos deseja executar em paralelo? (0 para ilimitado): ")
            max_threads = int(max_threads_input)
            if max_threads < 0:
                print("Por favor, insira um número válido (0 ou maior).")
                continue
            break
        except ValueError:
            print("Entrada inválida. Por favor, insira um número inteiro.")
            continue

    # Dicionário para armazenar tokens agrupados por tribunal
    tokens_por_tribunal = defaultdict(list)

    # Processa cada documento para agrupar tokens por tribunal
    for documento in resultados:
        token_id_str = documento.get("token_id")
        if token_id_str:
            try:
                token_id = ObjectId(token_id_str)
                # Busca o documento do token na coleção tokens
                resultado_token = tokens.find_one({"_id": token_id})
                if resultado_token:
                    tribunal_id = resultado_token.get("tribunalId", ["Desconhecido"])[0]
                    # Adiciona um dicionário com as informações necessárias à lista do respectivo tribunal
                    tokens_por_tribunal[tribunal_id].append({
                        'token_id_str': token_id_str,
                        'token_info': resultado_token,
                        'documento_info': documento
                    })
                else:
                    print(f"Token não encontrado para token_id {token_id_str}")
            except Exception as e:
                print(f"Erro ao consultar token_id {token_id_str}: {e}")

    # Calcula o total de tribunais e tokens
    total_tribunais = len(tokens_por_tribunal)
    total_tokens = sum(len(tokens_list) for tokens_list in tokens_por_tribunal.values())

    print(f"Total de tribunais a serem processados: {total_tribunais}")
    print(f"Total de tokens a serem processados: {total_tokens}")

    # Variáveis para controle de progresso
    tokens_processados = 0
    tribunais_processados = 0
    progress_lock = threading.Lock()

    # Semáforo para controlar o número de threads ativas
    semaphore = threading.Semaphore(max_threads) if max_threads > 0 else threading.Semaphore()

    threads = []

    # Função para executar o executável com controle de semáforo
    def executar_executavel_com_limite(tribunal_id, tokens_list):
        nonlocal tribunais_processados, tokens_processados
        with semaphore:
            for token_data in tokens_list:
                token_id_str = token_data['token_id_str']
                token_info = token_data['token_info']
                documento_info = token_data['documento_info']
                executar_executavel(tribunal_id, token_id_str, token_info, documento_info)
                with progress_lock:
                    tokens_processados += 1
                    print(f"Progresso: {tokens_processados}/{total_tokens} tokens processados.")
            with progress_lock:
                tribunais_processados += 1
                print(f"Tribunal {tribunal_id} processado. Progresso: {tribunais_processados}/{total_tribunais} tribunais processados.")

    # Para cada tribunal, inicia uma thread para processar os tokens
    for tribunal_id, tokens_list in tokens_por_tribunal.items():
        thread = threading.Thread(target=executar_executavel_com_limite, args=(tribunal_id, tokens_list))
        thread.start()
        threads.append(thread)

    # Aguarda todas as threads concluírem
    for thread in threads:
        thread.join()

def executar_executavel(tribunal_id, token_id, token_info, documento_info):
    try:
        # Caminho para o executável
        executable_path = r"C:\Users\AndreAzevedo\Source\Repos\ProcessoAgil\ProcessoAgil.Logins\bin\Debug\ProcessoAgil.Logins.exe"

        # Diretório de trabalho
        working_dir = r"C:\Users\AndreAzevedo\Source\Repos\ProcessoAgil\ProcessoAgil.Logins\bin\Debug"

        # Monta o comando
        comando = [executable_path, "-id", token_id, "--rodar"]

        # Executa o executável e captura a saída
        result = subprocess.run(comando, cwd=working_dir, capture_output=True, text=True)

        # Exibe a saída e os erros
        print(f"Saída para token_id {token_id}:\n{result.stdout}")
        if result.stderr:
            print(f"Erros para token_id {token_id}:\n{result.stderr}")

        # Analisa a saída para encontrar links acessados e erros
        acessed_links = []
        errors = []
        for line in result.stdout.splitlines():
            # Verifica se a linha contém "Acessou {link}"
            match_access = re.search(r'Acessou\s+(https?://\S+)', line)
            if match_access:
                link = match_access.group(1)
                acessed_links.append(link)
            # Verifica se a linha contém "Erro no acesso: {mensagem_de_erro}"
            match_error = re.search(r'Erro no acesso:\s+(.*)', line)
            if match_error:
                error_message = match_error.group(1)
                errors.append(error_message)

        # Armazena o link do tribunal (apenas o primeiro encontrado)
        tribunal_link = acessed_links[0] if acessed_links else "Link não encontrado"

        # Decide se ocorreu um erro
        if result.returncode != 0 or errors:
            # Coleta as informações do token
            token_name = token_info.get('token', 'Desconhecido')
            # Obtém o documento (CPF ou OAB) do documento de credencial
            documento = documento_info.get('documento', 'Desconhecido')
            drive = token_info.get('drive', 'Desconhecido')
            # Monta a entrada de erro
            error_entry = f"{token_id} {token_name}:{documento} {drive}"
            # Nome do arquivo de erros
            error_file_name = f"erros_tokens_{tribunal_id}.txt"

            # Garante que apenas uma thread escreve no arquivo por vez
            with threading.Lock():
                # Verifica se o link já foi escrito no arquivo
                if not os.path.exists(error_file_name) or os.path.getsize(error_file_name) == 0:
                    # Escreve o link no início do arquivo
                    with open(error_file_name, 'w', encoding='utf-8') as error_file:
                        error_file.write(f"Link do tribunal: {tribunal_link}\n")
                        error_file.write(error_entry + '\n')
                else:
                    # Anexa a entrada de erro ao arquivo existente
                    with open(error_file_name, 'a', encoding='utf-8') as error_file:
                        error_file.write(error_entry + '\n')
            print(f"Erro ao executar o token_id {token_id}. Informação salva em {error_file_name}")
        else:
            print(f"Token_id {token_id} concluído com sucesso.")

    except Exception as e:
        print(f"Erro ao executar o token_id {token_id}: {e}")

if __name__ == "__main__":
    consultar_credenciais_pendentes()

# tasksApis.py

import os
import requests
from dotenv import load_dotenv
from logging_config import logger  # Certifique-se de que este módulo existe
import time

load_dotenv()

# URLs e Headers
BASE_URL = "https://bi.processoagil.com.br/api/bigtable/estatisticas/tribunais"
BASE_URL_TESTE_PROCESSOS = "https://bi.processoagil.com.br/api/teste/processosTeste"
BASE_URL_CARREGAR_FILTROS = "https://bi.processoagil.com.br/api/carregarFiltrosUrAnaliseDeProcessos"
AUTHORIZATION_HEADER = os.getenv('AUTHORIZATION_HEADER')

if not AUTHORIZATION_HEADER:
    raise Exception("A variável de ambiente 'AUTHORIZATION_HEADER' não está definida.")

HEADERS = {"authorization": AUTHORIZATION_HEADER}

def get_value(data_dict, key_list):
    for key in key_list:
        if isinstance(data_dict, dict):
            data_dict = data_dict.get(key, {})
        else:
            return None
    return data_dict if data_dict != {} else None

def Api_consultaP(range_value):
    url = f"{BASE_URL}?range={range_value}"
    try:
        response = requests.get(url=url, headers=HEADERS)
        response.raise_for_status()
        consultaPublica = response.json()
        return consultaPublica
    except Exception as e:
        logger.error(f"Erro ao chamar a API: {e}")
        return {}

def obter_dados_api(range_value):
    tentativa = 0
    max_tentativas = 5
    intervalo_tentativa = 60  # 1 minuto em segundos

    while tentativa < max_tentativas:
        try:
            dados_api = Api_consultaP(range_value)

            # Usando a função auxiliar para acessar os campos
            data_criacao = get_value(dados_api, ['resultado', 'relatorio', 'data_criacao'])
            percentual_processos_atualizados_24h = get_value(
                dados_api, ['resultado', 'relatorio', 'estatisticas', 'percentual_processos_atualizados_24h'])
            classificacoes = get_value(
                dados_api, ['resultado', 'relatorio', 'estatisticas', 'classificacoes']) or []

            # Verificando se 'fudeu' tem 'quantidade' maior que 0
            fudeu_quantidade = 0
            for classificacao in classificacoes:
                if classificacao.get('classificacao') == 'fudeu':
                    fudeu_quantidade = classificacao.get('quantidade', 0)
                    break  # Encontrou 'fudeu', pode sair do loop

            dados_para_salvar = {
                'data_criacao': data_criacao,
                'percentual_processos_atualizados_24h': percentual_processos_atualizados_24h,
                'fudeu_quantidade': fudeu_quantidade
            }

            # Exibindo mensagem no console
            logger.info("Dados da API obtidos com sucesso")

            if fudeu_quantidade > 0:
                status_msg = f"{data_criacao} percentual {percentual_processos_atualizados_24h} Status: fudeu"
                logger.warning(status_msg)
                dados_para_salvar['status'] = 'fudeu'
            else:
                status_msg = f"{data_criacao} percentual {percentual_processos_atualizados_24h}"
                logger.info(status_msg)

            return dados_para_salvar

        except Exception as e:
            tentativa += 1
            logger.error(f"Erro ao obter dados da API (tentativa {tentativa}/{max_tentativas}): {e}")

            if tentativa < max_tentativas:
                logger.info(f"Tentando novamente em {intervalo_tentativa} segundos...")
                time.sleep(intervalo_tentativa)
            else:
                logger.error("Número máximo de tentativas atingido. Falha ao obter dados da API.")
                return None
            
def obter_tabela_tokens():
    try:
        response = requests.get(url=BASE_URL_TESTE_PROCESSOS, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        if data.get('sucesso') and data.get('resultado'):
            tabela_tokens = data['resultado'].get('tabelaTokens', [])
            return tabela_tokens
        else:
            logger.error("Erro ao obter tabelaTokens: resposta inesperada da API.")
            return []
    except Exception as e:
        logger.error(f"Erro ao chamar a API processosTeste: {e}")
        return []
    
def obter_filtros_ur(ur):
    url = f"{BASE_URL_CARREGAR_FILTROS}/{ur}"
    try:
        response = requests.get(url=url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        if data.get('sucesso'):
            return data
        else:
            logger.error(f"Erro ao obter filtros para UR {ur}: resposta inesperada da API.")
            return {}
    except Exception as e:
        logger.error(f"Erro ao chamar a API carregarFiltrosUrAnaliseDeProcessos: {e}")
        return {}

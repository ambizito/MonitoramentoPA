# models/api_model.py

import os
import requests
import time
from dotenv import load_dotenv

class APIModel:
    def __init__(self):
        load_dotenv()
        self.BASE_URL = "https://bi.processoagil.com.br/api/bigtable/estatisticas/tribunais"
        self.AUTHORIZATION_HEADER = os.getenv('AUTHORIZATION_HEADER')

        if not self.AUTHORIZATION_HEADER:
            raise Exception("A variável de ambiente 'AUTHORIZATION_HEADER' não está definida.")

        self.HEADERS = {"authorization": self.AUTHORIZATION_HEADER}

    def get_value(self, data_dict, key_list):
        for key in key_list:
            if isinstance(data_dict, dict):
                data_dict = data_dict.get(key, {})
            else:
                return None
        return data_dict if data_dict != {} else None

    def obter_dados_api(self, range_value, fila):
        url = f"{self.BASE_URL}?range={range_value}&fila={fila}"
        tentativa = 0
        max_tentativas = 5
        intervalo_tentativa = 60  # 1 minuto em segundos

        while tentativa < max_tentativas:
            try:
                response = requests.get(url=url, headers=self.HEADERS)
                response.raise_for_status()
                dados_api = response.json()

                # Usando a função auxiliar para acessar os campos
                data_criacao = self.get_value(dados_api, ['resultado', 'relatorio', 'data_criacao'])
                percentual_processos_atualizados_24h = self.get_value(
                    dados_api, ['resultado', 'relatorio', 'estatisticas', 'percentual_processos_atualizados_24h'])
                classificacoes = self.get_value(
                    dados_api, ['resultado', 'relatorio', 'estatisticas', 'classificacoes']) or []

                # Verificando se 'fudeu' tem 'quantidade' maior que 0
                fudeu_quantidade = 0
                for classificacao in classificacoes:
                    if classificacao.get('classificacao') == 'fudeu':
                        fudeu_quantidade = classificacao.get('quantidade', 0)
                        break

                dados_para_retornar = {
                    'data_criacao': data_criacao,
                    'percentual_processos_atualizados_24h': percentual_processos_atualizados_24h,
                    'fudeu_quantidade': fudeu_quantidade,
                    'fila': fila
                }

                dados_para_retornar['status'] = 'fudeu' if fudeu_quantidade > 0 else 'OK'

                return dados_para_retornar

            except Exception as e:
                tentativa += 1
                print(f"Erro ao obter dados da API (tentativa {tentativa}/{max_tentativas}): {e}")

                if tentativa < max_tentativas:
                    print(f"Tentando novamente em {intervalo_tentativa} segundos...")
                    time.sleep(intervalo_tentativa)
                else:
                    print("Número máximo de tentativas atingido. Falha ao obter dados da API.")
                    return None

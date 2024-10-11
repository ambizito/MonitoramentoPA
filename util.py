# util.py
import requests
from logging_config import logger
from bson import json_util
import os
from datetime import datetime
from pymongo import MongoClient

# URLs de conexão MongoDB
mongoTribunalUrl = ""
TransparenciaUrl = ""

# URLs de conexão MongoDB
mongoTribunalUrl = ""
TransparenciaUrl = ""

# Conexão com o MongoDB do Tribunal
mongoTribunal = MongoClient(mongoTribunalUrl)
mongoTribunalSoftUrbano = mongoTribunal["softurbano"]
tokens = mongoTribunalSoftUrbano["tokens"]

# Conexão com o MongoDB da Transparência
mongoTransparencia = MongoClient(TransparenciaUrl)

# Banco de dados 'softurbano'
mongoTransparenciaDB_softurbano = mongoTransparencia["softurbano"]

# Coleções do banco de dados SoftUrbano
bigtable_credenciais = mongoTransparenciaDB_softurbano["bigtable_credenciais"]
bigtable_dominios = mongoTransparenciaDB_softurbano["bigtable_dominios"]

# Exportar as conexões e coleções necessárias
__all__ = [
    'mongoTribunalSoftUrbano', 'tokens', 'bigtable_credenciais'
]


# URLs e Headers
urlConsultaP = "https://bi.processoagil.com.br/api/bigtable/estatisticas/tribunais"
Header = {"authorization": "Basic uPIEIs2JxxpbqzKBt3oVkTFsePrfEz3zNg4fbn7aIu4yh226XKBzQMc5TEbtFZi7+PqXRDrEkTObIq8DAXmBoAAGvjrDrxWFw2c12VbDdW8="}


def Api_consultaP():
    try:
        response = requests.get(url=urlConsultaP, headers=Header)
        response.raise_for_status()
        consultaPublica = response.json()
        return consultaPublica
    except Exception as e:
        logger.error(f"Erro ao chamar a API: {e}")
        return {}

# Função para salvar os resultados em um arquivo .txt
def salvar_em_txt(conteudo, nome_arquivo, diretorio):
    logger.info(f"Tentando salvar dados em {diretorio}")
    try:
        # Garantir que o diretório existe
        if not os.path.exists(diretorio):
            os.makedirs(diretorio)

        # Formatar data e hora
        data_hora_atual = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Construir o nome completo do arquivo com data e hora
        nome_completo = f"{data_hora_atual}_{nome_arquivo}"

        # Caminho completo do arquivo
        caminho_arquivo = os.path.join(diretorio, nome_completo)

        with open(caminho_arquivo, 'w', encoding='utf-8') as file:
            if isinstance(conteudo, dict):
                json_str = json_util.dumps(conteudo, ensure_ascii=False, indent=4)
                file.write(json_str)
            else:
                for item in conteudo:
                    json_str = json_util.dumps(item, ensure_ascii=False)
                    file.write(json_str + '\n')
        logger.info(f"Dados salvos com sucesso em {caminho_arquivo}")
    except Exception as e:
        logger.error(f"Erro ao salvar dados em {nome_arquivo}: {e}")

def get_value(data_dict, key_list):
    for key in key_list:
        if isinstance(data_dict, dict):
            data_dict = data_dict.get(key, {})
        else:
            return None
    return data_dict if data_dict != {} else None

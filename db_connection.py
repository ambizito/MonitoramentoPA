# db_connection.py

import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def get_mongo_client():
    # URLs de conexão obtidas das variáveis de ambiente
    mongo_tribunal_url = os.getenv('MONGO_TRIBUNAL_URL')
    transparencia_url = os.getenv('TRANSPARENCIA_URL')

    # Verificar se as URLs estão definidas
    if not mongo_tribunal_url or not transparencia_url:
        raise Exception("As URLs de conexão não estão definidas nas variáveis de ambiente.")

    # Conexão com o MongoDB do Tribunal (mongo_tribunal_url)
    mongo_tribunal = MongoClient(mongo_tribunal_url)
    mongo_tribunal_db = mongo_tribunal["softurbano"]
    mongo_token_contador_processo = mongo_tribunal_db["tokenContadorProcesso"]
    mongo_tokens = mongo_tribunal_db["tokens"]

    # Conexão com o MongoDB da Transparência (transparencia_url)
    mongo_transparencia = MongoClient(transparencia_url)
    mongo_transparencia_db = mongo_transparencia["softurbano"]
    mongo_bigtable_analise = mongo_transparencia_db["bigtable_analise"]

    connections = {
        'mongo_tribunal_fila': mongo_tribunal_db["fila"],
        'mongo_transparencia_db': mongo_transparencia_db,
        'mongo_token_contador_processo': mongo_token_contador_processo,
        'mongo_bigtable_analise': mongo_bigtable_analise,
        'mongo_tokens': mongo_tokens 
    }

    return connections

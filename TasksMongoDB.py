# TasksMongoDB.py

from datetime import datetime, timedelta
from db_connection import get_mongo_client
from bson.objectid import ObjectId


def query_geral24h():
    try:
        connections = get_mongo_client()
        mongoTribunalFila = connections['mongo_tribunal_fila']
    except Exception as e:
        raise Exception(f"Não foi possível conectar ao banco de dados: {e}")

    data24h = datetime.now() - timedelta(hours=21)
    geral24h_cursor = mongoTribunalFila.find({
        "sqlFlag": True,
        "temAlteracao": True,
        "instanciasAtualizadas": {"$exists": True},
        "dataDeAlteracao": {"$lt": data24h},
        "$expr": {"$gte": ["$dataDeAlteracao", "$dataDoSql"]},
    })
    geral24h_list = list(geral24h_cursor)
    return geral24h_list

def query_clientes_dedicados_24h(dedicated_urs):
    try:
        connections = get_mongo_client()
        mongoTribunalFila = connections['mongo_tribunal_fila']
    except Exception as e:
        raise Exception(f"Não foi possível conectar ao banco de dados: {e}")

    data24h = datetime.now() - timedelta(hours=21)
    clientes_dedicados_cursor = mongoTribunalFila.find({
        "sql.ur": {"$in": dedicated_urs},
        "sqlFlag": True,
        "temAlteracao": True,
        "instanciasAtualizadas": {"$exists": True},
        "dataDeAlteracao": {"$lt": data24h},
        "$expr": {"$gte": ["$dataDeAlteracao", "$dataDoSql"]}
    })
    clientes_dedicados_list = list(clientes_dedicados_cursor)
    return clientes_dedicados_list

def query_expediente_6h():
    try:
        connections = get_mongo_client()
        mongoTribunalFila = connections['mongo_tribunal_fila']
    except Exception as e:
        raise Exception(f"Não foi possível conectar ao banco de dados: {e}")

    data6h = datetime.now() - timedelta(hours=6)
    expediente_cursor = mongoTribunalFila.find({
        "sqlFlag": True,
        "temAlteracao": True,
        "sql.expediente": {"$exists": True},
        "dataDeAlteracao": {"$lte": data6h},
        "$expr": {"$gte": ["$dataDeAlteracao", "$dataDoSql"]}
    })
    expediente_list = list(expediente_cursor)
    return expediente_list

def obter_detalhes_ur(ur):
    try:
        # Conexão com o MongoDB
        connections = get_mongo_client()
        mongo_bigtable_analise = connections['mongo_bigtable_analise']
        mongo_token_contador_processo = connections['mongo_token_contador_processo']
        mongo_tokens = connections['mongo_tokens']
    except Exception as e:
        raise Exception(f"Não foi possível conectar ao banco de dados: {e}")

    # Definindo a query com base nos critérios especificados
    query = {
        "sistema": ur,
        "analise_status_producao": "ativo",
        "ativo_no_acervo": True,
        "atualizado_no_acervo": False,
        "$or": [
            {"token_status_avaliacao_manual": None},
            {
                "$expr": {
                    "$gte": [
                        "$token_data_sucesso",
                        "$token_ultima_avaliacao_manual"
                    ]
                }
            }
        ]
    }

    # Executando a query no MongoDB
    detalhes_ur_cursor = mongo_bigtable_analise.find(query)
    detalhes_ur_list = list(detalhes_ur_cursor)

    resultados = []

    # Definir o limite de tempo (últimas 24 horas)
    agora = datetime.utcnow()
    limite_tempo = agora - timedelta(hours=24)

    for processo in detalhes_ur_list:
        numero = processo.get('numero')
        if numero:
            # Consultar na coleção 'tokenContadorProcesso' para obter 'token_id' e 'atualizacao'
            token_contador_cursor = mongo_token_contador_processo.find({'numero': numero})
            token_contador_list = list(token_contador_cursor)

            # Verificar se algum documento tem 'atualizacao' nas últimas 24 horas
            ignorar_processo = False
            for token_contador in token_contador_list:
                atualizacao = token_contador.get('atualizacao')
                if atualizacao and isinstance(atualizacao, datetime):
                    if atualizacao >= limite_tempo:
                        ignorar_processo = True
                        break  # Se um documento tiver atualização recente, ignorar o processo

            if ignorar_processo:
                continue  # Pula para o próximo processo

            for token_contador in token_contador_list:
                token_id = token_contador.get('token_id')

                # Consultar na coleção 'tokens' usando 'token_id' para obter 'tipo', 'tribunal' e 'drive'
                if token_id:
                    # Certifique-se de que 'token_id' é um ObjectId
                    if not isinstance(token_id, ObjectId):
                        token_id = ObjectId(token_id)
                    token_doc = mongo_tokens.find_one({'_id': token_id})

                    if token_doc:
                        tipo = token_doc.get('tipo', 'Não encontrado')
                        tribunal = token_doc.get('tribunal', 'Não encontrado')
                        drive = token_doc.get('drive', 'Não encontrado')

                        # Montar o resultado
                        resultado = {
                            'numero': numero,
                            'token_id': str(token_id),
                            'tipo': tipo,
                            'tribunal': tribunal,
                            'drive': drive
                        }
                        resultados.append(resultado)
                    else:
                        # Caso não encontre o token na coleção 'tokens'
                        resultado = {
                            'numero': numero,
                            'token_id': str(token_id),
                            'tipo': 'Não encontrado',
                            'tribunal': 'Não encontrado',
                            'drive': 'Não encontrado'
                        }
                        resultados.append(resultado)
                else:
                    # Caso não tenha 'token_id' no 'tokenContadorProcesso'
                    resultado = {
                        'numero': numero,
                        'token_id': 'Não encontrado',
                        'tipo': 'Não encontrado',
                        'tribunal': 'Não encontrado',
                        'drive': 'Não encontrado'
                    }
                    resultados.append(resultado)
        else:
            # Caso não tenha 'numero' no processo
            continue

    return resultados

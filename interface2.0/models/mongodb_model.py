# models/mongodb_model.py

from datetime import datetime, timedelta
from .db_connection import get_mongo_client
from bson.objectid import ObjectId

class MongoDBModel:
    def __init__(self):
        connections = get_mongo_client()
        if connections is None:
            print("Conexões com o MongoDB não foram estabelecidas.")
            self.mongo_tribunal_fila = None
            self.mongo_bigtable_analise = None
            self.mongo_token_contador_processo = None
            self.mongo_tokens = None
        else:
            self.mongo_tribunal_fila = connections['mongo_tribunal_fila']
            self.mongo_bigtable_analise = connections['mongo_bigtable_analise']
            self.mongo_token_contador_processo = connections['mongo_token_contador_processo']
            self.mongo_tokens = connections['mongo_tokens']
            print("Conexões com o MongoDB estabelecidas com sucesso.")

    def get_tabela_tokens(self):
        if self.mongo_tokens is None:
            raise Exception("Conexão com mongo_tokens não está estabelecida.")
        try:
            tabela_tokens_cursor = self.mongo_tokens.find({})
            tabela_tokens_list = list(tabela_tokens_cursor)
            print(f"get_tabela_tokens: Retornando {len(tabela_tokens_list)} registros.")
            return tabela_tokens_list
        except Exception as e:
            print(f"Erro ao obter tabela de tokens: {e}")
            return []


    def get_detalhes_ur(self, ur):
        # Renomeamos o método de 'obter_detalhes_ur' para 'get_detalhes_ur' para manter a consistência
        if self.mongo_bigtable_analise is None or self.mongo_token_contador_processo is None or self.mongo_tokens is None:
            raise Exception("Conexões com as coleções do MongoDB não estão estabelecidas.")

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

        detalhes_ur_cursor = self.mongo_bigtable_analise.find(query)
        detalhes_ur_list = list(detalhes_ur_cursor)

        resultados = []

        agora = datetime.utcnow()
        limite_tempo = agora - timedelta(hours=24)

        for processo in detalhes_ur_list:
            numero = processo.get('numero')
            if numero:
                token_contador_cursor = self.mongo_token_contador_processo.find({'numero': numero})
                token_contador_list = list(token_contador_cursor)

                ignorar_processo = False
                for token_contador in token_contador_list:
                    atualizacao = token_contador.get('atualizacao')
                    if atualizacao and isinstance(atualizacao, datetime):
                        if atualizacao >= limite_tempo:
                            ignorar_processo = True
                            break

                if ignorar_processo:
                    continue

                for token_contador in token_contador_list:
                    token_id = token_contador.get('token_id')

                    if token_id:
                        if not isinstance(token_id, ObjectId):
                            token_id = ObjectId(token_id)
                        token_doc = self.mongo_tokens.find_one({'_id': token_id})

                        if token_doc:
                            tipo = token_doc.get('tipo', 'Não encontrado')
                            tribunal = token_doc.get('tribunal', 'Não encontrado')
                            drive = token_doc.get('drive', 'Não encontrado')

                            resultado = {
                                'numero': numero,
                                'token_id': str(token_id),
                                'tipo': tipo,
                                'tribunal': tribunal,
                                'drive': drive
                            }
                            resultados.append(resultado)
                        else:
                            resultado = {
                                'numero': numero,
                                'token_id': str(token_id),
                                'tipo': 'Não encontrado',
                                'tribunal': 'Não encontrado',
                                'drive': 'Não encontrado'
                            }
                            resultados.append(resultado)
                    else:
                        resultado = {
                            'numero': numero,
                            'token_id': 'Não encontrado',
                            'tipo': 'Não encontrado',
                            'tribunal': 'Não encontrado',
                            'drive': 'Não encontrado'
                        }
                        resultados.append(resultado)
            else:
                continue

        return resultados

    def query_geral24h(self):
        if self.mongo_tribunal_fila is None:
            raise Exception("Conexão com mongo_tribunal_fila não está estabelecida.")
        data24h = datetime.now() - timedelta(hours=21)
        cursor = self.mongo_tribunal_fila.find({
            "sqlFlag": True,
            "temAlteracao": True,
            "instanciasAtualizadas": {"$exists": True},
            "dataDeAlteracao": {"$lt": data24h},
            "$expr": {"$gte": ["$dataDeAlteracao", "$dataDoSql"]},
        })
        return list(cursor)

    def query_clientes_dedicados_24h(self, dedicated_urs):
        if self.mongo_tribunal_fila is None:
            raise Exception("Conexão com mongo_tribunal_fila não está estabelecida.")
        data24h = datetime.now() - timedelta(hours=21)
        cursor = self.mongo_tribunal_fila.find({
            "sql.ur": {"$in": dedicated_urs},
            "sqlFlag": True,
            "temAlteracao": True,
            "instanciasAtualizadas": {"$exists": True},
            "dataDeAlteracao": {"$lt": data24h},
            "$expr": {"$gte": ["$dataDeAlteracao", "$dataDoSql"]}
        })
        return list(cursor)

    def query_expediente_6h(self):
        if self.mongo_tribunal_fila is None:
            raise Exception("Conexão com mongo_tribunal_fila não está estabelecida.")
        data6h = datetime.now() - timedelta(hours=6)
        cursor = self.mongo_tribunal_fila.find({
            "sqlFlag": True,
            "temAlteracao": True,
            "sql.expediente": {"$exists": True},
            "dataDeAlteracao": {"$lte": data6h},
            "$expr": {"$gte": ["$dataDeAlteracao", "$dataDoSql"]}
        })
        return list(cursor)
    
    def obter_detalhes_ur(self, ur):
        if self.mongo_bigtable_analise is None or self.mongo_token_contador_processo is None or self.mongo_tokens is None:
            raise Exception("Conexões com as coleções do MongoDB não estão estabelecidas.")

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

        detalhes_ur_cursor = self.mongo_bigtable_analise.find(query)
        detalhes_ur_list = list(detalhes_ur_cursor)

        resultados = []

        agora = datetime.utcnow()
        limite_tempo = agora - timedelta(hours=24)

        for processo in detalhes_ur_list:
            numero = processo.get('numero')
            if numero:
                token_contador_cursor = self.mongo_token_contador_processo.find({'numero': numero})
                token_contador_list = list(token_contador_cursor)

                ignorar_processo = False
                for token_contador in token_contador_list:
                    atualizacao = token_contador.get('atualizacao')
                    if atualizacao and isinstance(atualizacao, datetime):
                        if atualizacao >= limite_tempo:
                            ignorar_processo = True
                            break

                if ignorar_processo:
                    continue

                for token_contador in token_contador_list:
                    token_id = token_contador.get('token_id')

                    if token_id:
                        if not isinstance(token_id, ObjectId):
                            token_id = ObjectId(token_id)
                        token_doc = self.mongo_tokens.find_one({'_id': token_id})

                        if token_doc:
                            tipo = token_doc.get('tipo', 'Não encontrado')
                            tribunal = token_doc.get('tribunal', 'Não encontrado')
                            drive = token_doc.get('drive', 'Não encontrado')

                            resultado = {
                                'numero': numero,
                                'token_id': str(token_id),
                                'tipo': tipo,
                                'tribunal': tribunal,
                                'drive': drive
                            }
                            resultados.append(resultado)
                        else:
                            resultado = {
                                'numero': numero,
                                'token_id': str(token_id),
                                'tipo': 'Não encontrado',
                                'tribunal': 'Não encontrado',
                                'drive': 'Não encontrado'
                            }
                            resultados.append(resultado)
                    else:
                        resultado = {
                            'numero': numero,
                            'token_id': 'Não encontrado',
                            'tipo': 'Não encontrado',
                            'tribunal': 'Não encontrado',
                            'drive': 'Não encontrado'
                        }
                        resultados.append(resultado)
            else:
                continue

        return resultados

    def query_transparencia_24h(self, dedicated_urs):
        if self.mongo_tribunal_fila is None:
            raise Exception("Conexão com mongo_tribunal_fila não está estabelecida.")
        data24h = datetime.now() - timedelta(hours=24)
        cursor = self.mongo_tribunal_fila.find({
            "sqlFlag": True,
            "temAlteracao": True,
            "instanciasAtualizadas": {"$exists": True},
            "dataDeAlteracao": {"$lt": data24h},
            "$expr": {"$gte": ["$dataDeAlteracao", "$dataDoSql"]}
        })
        return list(cursor)
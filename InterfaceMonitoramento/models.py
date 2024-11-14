# models.py
from TasksMongoDB import (
    query_geral24h,
    query_clientes_dedicados_24h,
    query_expediente_6h,
    obter_detalhes_ur as obter_detalhes_ur_mongo
)
from TasksApis import obter_dados_api, obter_tabela_tokens
from db_connection import get_mongo_client

class DataModel:
    def __init__(self):
        try:
            connections = get_mongo_client()
            self.mongo_bigtable_analise = connections['mongo_bigtable_analise']
            self.mongo_token_contador_processo = connections['mongo_token_contador_processo']
        except Exception as e:
            raise ConnectionError(f"Não foi possível conectar ao banco de dados: {e}")

    def get_tabela_tokens(self):
        return obter_tabela_tokens()

    def get_detalhes_ur(self, ur):
        return obter_detalhes_ur_mongo(ur)

    def get_dados_api(self, range_value):
        return obter_dados_api(range_value)

    def get_query_geral24h(self):
        return query_geral24h()

    def get_query_clientes_dedicados_24h(self, dedicated_urs):
        return query_clientes_dedicados_24h(dedicated_urs)

    def get_query_expediente_6h(self):
        return query_expediente_6h()

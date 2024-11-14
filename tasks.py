# tasks.py
from logging_config import logger
from util import salvar_em_txt, get_value, Api_consultaP
from pymongo import MongoClient
from datetime import datetime, timedelta
import time

# URLs de conexão MongoDB
mongoTribunalUrl = "mongodb://softurbanotribunal:ilovemongotribunal@token.softurbano.com:30050/admin?retryWrites=true&loadBalanced=false&connectTimeoutMS=10000&authSource=admin&authMechanism=SCRAM-SHA-1"
TransparenciaUrl = "mongodb://bigtabletrasparencia:EssaSenhaEMuitoD1f1c1lParaTrasparencia#@mariobros:40060/admin?connectTimeoutMS=300000&socketTimeoutMS=300000&keepAlive=300000"


# Conexão com o MongoDB do Tribunal
mongoTribunal = MongoClient(mongoTribunalUrl)
mongoTribunalSoftUrbano = mongoTribunal["softurbano"]
mongoTribunalFila = mongoTribunalSoftUrbano["fila"]

# Conexão com o MongoDB da Transparência
mongoTransparencia = MongoClient(TransparenciaUrl)

mongoTransparenciaDB = mongoTransparencia["softurbano"]
bigtable_dominios = mongoTransparenciaDB["bigtable_dominios"]

# Diretórios para salvar os arquivos
DIRETORIO_EXPEDIENTES = r"C:\Users\AndreAzevedo\Documents\Dev\Expedientes"
DIRETORIO_TRANSPARENCIA = r"C:\Users\AndreAzevedo\Documents\Dev\Transparencia"
DIRETORIO_CONSULTA_PUBLICA = r"C:\Users\AndreAzevedo\Documents\Dev\Consulta Pública"

# Lista de URs dedicados
dedicated_urs = [
    "1BFC3BFA-D454-4123-84DD-B6DD9F2C0F08",
    "1D8AA8E2-408D-4946-87FF-52849F80DEC5",
    "298D95CA-6E34-47A5-8C9A-6D73E4EA5A1D",
    "41A3FD3A-470C-4CBA-A7CF-6C1F8BAC29D5",
    "8C863D87-8420-43B1-A2C9-7B3DEB8DE30E",
    "CE42094B-E45C-4D75-AA24-A57DD3AF5E21"
]

def obter_dados_api():
    tentativa = 0
    max_tentativas = 5
    intervalo_tentativa = 60  # 1 minuto em segundos

    while tentativa < max_tentativas:
        try:
            dados_api = Api_consultaP()

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
                'percentual_processos_atualizados_24h': percentual_processos_atualizados_24h
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

def task_queries_9am():
    logger.info("Iniciando consultas das 9h")
    try:
        # Obtendo dados da API
        dados_api = obter_dados_api()
        if dados_api:
            logger.info(f"Dados da API para salvar: {dados_api}")
            salvar_em_txt(dados_api, 'dados_api.txt', DIRETORIO_CONSULTA_PUBLICA)
            logger.info("Dados da API salvos em 'dados_api.txt'")

        # Consultas MongoDB
        data24h = datetime.now() - timedelta(hours=21)
        data6h = datetime.now() - timedelta(hours=6)

        # Primeira query: geral24h
        geral24h_cursor = mongoTribunalFila.find({
            "sqlFlag": True,
            "temAlteracao": True,
            "instanciasAtualizadas": {"$exists": True},
            "dataDeAlteracao": {"$lt": data24h},
            "$expr": {"$gte": ["$dataDeAlteracao", "$dataDoSql"]},
        })
        geral24h_list = list(geral24h_cursor)
        geral24h_count = len(geral24h_list)
        salvar_em_txt(geral24h_list, 'geral24h.txt', DIRETORIO_TRANSPARENCIA)
        if geral24h_count > 0:
            logger.warning(f"{geral24h_count} processos em geral estão atrasados")
        else:
            logger.info("Nenhum processo em geral está atrasado")

        # Segunda query: clientes_dedicados_24h
        clientes_dedicados_cursor = mongoTribunalFila.find({
            "sql.ur": {"$in": dedicated_urs},
            "sqlFlag": True,
            "temAlteracao": True,
            "instanciasAtualizadas": {"$exists": True},
            "dataDeAlteracao": {"$lt": data24h},
            "$expr": {"$gte": ["$dataDeAlteracao", "$dataDoSql"]}
        })
        clientes_dedicados_list = list(clientes_dedicados_cursor)
        clientes_dedicados_count = len(clientes_dedicados_list)
        salvar_em_txt(clientes_dedicados_list, 'clientes_dedicados_24h.txt', DIRETORIO_TRANSPARENCIA)
        if clientes_dedicados_count > 0:
            logger.warning(f"{clientes_dedicados_count} processos de clientes dedicados estão atrasados")
        else:
            logger.info("Nenhum processo de clientes dedicados está atrasado")

        # Terceira query: expediente_6h
        expediente_cursor = mongoTribunalFila.find({
            "sqlFlag": True,
            "temAlteracao": True,
            "sql.expediente": {"$exists": True},
            "dataDeAlteracao": {"$lte": data6h},
            "$expr": {"$gte": ["$dataDeAlteracao", "$dataDoSql"]}
        })
        expediente_list = list(expediente_cursor)
        expediente_count = len(expediente_list)
        salvar_em_txt(expediente_list, 'expediente_6h.txt', DIRETORIO_EXPEDIENTES)
        if expediente_count > 0:
            logger.warning(f"{expediente_count} expedientes estão atrasados")
        else:
            logger.info("Nenhum expediente está atrasado")

        logger.success("Consultas das 9h concluídas")

    except Exception as e:
        logger.error(f"Erro durante as consultas das 9h: {e}")

def task_bigtable_dominios():
    logger.info("Iniciando consulta 'bigtable_dominios'")
    try:
        data12h = datetime.now() - timedelta(hours=12)

        resultado_total = bigtable_dominios.count_documents({
           "servidor": {"$ne": "erro"}   
        })
        
        resultados_cursor = bigtable_dominios.count_documents({
            "servidor": {"$ne": "erro"},
            "dataLock": {"$gte": data12h},
        })

        salvar_em_txt(f"foram processados {resultados_cursor} de {resultado_total}", 'bigtable_dominios_resultados.txt', DIRETORIO_TRANSPARENCIA)
        

        if resultados_cursor != resultado_total:
            logger.warning(f"{resultado_total - resultados_cursor} registros em 'bigtable_dominios' estão atrasados")
        else:
            logger.info("Nenhum registro em 'bigtable_dominios' está atrasado")

        logger.success("Consulta 'bigtable_dominios' concluída")

    except Exception as e:
        logger.error(f"Erro durante a consulta 'bigtable_dominios': {e}")


# Dicionário de tarefas disponíveis
tasks = {
    "task_queries_9am": task_queries_9am,
    "task_bigtable_dominios": task_bigtable_dominios,
    # Adicione mais tarefas aqui se necessário
}

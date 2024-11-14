# services/logins_service.py

import subprocess
import threading
import re
import time


class LoginsService:
    def __init__(self, executable_path, working_dir):
        self.executable_path = executable_path
        self.working_dir = working_dir

    def executar_logins(self, token_id, callback_linha_log, callback_erro=None):
        """
        Executa o Logins para um determinado token_id.

        :param token_id: ID do token para o qual o Logins será executado.
        :param callback_linha_log: Função chamada para cada linha de saída do Logins.
        :param callback_erro: Função chamada em caso de erro na execução do Logins.
        """
        def run():
            try:
                comando = [self.executable_path, "-id", token_id, "--rodar"]

                process = subprocess.Popen(
                    comando,
                    cwd=self.working_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )

                for line in process.stdout:
                    print(line, end='')
                    line = line.strip()
                    callback_linha_log(line)

                process.wait()

            except Exception as e:
                print(f"Erro ao executar o Logins: {e}")
                if callback_erro:
                    callback_erro(e)

        threading.Thread(target=run, daemon=True).start()

    @staticmethod
    def processar_linha_log(line):
        """
        Processa uma linha de saída do Logins e extrai informações relevantes.

        :param line: Linha de saída do Logins.
        :return: Dicionário com informações extraídas ou None se não houver correspondência.
        """
        match_sucesso = re.search(r'advogado\s+([\d.-]+)\s+>>\s+Processo com', line)
        match_erro_processo = re.search(r'advogado\s+([\d.-]+)\s+>>\s+(.*)', line)
        match_erro_geral = re.search(r'^.*Erro no acesso:\s+(.*)$', line)

        if match_sucesso:
            numero_processo = match_sucesso.group(1)
            return {
                'tipo': 'sucesso',
                'numero_processo': numero_processo,
                'mensagem': 'OK'
            }
        elif match_erro_processo:
            numero_processo = match_erro_processo.group(1)
            mensagem = match_erro_processo.group(2)
            return {
                'tipo': 'erro_processo',
                'numero_processo': numero_processo,
                'mensagem': mensagem
            }
        elif match_erro_geral:
            mensagem = match_erro_geral.group(1)
            return {
                'tipo': 'erro_geral',
                'mensagem': mensagem
            }
        else:
            return None

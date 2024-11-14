import logging
import sys

# Definindo um nível de log personalizado para SUCCESS
SUCCESS_LEVEL_NUM = 25
logging.addLevelName(SUCCESS_LEVEL_NUM, "SUCCESS")

def success(self, message, *args, **kws):
    if self.isEnabledFor(SUCCESS_LEVEL_NUM):
        self._log(SUCCESS_LEVEL_NUM, message, args, **kws)

logging.Logger.success = success

class CustomFormatter(logging.Formatter):
    # Definindo formatos e cores
    reset = "\x1b[0m"

    FORMATS = {
        logging.DEBUG: "%(asctime)s " + "\x1b[37m" + "%(levelname)s:%(message)s" + reset,  # Cinza
        logging.INFO: "%(asctime)s " + "\x1b[92m" + "%(levelname)s:%(message)s" + reset,  # Verde Claro
        SUCCESS_LEVEL_NUM: "%(asctime)s " + "\x1b[32m" + "%(levelname)s:%(message)s" + reset,  # Verde Escuro
        logging.WARNING: "%(asctime)s " + "\x1b[33m" + "%(levelname)s:%(message)s" + reset,  # Amarelo
        logging.ERROR: "%(asctime)s " + "\x1b[31m" + "%(levelname)s:%(message)s" + reset,  # Vermelho
        logging.CRITICAL: "%(asctime)s " + "\x1b[31;1m" + "%(levelname)s:%(message)s" + reset  # Vermelho Negrito
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        if not log_fmt:
            log_fmt = "%(asctime)s %(levelname)s:%(message)s" + self.reset
        formatter = logging.Formatter(log_fmt, datefmt='%H:%M:%S')
        return formatter.format(record)

# Configurando o handler e o logger
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(CustomFormatter())
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.handlers = [handler]

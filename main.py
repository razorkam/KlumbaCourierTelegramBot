import logging
from logging.handlers import RotatingFileHandler
from source.TelegramWorker import TgWorker

LOG_MAX_SIZE = 2 * 1024 * 1024 # 2 mbytes


def main():
        # TODO: add logs rotation
        log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
        log_handler = RotatingFileHandler('app.log', mode='a', maxBytes=LOG_MAX_SIZE,
                                          backupCount=5)
        log_handler.setFormatter(log_formatter)
        log_handler.setLevel(logging.ERROR)
        logging.basicConfig(handlers=[log_handler])


        tg_worker = TgWorker()
        tg_worker.run()



main()
import logging
from escpos.printer import Network
from dnd import config

logger = logging.getLogger(__name__)

printer_address = config.conf["printer_configs"]["network_address"]


def print_receipt(string):
    try:
        printer = Network(printer_address)
        printer.text(string)
        printer.cut()
        return True
    except:
        logger.exception("Unable to print.")
        return False

import os
import yaml

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

try:
    with open(os.path.join(__location__, "config.yml"), 'r') as f:
        conf = yaml.safe_load(f)
except FileNotFoundError:
    print("Error config.yml not found!")
    exit(1)

import logging
logger = logging.getLogger(__name__)
logger.info("Reading config.yml")

try:
    db_location = os.environ["db_location"]
except KeyError:
    try:
        db_location = conf["general_configs"]["db_location"]
    except KeyError:
        logger.error("Database location could not be set!")
        exit(1)


def get_database_configs():
    db_configs = {}
    for config in conf["database"][db_location]["db_config"]:
        key = config
        value = conf["database"][db_location]["db_config"][key]
        db_configs[key] = value
    return db_configs

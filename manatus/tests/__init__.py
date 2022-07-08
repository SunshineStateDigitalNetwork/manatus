import configparser
import sys
from pathlib import Path

from .exceptions_test import *
from .harvest_test import *
from .maps_test import *
from .organiztions_test import *
from .scenarios_test import *
from .source_resource_test import *
from .transform_test import *

if __name__ == 'manatus.tests':
    # Locating configs
    if os.getenv('MANATUS_CONFIG'):
        CONFIG_PATH = Path(os.getenv('MANATUS_CONFIG'))
    elif os.path.exists(os.path.join(Path.home(), '.local/share/manatus/manatus.cfg')):
        CONFIG_PATH = os.path.join(Path.home(), '.local/share/manatus')
    elif os.path.exists(os.path.join(Path(__file__).parents[0], 'manatus.cfg')):
        CONFIG_PATH = Path(__file__).parents[0]
    else:
        CONFIG_PATH = None

    try:
        manatus_config = configparser.ConfigParser()
        manatus_config.read(os.path.join(CONFIG_PATH, 'manatus.cfg'))
        for profile in manatus_config.keys():
            custom_map_test_path = manatus_config[profile]['CustomMapPath']
            try:
                sys.path.append(custom_map_test_path)
                from custom_map_tests import *
            except (ModuleNotFoundError, NameError):
                pass
    except TypeError:
        pass

import logging
import os
import sys

import manatus
import manatus.maps

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def build(custom_map_function, data, org, provider):
    """apply transformation map to data iterable"""
    logger.debug('cli.build called')
    records = manatus.RecordGroup()

    logger.debug(f'Mapping data with {custom_map_function}')
    mapped_data = map(custom_map_function, data)

    logger.debug(f'Mapped data with {custom_map_function}')
    for mapped_rec in mapped_data:
        # map generators can return None if record is marked to be skipped or errors
        if mapped_rec:
            for sr, tn, *args in mapped_rec:

                logger.info(f"Building {sr.data['identifier']}")
                dpla = manatus.DPLARecord()
                if args:
                    dpla.dataProvider = args[0]
                else:
                    dpla.dataProvider = org.data_provider

                if args:
                    dpla.intermediateProvider = args[1]
                else:
                    dpla.intermediateProvider = org.intermediate_provider

                dpla.provider = {'@id': 'UNDETERMINED', 'name': provider}
                dpla.isShownAt = sr.data['identifier']
                dpla.preview = tn
                dpla.sourceResource = sr.data

                logger.debug(f"Built record {sr.data['identifier']}")
                records.append(dpla.data)

        else:
            continue

    return records


def transform(manatus_config, org_transformation_info, org_key, profile, verbosity, to_console=False):
    """
    Manatus transformation function

    :param dict manatus_config: Data from ``manatus.cfg``. See :doc:`configuration` for more information.
    :param dict org_transformation_info: Data from ``manatus_scenarios.cfg``. Includes the key, value pairs
        :py:data:`scenario`, :py:data:`map`, :py:data:`dataprovider`, and *(optional)*
        :py:data:`intermediatedataprovider`. See :doc:`configuration` for more information.
    :param str org_key: Section key in ``manatus_scenarios.cfg``. Used to locate source data for transformation.
    :param str profile: Profile invoked during run
    :param int verbosity: Set verbosity
    :param bool to_console: If set to ``True``, transformed data is written to the console rather than the file system.

    """
    logger.debug('cli.transform called')
    IN_PATH = os.path.abspath(manatus_config[profile]['InFilePath'])
    OUT_PATH = os.path.abspath(manatus_config[profile]['OutFilePath'])
    prefix = manatus_config[profile]['OutFilePrefix']
    provider = manatus_config[profile]['Provider']

    ### IMPORTING CUSTOM MAPS
    custom_map_path = os.path.abspath(manatus_config[profile]['CustomMapPath'])
    sys.path.append(custom_map_path)

    # import config key, value pairs into DataProvider slot attrs
    o = manatus.DataProvider()
    o.key = org_key
    o.map = org_transformation_info['Map']
    o.data_provider = org_transformation_info['DataProvider']
    try:
        o.intermediate_provider = org_transformation_info['IntermediateProvider']
    except KeyError:
        o.intermediate_provider = None

    ###############################################################################
    # These six lines take a string and use it to search the supplied module      #
    # for a callable function with that name.                                     #
    #   custom_map_module can only be imported (and then searched) if             #
    #       1. the module location is added to sys.path (as CustomMapPath is)     #
    #       2. the module name does not collide with another module coming before #
    #           it in the MRO (i.e. name it something unique)                     #
    ###############################################################################

    # use config scenario value to search for manatus.scenarios class
    o.scenario = getattr(manatus, org_transformation_info['Scenario'])
    # use config map value to search for callable module & function with that name
    try:
        logger.debug(f'Trying to find custom map module {o.map}')
        custom_map_module = __import__(o.map)
        custom_map_function = getattr(custom_map_module, o.map)
    except ModuleNotFoundError:
        # if custom lookup fails, fall back to manatus default maps
        custom_map_function = getattr(manatus.maps, o.map)
        logger.info(f'Custom map module {o.map} not found. Using default manatus map')

    # check scenario subclassing
    # XMLScenario subclasses read data from disk
    if issubclass(o.scenario, manatus.XMLScenario):
        for f in os.listdir(os.path.join(IN_PATH, o.key)):

            logger.info(f'Transforming {o.key} data {f}')
            if verbosity > 1:
                print(f'Transforming {o.key} data {f}')
            # parse file using scenario and get records as iterable list

            logger.debug(f'Loading data {f} with {o.scenario}')
            data = o.scenario(os.path.join(IN_PATH, o.key, f))

            logger.debug(f'Loaded data {f} with {o.scenario}')
            records = build(custom_map_function, data, o, provider)

    # APIScenario subclasses need to make queries and read data from responses
    elif issubclass(o.scenario, manatus.APIScenario):

        logger.info(f'Transforming {o.key} data API')
        if verbosity > 1:
            print(f'Transforming {o.key} data from API')

        logger.debug(f'Loading API data with {o.scenario}')
        data = o.scenario(o.key)

        logger.debug(f'Loaded API data with {o.scenario}')
        records = build(custom_map_function, data, o, provider)

    if to_console:
        logger.debug('Printing records')
        records.print()

    else:
        logger.debug(f'Writing records to {OUT_PATH}')
        records.write_jsonl(OUT_PATH, prefix=prefix)

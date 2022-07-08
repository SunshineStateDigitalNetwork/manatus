import datetime
import logging
import os

import sickle
from sickle import models
from sickle.iterator import OAIItemIterator
from sickle.utils import xml_to_dict

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class SickleRecord(models.Record):

    def __init__(self, record_element, strip_ns=True):
        models.Record.__init__(self, record_element, strip_ns=strip_ns)

    def get_metadata(self):
        try:
            self.metadata = xml_to_dict(
                self.xml.find(
                    './/' + self._oai_namespace + 'metadata'
                ).getchildren()[0], strip_ns=self._strip_ns)
        except AttributeError:
            self.metadata = None


def harvest(org_harvest_info, org_key, write_path, verbosity):
    """
    Manatus harvest function

    :param dict org_harvest_info: Dict of data from ``manatus_harvests.cfg``.
        Includes the key, value pairs :py:data:`oaiendpoint`, :py:data:`setlist`, and :py:data:`metadataprefix`.
        See :doc:`configuration` for more information.
    :param str org_key: Section key in ``manatus_harvests.cfg``. Appended to :py:data:`write_path`
    :param str write_path: File path to write data. Taken from ``manatus.cfg``
    :param int verbosity: Set verbosity

    """
    logger.debug('cli.harvest called')
    # check for dir path
    if not os.path.exists(os.path.join(write_path, org_key)):
        logger.debug(f'Creating path {os.path.join(write_path, org_key)}')
        os.makedirs(os.path.join(write_path, org_key))

    # OAI-PMH endpoint URL from config
    oai = org_harvest_info['OAIEndpoint']

    # metadataPrefix from config
    metadata_prefix = org_harvest_info['MetadataPrefix']

    # iterate through sets to harvest
    for set_spec in org_harvest_info['SetList'].split(', '):
        logger.debug(f'Harvesting {org_key} set {set_spec}')
        if verbosity > 1:
            print(f'Harvesting {org_key} set {set_spec}')

        # Sickle harvester
        harvester = sickle.Sickle(oai, iterator=OAIItemIterator, encoding='utf-8')
        harvester.class_mapping['ListRecords'] = SickleRecord

        records = harvester.ListRecords(set=set_spec, metadataPrefix=metadata_prefix, ignore_deleted=True)

        # write XML
        with open(os.path.join(write_path, org_key, f'{set_spec.replace(":", "_")}_{datetime.date.today()}.xml'), 'w',
                  encoding='utf-8') as fp:
            logger.debug(f'Writing records {fp.name}')
            fp.write('<oai>')
            for record in records:
                fp.write(record.raw)
            fp.write('</oai>')

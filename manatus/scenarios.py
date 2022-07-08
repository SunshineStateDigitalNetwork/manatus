"""
Source document parsers and record classes for returning XML or JSON document values
"""
import json
import logging
import re

import requests
from pymods import OAIReader

dc = '{http://purl.org/dc/elements/1.1/}'
dcterms = '{http://purl.org/dc/terms/}'

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class Scenario:
    """
    Scenario superclass defining private dunder methods

    :meta private:

    """

    def __init__(self, records):
        self.records = records

    def __getitem__(self, item):
        return self.records[item]

    def __iter__(self):
        for record in self.records:
            yield record

    def __len__(self):
        return len(self.records)

    def __str__(self):
        return f'{self.__class__.__name__}'


class XMLScenario(Scenario):

    def __init__(self, xml_path):
        """
        Generic class for parsing OIA-PMH XML. Serves as a iterable container for :py:mod:`pymods.Records`
        at self.records

        :param str xml_path: Path to an XML file of OAI-PMH records

        """
        logger.debug(f"Loading {xml_path} with {__name__}.XMLScenario")
        self.records = []
        with open(xml_path, encoding='utf-8') as data_in:
            records = OAIReader(data_in)
            for record in records:

                # deleted record handling for repox
                try:
                    if 'deleted' in record.attrib.keys():
                        if record.attrib['deleted'] == 'true':
                            continue
                except AttributeError:
                    pass

                # deleted record handling for OAI-PMH
                try:
                    if 'status' in record.find('./{*}header').attrib.keys():
                        if record.find('./{*}header').attrib['status'] == 'deleted':
                            continue
                except AttributeError:
                    pass

                self.records.append(record)
        Scenario.__init__(self, self.records)


class SSDNDC(XMLScenario):

    def __init__(self, xml_path):
        """
        Parser and container for :py:class:`manatus.DC_Record` records

        :param str xml_path: Path to an XML file of oai_dc records

        """
        logger.debug(f"Loading {xml_path} with {__name__}.SSDNDC")
        XMLScenario.__init__(self, xml_path)
        self.records = [DCRecord(record) for record in self.records]


class SSDNQDC(XMLScenario):

    def __init__(self, xml_path):
        """
        Parser and container for :py:class:`manatus.QDC_Record` records

        :param str xml_path: Path to an XML file of oai_qdc records

        """
        logger.debug(f"Loading {xml_path} with {__name__}.SSDNQDC")
        XMLScenario.__init__(self, xml_path)
        self.records = [QDCRecord(record) for record in self.records]


class SSDNMODS(XMLScenario):

    def __init__(self, xml_path):
        """
        Parser and container for :py:class:`manatus.MODS_Record` records

        :param str xml_path: Path to an XML file of OAI-PMH MODS records

        """
        logger.debug(f"Loading {xml_path} with {__name__}.SSDNMODS")
        XMLScenario.__init__(self, xml_path)
        self.records = [MODSRecord(record) for record in self.records]


class BepressDC(SSDNDC):

    def __init__(self, xml_path):
        """
        Bepress specific parser for :py:class:`BepressDCRecord`

        :param str xml_path: Path to an XML file of BePress DC records

        """
        logger.debug(f"Loading {xml_path} with {__name__}.BepressDC")
        SSDNDC.__init__(self, xml_path)
        self.records = [BepressDCRecord(record) for record in self.records]


class SSDNPartnerMODSScenario(SSDNMODS):

    def __init__(self, xml_path):
        """
        Parser and container for :py:class:`SSDNMODSRecord` records


        :param str xml_path: Path to an XML file of OAI-PMH MODS records

        """
        logger.debug(f"Loading {xml_path} with {__name__}.SSDNPartnerMODSScenario")
        SSDNMODS.__init__(self, xml_path)
        self.records = [SSDNMODSRecord(record) for record in self.records]


class APIScenario(Scenario):

    def __init__(self, url, record_key, count_key=None, page_key=None):
        """
        Generic scenario class for API calls

        :param str url: API URL
        :param record_key: For navigating paged content
        :param count_key: For navigating paged content
        :param page_key: For navigating paged content

        """
        logger.debug(f"Running {__name__}.APIScenario query to {url}")
        r = requests.get(url)
        data = json.loads(r.text.replace('\\u00a0', ''))
        if count_key:
            record_count = [v for v in self._item_generator(data, count_key)][0]
        self.records = [record for record in self._item_generator(data, record_key)]
        if record_count:
            page = 1
            while len(self.records) < record_count:
                page += 1
                data = json.loads(requests.get(url + f'&{page_key}={page}').text.replace('\\u00a0', ''))
                self.records = self.records + [record for record in self._item_generator(data, record_key)]
                continue
        Scenario.__init__(self, self.records)

    def _item_generator(self, json_input, lookup_key):
        if isinstance(json_input, dict):
            for k, v in json_input.items():
                if k == lookup_key:
                    if isinstance(v, list):
                        for i in v:
                            yield i
                    else:
                        yield v
                else:
                    yield from self._item_generator(v, lookup_key)
        elif isinstance(json_input, list):
            for item in json_input:
                yield from self._item_generator(item, lookup_key)


class InternetArchive(APIScenario):

    def __init__(self, collection):
        """
        Scenario class for calls to the Internet Archive's API

        :param str collection: Designation of Internet Archive collection to pull metadata for

        """
        url = f'https://archive.org/advancedsearch.php?q=collection:{collection}&output=json&rows=100'
        logger.debug(f"Running {__name__}.InternetArchive query to {url}")
        APIScenario.__init__(self, url, 'docs', 'numFound', 'page')
        self.records = [InternetArchiveRecord(record) for record in self.records]


class ManatusRecord:

    def __init__(self, record):
        """
        Generic class for single records

        :param record: Generic record

        """
        self.record = record

    def __str__(self):
        return f'{self.__class__.__name__}, {self.harvest_id}'


class XMLRecord(ManatusRecord):

    def __init__(self, record):
        """
        Generic class for single records. Makes record OAI-PMH identifier available through
        :py:attr:`self.harvest_id` attribute

        :param record: Generic record

        """
        ManatusRecord.__init__(self, record)
        self.harvest_id = self.record.oai_urn


class DCRecord(XMLRecord):

    def __init__(self, record):
        """
        Dublin Core record class. Element text is available through ``self.<element>`` properties

        :param record: oai_dc record

        """
        XMLRecord.__init__(self, record)
        self.oai_urn = self.record.oai_urn
        self.metadata = self.record.metadata

    def _value_list(self, elem, ns):
        try:
            return [value.strip(':').strip(' ') for value in
                    self.record.metadata.get_element('.//{0}{1}'.format(ns, elem), delimiter=';')
                    if value]
        except TypeError:
            return None

    def _clean_mark_up(self, text):
        mark_up_re = re.compile('<.*?>')
        new_line_re = re.compile('\n')
        clean_text = re.sub(mark_up_re, '', text)
        clean_text = re.sub(new_line_re, ' ', clean_text)
        return clean_text

    @property
    def contributor(self):
        """dc:contributor"""
        return self._value_list('contributor', dc)

    @property
    def creator(self):
        """dc:contributor"""
        return self._value_list('creator', dc)

    @property
    def date(self):
        """dc:date"""
        return self._value_list('date', dc)

    @property
    def description(self):
        """dc:description"""
        return self._value_list('description', dc)

    @property
    def format(self):
        """dc:format"""
        return self._value_list('format', dc)

    @property
    def identifier(self):
        """dc:identifier"""
        return self._value_list('identifier', dc)

    @property
    def language(self):
        """dc:language"""
        return self._value_list('language', dc)

    @property
    def place(self):
        """dc:coverage"""
        return self._value_list('coverage', dc)

    @property
    def publisher(self):
        """dc:publisher"""
        return self._value_list('publisher', dc)

    @property
    def rights(self):
        """dc:rights"""
        return self._value_list('rights', dc)

    @property
    def subject(self):
        """dc:subject"""
        try:
            return [re.sub("\( lcsh \)$", '', sub).strip(' ') for sub in
                    self.record.metadata.get_element('.//{0}subject'.format(dc), delimiter=';') if sub]
        except TypeError:
            return None

    @property
    def title(self):
        """dc:title"""
        return self._value_list('title', dc)

    @property
    def thumbnail(self):
        """
        some repositories implement a non-standard dc:identifier.thumbnail element for thumbnail URLs

        :return: thumbnail URL or None

        """
        try:
            return self.record.metadata.get_element('.//{0}identifier.thumbnail'.format(dc))[0]
        except TypeError:
            return None

    @property
    def type(self):
        """dc:type"""
        return self._value_list('type', dc)


class QDCRecord(DCRecord):

    def __init__(self, record):
        """
        Qualified Dublin Core record class. Element text is available through ``self.<element>`` properties.
        Subclass of :py:class:`DC_Record`

        :param record: oai_qdc record

        """
        DCRecord.__init__(self, record)

    @property
    def abstract(self):
        """dcterms:abstract"""
        return self._value_list('abstract', dcterms)

    @property
    def alternative(self):
        """dcterms:alternative"""
        return self._value_list('alternative', dcterms)

    @property
    def is_part_of(self):
        """dcterms:isPartOf"""
        return self._value_list('isPartOf', dcterms)

    @property
    def date(self):
        """
        General date parser returning the first date encountered in the order ``dcterms:created``, ``dcterms:issued``,
        ``dcterms:date``, ``dc:date``, ``dcterms:available``, ``dcterms:dateAccepted``, ``dcterms:dateCopyrighted``,
        ``dcterms:dateSubmitted``

        For more customizable access to dates, use the :py:attr:`QDCRecord.dates` property

        """
        date = None
        date_list = (f'{dcterms}created', f'{dcterms}issued', f'{dcterms}date', f'{dc}date', f'{dcterms}available',
                     f'{dcterms}dateAccepted', f'{dcterms}dateCopyrighted', f'{dcterms}dateSubmitted')
        for d in date_list:
            date = self.record.metadata.get_element(f'.//{d}')
            if date:
                break
        return date

    @property
    def dates(self):
        """
        Customizable handling for date type elements in dcterms
        Not Implemented

        """
        return NotImplemented

    @property
    def extent(self):
        """dcterms:extent"""
        return self._value_list('extent', dcterms)

    @property
    def medium(self):
        """dcterms:medium"""
        return self._value_list('medium', dcterms)

    @property
    def place(self):
        """dcterms:spatial"""
        return self._value_list('spatial', dcterms)

    @property
    def requires(self):
        """dcterms:requires"""
        return self._value_list('requires', dcterms)


class MODSRecord(XMLRecord):

    def __init__(self, record):
        """
        MODS record class making MAPv4 elements available through ``self.<element>`` properties

        :param record: OAI-PMH MODS record

        """
        XMLRecord.__init__(self, record)
        self.oai_urn = self.record.oai_urn
        self.metadata = self.record.metadata

    @property
    def alternative(self):
        """List of alternative titles"""
        return self.record.metadata.titles[1:]

    @property
    def collection(self):
        """Name of archival collection or None"""
        try:
            return self.record.metadata.collection
        except (AttributeError, TypeError):
            return None

    @property
    def contributor(self):
        """
        List of contributor names as dicts: ``[{"@id": "Name URI", "name": "Name text"}, ...]``

        """
        return [{"@id": name.uri, "name": name.text} if name.uri else {"name": name.text} for name in
                filter(self._creator_filter, self.record.metadata.names)]

    def _creator_filter(self, name):
        if name.role.text != 'Creator' and name.role.code != 'cre' and name.role.text is not None and name.role.code is not None:
            return name

    @property
    def creator(self):
        """
        List of creator names as dicts: ``[{"@id": "Name URI", "name": "Name text"}, ...]``

        """
        return [{"@id": name.uri, "name": name.text} if name.uri else {"name": name.text} for name in
                self.record.metadata.get_creators]

    @property
    def date(self):
        """
        Date returned as a dict: ``{"displayDate": "date text", "begin": "start date", "end": "end date"}``

        """
        if self.record.metadata.dates:
            date = self.record.metadata.dates[0].text
            if ' - ' in date:
                return {"displayDate": date,
                        "begin": date[0:4],
                        "end": date[-4:]}
            else:
                return {"displayDate": date,
                        "begin": date,
                        "end": date}

    @property
    def description(self):
        """List of abstracts"""
        return [abstract.text for abstract in self.record.metadata.abstract]

    @property
    def extent(self):
        """Extent"""
        return self.record.metadata.extent

    @property
    def format(self):
        """
        List of genres as dicts: ``[{"@id": "Genre URI", "name": "Genre text"}, ...]``

        """
        return [{'name': genre.text, '@id': genre.uri} if genre.uri else {'name': genre.text} for genre in
                self.record.metadata.genre]

    @property
    def geographic_code(self):
        """Geographic code"""
        return self.record.metadata.geographic_code

    @property
    def identifier(self):
        """PURL"""
        return self.record.metadata.purl[0]

    @property
    def iid(self):
        """IID identifier"""
        return self.record.metadata.iid

    @property
    def language(self):
        """
        List of languages as dicts: ``[{"name": "Language text", "iso_639_3": "Language code"}, ...]``

        """
        return [{"name": lang.text, "iso_639_3": lang.code} for lang in self.record.metadata.language]

    @property
    def place(self):
        """
        Place names as ``{"name": "Place text"}``

        """
        for subject in self.record.metadata.subjects:
            for c in subject.elem.getchildren():
                if 'eographic' in c.tag:
                    return {"name": subject.text}

    @property
    def pid(self):
        """PID"""
        if self.record.metadata.pid:
            return self.record.metadata.pid
        else:
            return self.record.oai_urn.split(':')[-1].replace('_', ':')

    @property
    def publisher(self):
        """Publisher"""
        return self.record.metadata.publisher

    # sourceResource.relation

    # sourceResource.isReplacedBy

    # sourceResource.replaces

    @property
    def rights(self):
        """Rights URI if available, otherwise rights text"""
        for rights in self.record.metadata.rights:
            if rights.uri:
                return rights.uri
            else:
                return rights.text

    @property
    def subject(self):
        """
        List of subjects as dicts: ``[{"@id": "Subject URI", "name": "Subject text"}, ...]``

        """
        return [{"@id": subject.uri, "name": subject.text}
                if subject.uri
                else {"name": subject.text}
                for subject in self.record.metadata.subjects if
                'eographic' not in subject.elem.tag]

    @property
    def title(self):
        """Title"""
        return self.record.metadata.titles[0]

    @property
    def type(self):
        """Type of resource"""
        return self.record.metadata.type_of_resource


class BepressDCRecord(DCRecord):

    def __init__(self, record):
        """
        Extension of :py:class:`DCRecord` class to expose BePress specific elements
        """
        DCRecord.__init__(self, record)

    @property
    def description(self):
        """dc:description.abstract"""
        try:
            return [re.sub(' {2}', ' ', self._clean_mark_up(abstract)).strip(' ') for abstract in
                    self.record.metadata.get_element('.//{0}description.abstract'.format(dc), delimiter=';')
                    if abstract]
        except TypeError:
            return None

    @property
    def date(self):
        """dc:date.created"""
        return re.sub('T[\\d*:]*Z', '', self._value_list('date.created', dc)[0])


class SSDNMODSRecord(MODSRecord):

    def __init__(self, record):
        """
        Extension of :py:class:`MODSRecord`
        """
        MODSRecord.__init__(self, record)

    @property
    def creator(self):
        # Case 1: Name has either role.text=Creator or role.code=cre
        # Case 2: Name has incorrectly formed role.text=creator
        # Case 3: Name has neither role.text nor role.code
        names = self.record.metadata.get_creators + self.record.metadata.get_names(
            role="creator") + self.record.metadata.get_names(role=None)
        return [{"@id": name.uri, "name": name.text} if name.uri else {"name": name.text} for name in
                names]

    @property
    def rights(self):
        # TODO: this is real ugly and will break if there are no RS.org URIs to return
        for rights in self.record.metadata.rights:
            if rights.uri:
                return rights.uri
            else:
                if rights.text.startswith('http'):
                    return rights.text
                else:
                    continue


class InternetArchiveRecord(ManatusRecord):

    def __init__(self, record):
        """
        Internet Archive record class
        """
        ManatusRecord.__init__(self, record)
        self.harvest_id = f'ia:{self.identifier}'

    @property
    def identifier(self):
        """Expose record identifier"""
        return self.record['identifier']

    def __getattr__(self, item):
        return self.record[item]

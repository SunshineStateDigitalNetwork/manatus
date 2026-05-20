"""
Source document parsers and record classes for returning XML or JSON document values
"""
import json
import logging
import re

import requests
from manatus.exceptions import APIScenarioStatusCodeException
from pymods import OAIReader

dc = '{http://purl.org/dc/elements/1.1/}'
dcterms = '{http://purl.org/dc/terms/}'
marc = '{http://www.loc.gov/MARC21/slim}'

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


class MARCXML(XMLScenario):

    def __init__(self, xml_path):
        """
        Parser and container for :py:class:`MARCXMLRecord records

        :param str xml_path: Path to an XML file of OAI-PMH MARCXML records

        """
        logger.debug(f"Loading {xml_path} with {__name__}.MARCXML")
        XMLScenario.__init__(self, xml_path)
        self.records = [MARCXMLRecord(record) for record in self.records]


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
        if r.status_code == 200:
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
        else:
            raise APIScenarioStatusCodeException(f"{r.status_code} status code returned for URL: {url}")


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
            return [self._clean_text(value) for value in
                    self.record.metadata.get_element('.//{0}{1}'.format(ns, elem), delimiter=';')
                    if value]
        except TypeError:
            return None

    def _clean_text(self, text):
        mark_up_re = re.compile('<.*?>')
        new_line_re = re.compile('\n')
        date_time_code_re = re.compile('T\\d{2}:\\d{2}:\\d{2}Z')

        # remove extraneous leading and trailing characters
        clean_text = text.strip(':').strip(' ')

        # remove markup
        clean_text = re.sub(mark_up_re, '', clean_text)

        # remove newlines
        clean_text = re.sub(new_line_re, ' ', clean_text)

        # remove timecode data trailing a date
        clean_text = re.sub(date_time_code_re, '', clean_text)
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
    def source(self):
        """dc:source"""
        return self._value_list('source', dc)

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
            return [re.sub(' {2}', ' ', self._clean_text(abstract)).strip(' ') for abstract in
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
        # TODO: this is real ugly
        rights_info = {}
        for rights in self.record.metadata.rights:
            if rights.uri:
                rights_info['uri'] = rights.uri
            else:
                if rights.text.startswith('http://rightsstatements'):
                    rights_info['uri'] = rights.text
                else:
                    rights_info['text'] = rights.text
            continue
        if 'uri' in rights_info.keys():
            return rights_info['uri']
        elif 'text' in rights_info.keys():
            return rights_info['text']
        else:
            return None


class MARCXMLRecord(XMLRecord):
    """
    MARCXML record class making MAPv4 elements available through ``self.<element>`` properties

    :param record: OAI-PMH MARCXML record
    """

    _URI_RE = re.compile(r'^(https?://|urn:|info:)')

    def __init__(self, record):
        super().__init__(record)
        self.oai_urn = self.record.oai_urn
        self.metadata = self.record.metadata
        self.elem = self._coerce_record_elem(self.record)

    # Core element coercion/helpers
    def _coerce_record_elem(self, md):
        """
        Try to get the actual MARCXML <record> element.
        Works if md is already an Element, or a wrapper with .elem/.record, etc.
        """
        root = md

        # common wrapper patterns
        for attr in ("elem", "record", "root"):
            if hasattr(root, attr):
                try:
                    root = getattr(root, attr)
                except Exception:
                    pass

        # If we’re already at <record>, great. Otherwise try to find it.
        try:
            if getattr(root, "tag", None) == f"{marc}record" or getattr(root, "tag", None) == "record":
                return root
        except Exception:
            pass

        # Try namespace-qualified record first, then unqualified fallback
        try:
            rec = root.find(f".//{marc}record")
            print('found record')
            if rec is not None:
                return rec
        except Exception:
            pass

        try:
            rec = root.find(".//record")
            if rec is not None:
                return rec
        except Exception:
            pass

        # Last resort: return what we got; helpers may still work if it’s record-ish
        return root

    def datafields(self, tag=None):
        """Return list of <datafield> elements, optionally filtered by @tag."""
        if tag is None:
            return self.record.findall(f".//{marc}datafield")
        return self.record.findall(f".//{marc}datafield[@tag='{tag}']")


    def controlfields(self, tag=None):
        """Return list of <controlfield> elements, optionally filtered by @tag."""
        if tag is None:
            return self.elem.findall(f".//{marc}controlfield")
        return self.elem.findall(f".//{marc}controlfield[@tag='{tag}']")

    def subfields(self, field_elem, codes=None):
        """
        Return list of <subfield> elements from a datafield, optionally filtered by code(s).
        `codes` can be a string ('a') or iterable ('ab').
        """
        sfs = field_elem.findall(f"{marc}subfield")
        if not codes:
            return sfs
        if isinstance(codes, str):
            codes = set(codes)
        else:
            codes = set(codes)
        return [sf for sf in sfs if sf.get("code") in codes]

    def _sf_text(self, field_elem, code):
        """First subfield text for code, cleaned."""
        for sf in self.subfields(field_elem, codes=code):
            txt = (sf.text or "").strip()
            if txt:
                return self._clean_text(txt)
        return None

    def _sf_texts(self, field_elem, codes):
        """All subfield texts for given code(s), cleaned, in-order."""
        return [self._clean_text((sf.text or "").strip())
                for sf in self.subfields(field_elem, codes=codes)
                if (sf.text or "").strip()]

    def _clean_text(self, text):
        """Light cleanup similar to DCRecord._clean_text, but MARC-friendly."""
        text = re.sub(r"\s+", " ", text).strip()
        # common trailing separators when joining MARC title parts
        return text

    def _clean_title_punct(self, title):
        """
        Remove some MARC-ish trailing punctuation introduced by concatenation.
        Keep this conservative; you can tune based on local data.
        """
        title = re.sub(r"\s+", " ", title).strip()
        title = title.rstrip(" /")
        title = title.rstrip(" :")
        title = title.rstrip(" ,")
        title = title.strip()
        return title or None

    def _name_fields(self, tags):
        out = []
        for tag in tags:
            for f in self.datafields(tag):
                parts = []
                for code in ("a", "b", "c", "d", "q"):
                    parts.extend(self._sf_texts(f, code))
                if parts:
                    out.append(" ".join(parts).rstrip(" ,.;"))
        return out or None

    @property
    def contributor(self):
        return self._name_fields(("700", "710", "711", "720"))

    @property
    def creator(self):
        return self._name_fields(("100", "110", "111"))

    @property
    def date(self):
        for tag in ("264", "260"):
            for f in self.datafields(tag):
                c = self._sf_text(f, "c")
                if c:
                    return c.strip("[]().")

        cf008 = self.controlfield_008()
        if cf008 and len(cf008) >= 11:
            year = cf008[7:11]
            if year.isdigit():
                return year

        return None

    @property
    def description(self):
        for f in self.datafields("520"):
            a = self._sf_text(f, "a")
            if a:
                return a

        # fallback: subtitle-ish description
        for f in self.datafields("245"):
            b = self._sf_text(f, "b")
            if b:
                return b

        return None

    @property
    def format(self):
        for f in self.datafields("300"):
            parts = []
            for code in ("a", "b", "c"):
                parts.extend(self._sf_texts(f, code))
            if parts:
                return " ".join(parts).strip(' ;')

        for tag in ("337", "338", "530"):
            for f in self.datafields(tag):
                a = self._sf_text(f, "a")
                if a:
                    return a.strip(' ;')

        return None

    @property
    def identifier(self):
        for f in self.datafields("856"):
            for u in self._sf_texts(f, "u"):
                if self._URI_RE.match(u):
                    return u

        for tag in ("020", "022"):
            for f in self.datafields(tag):
                a = self._sf_text(f, "a")
                if a:
                    return a.split()[0]

        return self.oai_urn

    @property
    def language(self):
        for f in self.datafields("041"):
            for a in self._sf_texts(f, "a"):
                return a

        cf008 = self.controlfield_008()
        if cf008 and len(cf008) >= 38:
            lang = cf008[35:38]
            if lang.strip():
                return lang

        return None

    @property
    def place(self):
        for tag in ("264", "260"):
            for f in self.datafields(tag):
                a = self._sf_text(f, "a")
                if a:
                    return a.rstrip(" :,;")

        return None

    @property
    def publisher(self):
        for tag in ("264", "260"):
            for f in self.datafields(tag):
                b = self._sf_text(f, "b")
                if b:
                    return b.rstrip(" :,;")

        return None

    @property
    def rights(self):
        """
        Rights: prefer URI forms if present, else textual statement.
        Checks common MARC fields:
          - 540 (Terms Governing Use and Reproduction): $u for URI, $a for text
          - 542 (Information Relating to Copyright Status): $u for URI, $l/$d etc. (fallback)
          - 856 (Electronic Location and Access): $u if it looks like a rights URI
          - 506 (Restrictions on Access): $a fallback
        """
        # 540: $u then $a
        for f in self.datafields("540"):
            for u in self._sf_texts(f, "u"):
                if self._URI_RE.match(u):
                    return u
            a = self._sf_text(f, "a")
            if a:
                # if someone shoved a URI into $a
                if self._URI_RE.match(a):
                    return a
                return a

        # 542: $u then any reasonable text-ish bits
        for f in self.datafields("542"):
            for u in self._sf_texts(f, "u"):
                if self._URI_RE.match(u):
                    return u
            for code in ("l", "d", "f", "g", "n"):  # conservative fallbacks
                txt = self._sf_text(f, code)
                if txt:
                    return txt

        # 856: look for rights-ish links (rightsstatements, creativecommons, etc.)
        for f in self.datafields("856"):
            for u in self._sf_texts(f, "u"):
                if self._URI_RE.match(u) and (
                    "rightsstatements.org" in u
                    or "creativecommons.org" in u
                    or "/rights" in u
                ):
                    return u

        # 506: $a fallback
        for f in self.datafields("506"):
            a = self._sf_text(f, "a")
            if a:
                return a

        return None

    @property
    def is_shown_at(self):
        """
        Landing page URL (prefer 856 with no $y 'thumbnail' semantics).
        """
        for f in self.datafields("856"):
            u = self._sf_text(f, "u")
            if u and self._URI_RE.match(u):
                return u.split('/files')[0]
        return None

    @property
    def subject(self):
        """
        Subjects as list of dicts:
          [{'name': 'Topic -- Subdivision', '@id': 'http://…'}, ...]
        Pulls from 600/610/611/630/648/650/655.
        Uses $1 (URI) or $0 (control/URI) if it looks like a URI-ish token.
        """
        tags = ("600", "610", "611", "630", "648", "650", "655")
        out = []

        for tag in tags:
            for f in self.datafields(tag):
                # authority identifiers
                uri = None
                for candidate in self._sf_texts(f, "1") + self._sf_texts(f, "0"):
                    if self._URI_RE.match(candidate):
                        uri = candidate
                        break

                # build label: keep MARC subdivision semantics for x/y/z/v
                pieces = []
                subdivisions = []

                for sf in self.subfields(f):
                    code = sf.get("code")
                    txt = (sf.text or "").strip()
                    if not txt:
                        continue
                    txt = self._clean_text(txt)

                    # skip control-ish and non-display subfields
                    if code in {"0", "1", "2", "3", "4", "5", "6", "7", "8", "w"}:
                        continue

                    if code in {"x", "y", "z", "v"}:
                        subdivisions.append(txt)
                    else:
                        pieces.append(txt)

                if not pieces and not subdivisions:
                    continue

                label = " ".join(pieces).strip()
                if subdivisions:
                    label = f"{label} -- " + " -- ".join(subdivisions) if label else " -- ".join(subdivisions)

                label = label.strip(" .;/,:")
                if label.endswith(" ( lcsh )"):
                    label = label[:-9]
                if not label:
                    continue

                out.append({"@id": uri, "name": label} if uri else {"name": label})

        return out or None

    @property
    def title(self):
        """
        Primary title from 245 (a, b, n, p). Returns a string or None.
        """
        titles = self.titles  # uses helper below
        return titles[0] if titles else None

    @property
    def titles(self):
        """
        All 245 titles (a, b, n, p), one per 245 field, in record order.
        This aligns with your earlier “all 245 values” need.
        """
        out = []
        for f in self.datafields("245"):
            parts = []
            for code in ("a", "b", "n", "p"):
                parts.extend(self._sf_texts(f, code))
            if parts:
                out.append(self._clean_title_punct(" ".join(parts)))
        return [t for t in out if t]

    @property
    def type(self):
        """
        Type of resource:
          - Prefer RDA content type in 336$a (often already 'text', 'still image', etc.)
          - Else map leader/06 to a coarse type string
        """
        # 336$a
        for f in self.datafields("336"):
            a = self._sf_text(f, "a")
            if a:
                return a

        # leader mapping
        leader_elems = self.elem.findall(f".//{marc}leader")
        if leader_elems and (leader_elems[0].text or ""):
            leader = leader_elems[0].text
            if len(leader) > 6:
                t06 = leader[6]
                return {
                    "a": "text",
                    "c": "notated music",
                    "d": "notated music",
                    "e": "cartographic",
                    "f": "cartographic",
                    "g": "moving image",
                    "i": "sound recording",
                    "j": "sound recording",
                    "k": "still image",
                    "m": "software, multimedia",
                    "o": "kit",
                    "p": "mixed material",
                    "r": "three-dimensional object",
                    "t": "manuscript text",
                }.get(t06, None)

        return None

    @property
    def thumbnail(self):
        for f in self.datafields("694"):
            y = self._sf_text(f, "y")
            if y and (
                    "thumbnail" in y.lower()
                    or "preview" in y.lower()
                    or y.lower().endswith((".jpg", ".jpeg", ".png"))
            ):
                return y
        return None

    def controlfield_008(self):
        """
        Optional helper to access 008 as-is (useful when debugging spacing/normalization issues)
        """
        cfs = self.controlfields("008")
        return (cfs[0].text if cfs and cfs[0].text else None)


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

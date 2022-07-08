"""
Container classes for the resulting DPLA MAPv4 JSON-LD document(s)
"""

import json
import logging
import os
from datetime import date
from json import JSONEncoder
from os.path import exists, join, splitext

from manatus.exceptions import SourceResourceRequiredElementException, RecordGroupFileExtensionError

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class Record(object):

    def __init__(self):
        """
        Generic object class. Provides some JSON-like methods
        """
        object.__init__(self)

    def __contains__(self, item):
        if item in self.__dict__.keys():
            return True
        else:
            return False

    def __iter__(self):
        for k in self.__dict__.keys():
            yield k

    def __delitem__(self, key):
        if key in self.__dict__.keys():
            del self.__dict__[key]
        else:
            raise KeyError

    def __getitem__(self, item):
        if item in self.__dict__.keys():
            return self.__dict__[item]
        else:
            raise KeyError

    def __setattr__(self, key, value):
        if value:
            self.__dict__[key] = value

    def __setitem__(self, key, value):
        if value:
            self.__dict__[key] = value

    def __str__(self):
        try:
            return f'{self.__class__.__name__}, {self.__dict__["identifier"]}'
        except KeyError:
            return f'{self.__repr__()}'

    def dumps(self, indent=None):
        """
        Return object's JSON representation. Useful for debugging

        :param indent: padding for pretty printing
        :type indent: integer or None
        :return: record JSON
        :rtype: str
        :meta hide-value:

        """
        return json.dumps(self.__dict__, indent=indent)

    @property
    def data(self):
        """Property for raw access to record's data at ``self.__dict__``"""
        return self.__dict__

    def keys(self):
        """JSON key iterator"""
        for k in self.__dict__.keys():
            yield k


class DPLARecord(Record):

    def __init__(self, record=None):
        """
        DPLA MAPv4 record class. Serves as the JSON-LD wrapper for :py:class:`SourceResource`. Includes some default
        attributes for convenience.
        """
        Record.__init__(self)
        if record:
            try:
                for k, v in json.loads(record).items():
                    self.__dict__[k] = v
            except TypeError:
                for k, v in record.items():
                    self.__dict__[k] = v
        else:
            self.__dict__['@context'] = "http://api.dp.la/items/context"
            self.aggregatedCHO = "#sourceResource"
            self.preview = ""


class SourceResource(Record):

    def __init__(self):
        """
        DPLA MAPv4 sourceResource record class

        :raises SourceResourceRequiredElementException: if either required elements 'rights' or 'title' are missing

        """
        Record.__init__(self)

    def __setattr__(self, key, value):
        if key == 'rights' and not value:
            raise SourceResourceRequiredElementException(self, 'Rights')
        elif key == 'title' and not value:
            raise SourceResourceRequiredElementException(self, 'Title')
        elif value:
            self.__dict__[key] = value


class RecordGroup(object):

    def __init__(self, records=None):
        """
        List container for :py:class:`scenarios.ManatusRecord` records

        :param list records: List of :py:class:`scenarios.ManatusRecord` records or subclassed records

        """
        object.__init__(self)
        if records:
            self.records = self.records + [DPLARecord(rec) for rec in records]
        else:
            self.records = []

    def __iter__(self):
        for r in self.records:
            yield r

    def __len__(self):
        return len(self.records)

    def append(self, record):
        self.records.append(record)

    def load(self, fp):
        """
        Load record group from file

        :param str fp: File path
        :return: :py:class:`manatus.source_resource.RecordGroup`
        :raises RecordGroupFileExtensionError: if the file does not have a `.json` or `.jsonl` extension
        :raises FileNotFoundError: is the specified file doesn't exist
        """
        if exists(fp):
            with open(fp) as f:
                if splitext(fp)[-1] == '.jsonl':
                    for line in f:
                        self.append(DPLARecord(line))
                elif splitext(fp)[-1] == '.json':
                    recs = json.load(f)
                    for rec in recs:
                        self.append(DPLARecord(rec))
                else:
                    raise RecordGroupFileExtensionError(fp)
            return self
        else:
            raise FileNotFoundError

    def write_json(self, fp, prefix=None, pretty_print=False):
        """

        :param str fp:
        :param str prefix:
        :param bool pretty_print:
        :return:
        """
        if not exists(fp):
            os.mkdir(fp)
        if prefix:
            f = f'{prefix}-{date.today()}'
        else:
            f = f'{date.today()}'
        if exists(join(fp, f'{f}.json')):
            with open(join(fp, f'{f}.json'), 'r', encoding='utf-8') as json_in:
                data = json.load(json_in)
                for record in data:
                    self.records.append(record)
            with open(join(fp, f'{f}.json'), 'w', encoding='utf-8') as json_out:
                if pretty_print:
                    json.dump(self.records, json_out, indent=2, cls=DPLARecordEncoder)
                else:
                    json.dump(self.records, json_out, cls=DPLARecordEncoder)
        else:
            with open(join(fp, f'{f}.json'), 'w', encoding='utf-8') as json_out:
                if pretty_print:
                    json.dump(self.records, json_out, indent=2, cls=DPLARecordEncoder)
                else:
                    json.dump(self.records, json_out, cls=DPLARecordEncoder)

    def write_jsonl(self, fp, prefix=None):
        """

        :param str fp:
        :param str prefix:
        :return:
        """
        if not exists(fp):
            os.mkdir(fp)
        if prefix:
            f = f'{prefix}-{date.today()}'
        else:
            f = f'{date.today()}'
        with open(join(fp, f'{f}.jsonl'), 'a', encoding='utf-8', newline='\n') as json_out:
            for rec in self.records:
                json_out.write(json.dumps(rec, cls=DPLARecordEncoder) + '\n')

    def print(self, indent=None):
        for rec in self.records:
            print(json.dumps(rec.data, indent=indent, cls=DPLARecordEncoder))


class DPLARecordEncoder(JSONEncoder):

    def default(self, o):
        return o.__dict__


def dedupe_record_group():
    pass

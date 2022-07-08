class DataProvider(object):
    __slots__ = ('__dict__', 'key', 'data_address', 'set_list', 'metadata_prefix', 'scenario', 'map', 'data_provider',
                 'intermediate_provider')

    def __init__(self):
        """
        DataProvider object model.

        .. py:attribute:: key
           :type: str

           Unique string identifying organization providing the data

        .. py:attribute:: data_address
           :type: str

           API URL such as an OAI endpoint where data is accessible for harvesting

        .. py:attribute:: set_list
           :type: list

           List of record sets to harvest (i.e. OAI setSpecs)

        .. py:attribute:: metadata_prefix
           :type: str

           A metadata parameter to be used in calls to a harvestable API (required for OAI-PMH)

        .. py:attribute:: scenario
           :type: str

           Parser class from :py:mod:`manatus.scenarios` manatus uses to encapsulate records

        .. py:attribute:: map
           :type: str

           Name of function used to map records from OAI-PMH into MAPv4. Can come from :py:mod:`manatus.maps` or be
           defined elsewhere such as a custom map from the Custom Map Directory defined in ``manatus.cfg``


        .. py:attribute:: data_provider
           :type: str

           Name of organization providing the data (dpla.dataProvider)

        .. py:attribute:: intermediate_provider
           :type: str

           *optional* Name of organization serving as an intermediary data provider (dpla.intermediateProvider)

        """
        object.__init__(self)

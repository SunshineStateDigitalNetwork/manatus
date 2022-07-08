.. _anchor02:

Configuring manatus
===================

Manatus uses data from configuration files to direct harvests and transformations.

Manatus looks for configuration files in a three step process

1. envar

    setting envars

2. home dir....

3. mod dir ...

Auto build from CLI

The status subcommand of the CLI can be used to view located configs, ENtries can be added and deleted as well from the CLI.



manatus.cfg
-----------

Main program configuration. Multiple profiles can be defined with ``[<profile name>]``

**CONFIG ENTRIES**

* ``InFilePath`` - path to input files
* ``OutFilePath`` - path to write output files to
* ``OutFilePrefix`` - *(optional)* prefix written to output file name
* ``CustomMapPath`` - path to custom maps directory
* ``CustomMapTestPath`` - path to custom map testing file
* ``CustomMapTestName`` - name of custom maps testing file
* ``LogPath`` - file path for writing log files
* ``LogLevel`` - level to set the default logger
* ``Provider`` - provider name as it will appear in ``edm:provider``

manatus_harvests.cfg
--------------------

Contains data about harvest data providers. Each provider begins with a section header ``[<provider>]``

**CONFIG ENTRIES FOR EACH SECTION**

* ``oaiendpoint`` - URL where data is available (OAI or API)
* ``setlist`` - comma separated list of setSpecs
* ``metadataprefix`` - metadata format to harvest

manatus_scenarios.cfg
---------------------

Provides manatus information required during the transformation process. Each provider begins with a section header ``[<provider>]``

**CONFIG ENTRIES FOR EACH SECTION**

* ``scenario`` - :py:mod:`manatus.scenario` to apply to data provider
* ``map`` - name of transformation map to apply to data
* ``dataprovider`` - data provider's name as it will appear in the ``edm:dataProvider`` element
* ``intermediatedataprovider`` - *(optional)* intermediate data provider's name as it will appear in the ``dpla:intermediateDataProvider`` element

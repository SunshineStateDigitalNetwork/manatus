manatus.maps
============

Maps define how data exposed through ``manatus.Scenarios`` are manipulated to build ``manatus.SourceResource`` objects

``manatus.cli.transform`` reads the configuration file ``manatus_scenarios.cfg``.to determine which map to apply for which source. Configuration options are covered in :ref:`Configuring manatus <anchor02>`

.. note:: You'll probably want to write custom maps as detailed in :ref:`Writing custom maps <anchor01>`

.. automodule:: manatus.maps

   .. rubric:: Functions

   .. autosummary::
   
      dc_standard_map
      qdc_standard_map
      mods_standard_map


Transformation maps
===================

Maps define how data exposed through :doc:`api_scenarios` are manipulated to build :doc:`source_resource` objects.

``manatus.cli.transform`` reads the configuration file ``manatus_scenarios.cfg`` to determine which map to apply for which source. Configuration options are covered in :ref:`Configuring manatus <anchor02>`.

.. note:: You'll probably want to write custom maps as detailed in :ref:`Writing custom maps <anchor01>`

Standard maps
-------------

Default maps bundled in manatus.

.. autofunction:: manatus.maps.dc_standard_map
.. code-include :: :func:`manatus.maps.dc_standard_map`

.. autofunction:: manatus.maps.qdc_standard_map
.. code-include :: :func:`manatus.maps.qdc_standard_map`

.. autofunction:: manatus.maps.mods_standard_map
.. code-include :: :func:`manatus.maps.mods_standard_map`

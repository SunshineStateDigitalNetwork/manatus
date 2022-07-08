Overview
========

loren ipsum

Installation
------------

``python3 -m pip install manatus``

Usage
-----

You can see an overview of options by running ``python3 -m manatus --help`` and
``python3 -m manatus <subcommand> --help``. The main subcommands are:

* ``status`` - display configuration environment status
* ``harvest`` - interact with harvest functionality
* ``transform`` - interact with transformation functionality

Setting the configuration environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Manatus uses a set of configuration files to direct it's behavior. It looks for these files in three places:

1. A location specific by a ``MANATUS_CONFIG`` environment variable

.. note::

    **Setting an environment variable**

    Windows: ``set MANATUS_CONFIG=/path/to/config/dir``

    Mac: ``export MANATUS_CONFIG=/path/to/config/dir``

    Linux: ``export MANATUS_CONFIG=/path/to/config/dir``

2. The file path ``$HOME/.local/share/manatus``

3. The manatus source directory

If a suitable set of configuration files are not identified at those locations, manatus will give you the option of
creating empty config files at the ``$HOME/.local/share/manatus`` path. Entries can be added to empty files through the
CLI.

See :doc:`cli` for full documentation of the CLI. Instructions for configuring the manatus environment are detailed in
:doc:`configuration`.

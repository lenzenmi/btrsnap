.. btrsnap documentation master file, created by
   sphinx-quickstart on Tue Nov 26 10:55:19 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. contents::

.. _btrsnap-functions:

btrsnap functions
=================

.. automodule:: btrsnap
   :members: snap, snapdeep, unsnap, unsnap_deep, show_snaps, show_snaps_deep, sendreceive, sendreceive_deep

btrsnap Classes
===============

.. note:: These Clasess are used internally and are referenced by the toplevel :ref:`functions <btrsnap-functions>`.

.. autoclass:: btrsnap.Btrfs
   :members:

.. autoclass:: btrsnap.Path
   :members:

.. autoclass:: btrsnap.SnapshotsMixin
   :members:

.. autoclass:: btrsnap.SnapPath
   :members:

.. autoclass:: btrsnap.SnapDeep
   :members:

.. autoclass:: btrsnap.ReceivePath
   :members:

.. autoclass:: btrsnap.ReceiveDeep
   :members:

btrsnap Exceptions
==================

.. autoexception:: btrsnap.PathError

.. autoexception:: btrsnap.TargetError

.. autoexception:: btrsnap.BtrfsError

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


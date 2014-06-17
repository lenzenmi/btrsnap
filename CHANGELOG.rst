=========
 btrsnap
=========

-----------
 CHANGELOG
-----------

v2.0.0
~~~~~~
.. attention:: 

    :SYNTAX CHANGE:
        the ``--delete`` option was removed from the *snap* sub-command. ``--keep`` now implies delete.
        
* Improved help/error messages
* Suppressed btrfs output when deleting -- became too noisy
* Code refactoring for easier code maintenance

v1.1.1
~~~~~~

* Fixed bug where some directories not matching the btrsnap timestamp could be processed as snapshots. 
* Renamed test modules to be more "pythonic"

v1.1.0
~~~~~~

* Added sphinx code documentation
* Cleaned up code to pep8 standards
* Added recursive list function
* Added recursive delete function
* Updated help text in CLI

v1.0.0
~~~~~~

* Initial Release

README.rst

=========
 btrsnap
=========

The btrsnap module is written for **python 3.x**.

SNAPPATH:
---------

btrsnap uses a specific directory layout to store BTRFS snapshots. These must be created manually before using many of btrsnap's features.

* It is a directory located on a BTRFS filesystem
* It contains a single symbolic link that points the BTRFS subvolume to be backed up.

It is good practice to organize a collection of SNAPPATHs in a parent directory to take advantage of btrsnap's 'deep' features.

Example
~~~~~~~
.. code-block::

    `-- parent
        |-- photos
        |   `-- target -> /home/photos
        `-- webserver
          `-- target -> /srv/http
        
In this example, photos and webserver are both valid SNAPPATHS and inside a parent folder. Symbolic links can be created using 

.. code-block:: 
    
    $'ln -s path target'
    
USAGE:
------
Now that you have your snappaths created, you can use btrsnap.





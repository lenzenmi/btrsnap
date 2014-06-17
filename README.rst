=========
 btrsnap
=========

The btrsnap module is written for **python 3.x**.

.. contents:: Table of Contents


The SNAPPATH:
--------------

btrsnap uses a specific directory layout to store BTRFS snapshots. These must be created manually before using many of btrsnap's features.

**Requirements**:

* It is a directory located on a BTRFS filesystem
* It contains a single symbolic link that points the BTRFS subvolume to be backed up.

It is good practice to organize a collection of SNAPPATHs in a parent directory to take advantage of btrsnap's 'recursive' features.

Example
~~~~~~~
::

    `-- parent
        |-- photos
        |   `-- target -> /home/photos
        `-- webserver
            `-- target -> /srv/http
        
In this example, photos and webserver are both valid SNAPPATHS and inside a parent folder. 

.. note::
        Symbolic links can be created with the 'ln' command:
        
        .. code-block:: bash
        
            $ln -s path target
    
USAGE:
------
.. note:: btrsnap has four main modes of operation. One of these modes must be specified from the command-line.

snap:
~~~~~
::
   
    usage: btrsnap snap [-h] [-r] [-k N] PATH
    
    Creates a new timestamped BTRFS snapshot inside of PATH. The snapshot will be
    a snapshot of the BTRFS subvolume pointed to by the symbolic link in PATH.
    
    positional arguments:
      PATH             A directory on a BTRFS file system with a symlink pointing
                       to a BTRFS subvolume
    
    optional arguments:
      -h, --help       show this help message and exit
      -r, --recursive  Instead, create a snapshot inside of each directory located
                       inside of PATH
      -k N, --keep N   After creating, delete all but N snapshots
    
    
list:
~~~~~
::

    usage: btrsnap list [-h] [-r] PATH
    
    Show timestamped snapshots in PATH
    
    positional arguments:
      PATH             A directory on a BTRFS filesystem that contains snapshots
                       created by btrsnap.
    
    optional arguments:
      -h, --help       show this help message and exit
      -r, --recursive  Instead, show summary statistics for all subdirectories in
                       PATH
    
delete:
~~~~~~~
::

    usage: btrsnap delete [-h] [-k N] [-r] PATH
    
    Delete all but KEEP snapshots from PATH. (Default, KEEP=5)
    
    positional arguments:
      PATH             A directory on a BTRFS filesystem that contains snapshots
                       created by btrsnap.
    
    optional arguments:
      -h, --help       show this help message and exit
      -k N, --keep N   keep N snapshots when deleting.
      -r, --recursive  Instead delete all but KEEP snapshots from each
                       subdirectory
    
send:      
~~~~~
::

    usage: btrsnap send [-h] [-r] SendPATH ReceivePATH
    
    Send all snapshots from SendPATH to ReceivePATH if not present.
    
    positional arguments:
      SendPATH         A directory on a BTRFS filesystem that contains snapshots
                       created by btrsnap.
      ReceivePATH      A directory on a BTRFS filesystem that will receive
                       snapshots.
    
    optional arguments:
      -h, --help       show this help message and exit
      -r, --recursive  Instead, send snapshots from each sub directory of SendPATH
                       to a subdirectory of the same name in ReceivePATH.
                       Subdirectories are automatically created if needed.

Installation:
-------------
* Instructions on btrsnap wiki:
    https://github.com/lenzenmi/btrsnap/wiki/Install

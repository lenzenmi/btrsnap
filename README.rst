=========
 btrsnap
=========

The btrsnap module is written for **python 3.x**.

.. contents:: Table of Contents

Installation:
-------------
* Instructions on btrsnap wiki:
    https://github.com/lenzenmi/btrsnap/wiki/Install
    

General Linux
~~~~~~~~~~~~~
clone this git repo to your local system, then install using python.

.. code-block:: bash
    
    #Install some dependencies
    pip install python-dateutil
    
    #Install btrsnap
    git clone git://github.com/lenzenmi/btrsnap.git
    cd btrsnap
    python setup.py install

Arch Linux
~~~~~~~~~~

If you are lucky enough to use Arch Linux, there is a python-btrsnap PKGBUILD available on the aur:
    PKGBUILD: python-btrsnap    
        https://aur.archlinux.org/packages/python-btrsnap/


This can easily be automatically installed using yaourt_

.. _yaourt: https://aur.archlinux.org/packages/yaourt/

.. code-block:: bash

    yaourt -S python-btrsnap


The SNAPPATH:
-------------

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

snap
~~~~~
::
   
    usage: btrsnap snap [-h] [-r] [-k N | -d YYYY-MM-DD or ?y?m?d?w] PATH
    
    Creates a new timestamped BTRFS snapshot inside of PATH. The snapshot will be
    a snapshot of the BTRFS subvolume pointed to by the symbolic link in PATH.
    
    positional arguments:
      PATH                  a directory on a BTRFS file system with a symlink
                            pointing to a BTRFS subvolume
    
    optional arguments:
      -h, --help            show this help message and exit
      -r, --recursive       instead, create a snapshot inside of each directory
                            located inside of PATH
    
    Mutually Exclusive:
      (Optional) - Choose 1
    
      -k N, --keep N        after creating, delete all but N snapshots
      -d YYYY-MM-DD or ?y?m?d?w, --date YYYY-MM-DD or ?y?m?d?w
                            after creating, delete all snapshots created on or
                            before the entered date. You may enter dates as ISO
                            format or use the alternate syntax ?y?m?d?w where N
                            can be any positive intager and indicates the number
                            of years, months, days, and weeks respectively
                            
                            
.. Important::
    You will need root permissions to delete.  
    
list
~~~~~
::

    usage: btrsnap list [-h] [-r] PATH
    
    Show timestamped snapshots in PATH.
    
    positional arguments:
      PATH             a directory on a BTRFS filesystem that contains snapshots
                       created by btrsnap.
    
    optional arguments:
      -h, --help       show this help message and exit
      -r, --recursive  instead, show summary statistics for all subdirectories in
                       PATH
    
delete
~~~~~~~
::

    usage: btrsnap delete [-h] [-r] [-k N | -d YYYY-MM-DD or ?y?m?d?w] PATH
    
    Delete all but KEEP snapshots from PATH, or delete all snapshots created on or
    or before DATE
    
    positional arguments:
      PATH                  a directory on a BTRFS filesystem that contains
                            snapshots created by btrsnap
    
    optional arguments:
      -h, --help            show this help message and exit
      -r, --recursive       instead delete all but KEEP snapshots from each
                            subdirectory
    
    Mutually Exclusive:
      (Required) - Choose 1
    
      -k N, --keep N        keep N snapshots when deleting
      -d YYYY-MM-DD or ?y?m?d?w, --date YYYY-MM-DD or ?y?m?d?w
                            delete all snapshots created on or before the entered
                            date. You may enter dates as ISO format or use the
                            alternate syntax ?y?m?d?w where N can be any positive
                            intager and indicates the number of years, months,
                            days, and weeks respectively

.. Important::
    You will need root permissions to delete.                            
    
send
~~~~~
::

    usage: btrsnap send [-h] [-r] SendPATH ReceivePATH
    
    Send all snapshots from SendPATH to ReceivePATH if not present.
    
    positional arguments:
      SendPATH         a directory on a BTRFS filesystem that contains snapshots
                       created by btrsnap
      ReceivePATH      a directory on a BTRFS filesystem that will receive
                       snapshots
    
    optional arguments:
      -h, --help       show this help message and exit
      -r, --recursive  instead, send snapshots from each sub directory of SendPATH
                       to a subdirectory of the same name in ReceivePATH.
                       Subdirectories are automatically created if needed
                       
.. important::
    The ``ReceivePATH`` needs to be relative to the top-level BTRFS volume. If you try to use a path relative to a mounted subvolume, **this operation will fail!!**

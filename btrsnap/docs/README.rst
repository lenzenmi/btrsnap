.. Note::
    This is the code documentation for developers. If you just want to install and use btrsnap, see the README.rst file in the root directory of this project.

The documentation uses ReST (reStructuredText) [1]_, and the Sphinx documentation system [2]_.
This allows it to be built into other forms for easier viewing and browsing.

To create an HTML version of the docs:

* Install Sphinx (using ``sudo pip install Sphinx`` or some other method)

* In this docs/ directory, type ``make html`` 

The documentation in ``_build/html/index.html`` can then be viewed in a web browser.

.. [1] http://docutils.sourceforge.net/rst.html

.. [2] http://sphinx-doc.org/

Installation
-------------

If you are lazy, just perform

::

 $ pip install plac

which will install the module on your system (and possibly argparse
too, if it is not already installed).

If you prefer to install the full distribution from source, including
the documentation, download the tarball_, unpack it and run

::

 $ python setup.py install

in the main directory, possibly as superuser.

.. _tarball: http://pypi.python.org/pypi/plac

Testing
--------

Run

::

 $ python doc/test_plac.py

or

::

 $ nosetests doc

or

::

 $ py.test doc

Some tests will fail if sqlsoup is not installed. 
Run a ``pip install sqlsoup`` or just ignore them.

Documentation
--------------

The source code and the documentation are hosted on GitHub.
Here is the full documentation:

https://github.com/micheles/plac/blob/0.9.6/doc/plac.pdf



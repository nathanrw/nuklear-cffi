nuklear-cffi
============

A semi-automatic Python binding for the nuklear C library.

The core of this is a python program that parses the nuklear.h header for
declarations and passes this to the 'cffi' Python binding generator.

Declarations are extracted using a C preprocessor followed by some simple ad
hoc text transformations.  The 'pcpp' preprocessor is used.  This is a C
preprocessor written in Python, so the preprocessing step doesn't actually
require a C compiler to be installed.

However, the process of generating the Python binding requires a C
compiler.

Some code for interfacing nuklear with pygame is provided under `pynk.nkpygame`.

Usage
-----

See `demo.py`.  The gist of it is to call the nuklear API via the `ffi` and
`lib` objects imported from `pynk` - this is provided by the `cffi` library.
Some code for interfacing with pygame is provided.

Installation
------------

The package on pypi should work: https://pypi.python.org/pypi/pynk

Otherwise

    python2 setup.py install

in the git repository should do it.

Dependencies
------------

 - cffi, a Python library.
 - pcpp, a C preprocessor written in Python.

As such you will need a C compiler installed if you want to build the library.

Note that at present the `pcpp` in pypi won't cut it, because in order to
preprocess nuklear.h we rely on a fix that has not (as of writing) yet been
integrated.  You will have to install the one in my github fork.

For the pygame integration code, `pygame` is necessary, but it's not a
requirement for installation or to use the binding.

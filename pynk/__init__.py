"""
Python-nuklear integration library.

Nuklear is exposed via the 'cffi' library; you make calls via the 'lib'
and 'ffi' objects.  'lib' exposes the nuklear api, while 'ffi' is used
for interfacing with C.  Note that this is a very low level interface;
you must understand both C and Python, and the 'cffi' library.

For details of the API, see nuklear.h.  You can also do help(lib) to
see what methods are exposed, but it won't tell you about their arguments.

For how to use the foreign function interface, see the documentation for
the 'cffi' library.

For an example, see 'demo.py'.
"""

from _nuklear import lib, ffi

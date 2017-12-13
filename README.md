nuklear-cffi
------------

A semi-automatic Python binding generator for the nuklear C library.

This is a python script that parses the nuklear.h header for declarations and
passes this to the 'cffi' Python binding generator.

Declarations are extracted using a C preprocessor followed by some simple ad
hoc text transformations.  At the moment only 'cpp' is supported, this may or
may not be a problem.

In addition to this, the process of generating the Python binding requires a C
compiler.  On Linux this is fine, but on Windows this can't be taken for
granted.  It should be possible to distribute binaries however...

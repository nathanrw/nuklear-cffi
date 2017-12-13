#!/usr/bin/env python2


"""
nuklear-cffi.py

Semi-automatically generates a Python binding for the 'nuklear' GUI library,
which is a simple header-only C library with no dependencies.  The binding
makes use of the 'cffi' python package; to use it see the documentation for
'cffi'.

Usage: ./nuklear-cffi.py [--header <filename>]
"""


import cffi
import re
import subprocess
import os
import os.path
import sys


def run_c_preprocessor(header_contents):
    """
    Run a C preprocessor on the given header file contents.  This
    implementation currently only supports 'cpp' but could be extended 
    in future.
    """
    filename = "preprocessor_input.h"
    open(filename, 'w').write(header_contents)
    return subprocess.check_output(["cpp", "-P", filename])


def build_nuklear_defs(filename, header):
    """
    Preprocess the header file and extract declarations, writing the
    declarations to the given output filename.

    The header contents is preprocessed and then a number of transformations
    are applied to remove problematic constructs - mostly compile-time arithmetic
    in enum declarations.
    """

    print "Preprocessing header..."
    preprocessed_text = run_c_preprocessor(header)

    print "Evaluating << expressions..."
    shift_expr = "\\(1 << \\(([0-9]+)\\)\\)"
    def evaluate_shift(match):
        return str(1 << int(match.group(1)))
    preprocessed_text = re.sub(shift_expr, evaluate_shift, preprocessed_text)

    print "Evaluating | expressions..."
    val_expr = "(nk|NK)_[a-zA-Z0-9_]+"
    or_expr = "%s( *\\| *%s)+" % (val_expr, val_expr)
    def lookup_value(value_name):
        ret = 0
        assignment = re.search("%s *= *([^\n,]*)" % value_name, preprocessed_text)
        if assignment:
            value = assignment.group(1)
            if re.match(or_expr, value) or re.match(val_expr, value):
                ret = evaluate_or(value)
            else:
                ret = int(value, 0)
        else:
            raise Exception("Cannot find definition for value '%s'" % value_name)
        return ret
    def evaluate_or(expression_text):
        values = map(lambda x: lookup_value(x.strip()), expression_text.split("|"))
        return reduce(lambda x,y: x|y, values)
    def replace_or(match):
        return str(evaluate_or(match.group(0)))
    preprocessed_text = re.sub(or_expr, replace_or, preprocessed_text)

    print "Removing dummy_array..."
    preprocessed_text = re.sub(
        "typedef char _dummy_array.*;",
        "",
        preprocessed_text
    )

    print "Stubbing nk_table..."
    preprocessed_text = re.sub(
    	"(struct nk_table {.*?;)[^;]*?sizeof\\(.*?};",
        lambda x: x.group(1) + "\n    ...;\n};",
        preprocessed_text,
        count=0,
        flags=re.MULTILINE|re.DOTALL
    )

    open(filename, 'w').write(preprocessed_text)


if __name__ == '__main__':

    # Names of the files we interact with.
    nuklear_header_filename = "nuklear/nuklear.h"
    nuklear_defs_filename = "nuklear.defs"

    # Parse command line arguments.
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "-h" or arg == "--help":
            print __doc__
            sys.exit(0)
        elif arg == "--header":
            if i+1 == len(sys.argv):
                print "--header <filename>"
                sys.exit(1)
            i += 1
            nuklear_header_filename = sys.argv[i]
        i += 1

    # Define the source & header for nuklear with the options we want to use.
    opts = ""
    header = opts + open(nuklear_header_filename, 'r').read()
    source = "#define NK_IMPLEMENTATION\n" + header
    
    # Extract the 'cdef' text from the header file.  Since this could break
    # with changes to the header file, this is semi-automatic: it will only
    # happen if the existing nuklear.defs is deleted.
    if not os.path.isfile(nuklear_defs_filename):
        print "nuklear.defs doesn't exist. Generating it."
        build_nuklear_defs(nuklear_defs_filename, header) 
    else:
        print "nuklear.defs already exists. Using that."
    
    # Now build the FFI wrapper.
    print "Building ffi wrapper..."
    defs = open(nuklear_defs_filename, 'r').read()
    ffibuilder = cffi.FFI()
    ffibuilder.cdef(defs)
    ffibuilder.set_source("_nuklear", source, libraries=[])
    ffibuilder.compile(verbose=True)

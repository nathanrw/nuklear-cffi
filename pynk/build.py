"""
Semi-automatically generates a Python binding for the 'nuklear' GUI library,
which is a simple header-only C library with no dependencies.  The binding
makes use of the 'cffi' python package; to use it see the documentation for
'cffi'.
"""


import cffi
import re
import os
import os.path
import platform
import StringIO
from pcpp.preprocessor import Preprocessor


def run_c_preprocessor(header_contents):
    """
    Run a C preprocessor on the given header file contents.
    """
    cpp = Preprocessor()
    if platform.system() == "Windows":
        cpp.define("_MSC_VER")
		
		# NOTE: the cffi 'cdef' parser doesn't appear to understand
		# the windows '__int32'.  So give it a definition.
		#   - Not entirely sure what the ramifications of this are,
		#     but it now compiles and runs on Windows...
		#   - A better solution here would probably be to define 
		#     NK_INT32 ourselves as int32_t.
        cpp.define ("__int32 int")
		
        if platform.architecture()[0] == "64bit":
            cpp.define("_WIN64")
        else:
            cpp.define("WIN32")
            cpp.define("_WIN32")
    else:
        cpp.define("__GNUC__")
        if platform.architecture()[0] == "64bit":
            cpp.define("__x86_64__")
    cpp.parse(header_contents)
    output = StringIO.StringIO()
    cpp.write(output)
    return output.getvalue()


def build_nuklear_defs(header, extra_cdef):
    """
    Preprocess the header file and extract declarations, writing the
    declarations to the given output filename.

    The header contents is preprocessed and then a number of transformations
    are applied to remove problematic constructs - mostly compile-time arithmetic
    in enum declarations.
    """

    # Define some options to prune the header.
    header_only_options = """
    #define NK_STATIC_ASSERT(X) 

    """

    print "Preprocessing header..."
    preprocessed_text = run_c_preprocessor(header_only_options + header)

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

    print "Stubbing nk_table..."
    preprocessed_text = re.sub(
    	"(struct nk_table {.*?;)[^;]*?sizeof\\(.*?};",
        lambda x: x.group(1) + "\n    ...;\n};",
        preprocessed_text,
        count=0,
        flags=re.MULTILINE|re.DOTALL
    )

    print "Removing duplicate 'nk_draw_list_clear' declaration..."
    preprocessed_text = re.sub(
        "extern void nk_draw_list_clear\\(struct nk_draw_list \\*list\\);",
        "",
        preprocessed_text
    )

    return preprocessed_text + extra_cdef


def maker():
    """ Make the ffibuilder object by parsing the nuklear header. """

    # Names of the files we interact with.
    nuklear_header_filename = "nuklear/nuklear.h"
    nuklear_overview_filename = "nuklear/demo/overview.c"

    # Define the source & header for nuklear with the options we want to use.
    opts = """
    #define NK_INCLUDE_DEFAULT_ALLOCATOR
    #define NK_INCLUDE_VERTEX_BUFFER_OUTPUT
    #define NK_INCLUDE_FONT_BAKING
    #define NK_INCLUDE_STANDARD_VARARGS
    """
    header = opts + open(nuklear_header_filename, 'r').read()
    source = """
    #define NK_IMPLEMENTATION
    """ + header
    extra_cdef = """
    void pynk_overview(struct nk_context *ctx);
    extern "Python" {
        float pynk_text_width_callback(nk_handle handle, float height, const char *text, int len);
        void pynk_query_font_glyph_callback(nk_handle handle, float font_height,
                                            struct nk_user_font_glyph *glyph,
                                            nk_rune codepoint, nk_rune next_codepoint);
    }
    """
    overview_source = open(nuklear_overview_filename, 'r').read()
    source += """
    #define UNUSED(a) (void)a
    #define MIN(a,b) ((a) < (b) ? (a) : (b))
    #define MAX(a,b) ((a) < (b) ? (b) : (a))
    #define LEN(a) (sizeof(a)/sizeof(a)[0])
    """
    source += overview_source
    source += """
    void pynk_overview(struct nk_context *ctx) {
        overview(ctx);
    }
    """

    # Extract the 'cdef' text from the header file.
    defs = build_nuklear_defs(header, extra_cdef)

    # Now create the FFI builder.
    print "Creating ffi builder..."
    ffibuilder = cffi.FFI()
    ffibuilder.cdef(defs)
    ffibuilder.set_source("_nuklear", source, libraries=[])
    return ffibuilder


if __name__ == '__main__':
    ffibuilder = maker()
    ffibuilder.compile(verbose=True)

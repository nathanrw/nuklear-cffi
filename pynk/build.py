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


def run_c_preprocessor(header_contents):
    """
    Run a C preprocessor on the given header file contents.
    """
    from pcpp.preprocessor import Preprocessor
    cpp = Preprocessor()
    cpp.parse(header_contents)
    output = StringIO.StringIO()
    cpp.write(output)
    return output.getvalue()


def build_nuklear_defs(preprocessed_text, extra_cdef):
    """
    Preprocess the header file and extract declarations, writing the
    declarations to the given output filename.

    The header contents is preprocessed and then a number of transformations
    are applied to remove problematic constructs - mostly compile-time arithmetic
    in enum declarations.
    """

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
    cached_preprocessed_header_filename = "nuklear_preprocessed.h"
    nuklear_overview_filename = "nuklear/demo/overview.c"

    # Define the source & header for nuklear with the options we want to use.
    opts = """
    #define NK_INCLUDE_DEFAULT_ALLOCATOR
    #define NK_INCLUDE_VERTEX_BUFFER_OUTPUT
    #define NK_INCLUDE_FONT_BAKING
    #define NK_INCLUDE_STANDARD_VARARGS
    
    // cffi already includes stdint, so we can just use the fixed-width types
    // here.  defining the FIXED_TYPES thingy causes stdint.h to actually get
    // pulled in when parsing the cdef (since we preprocess the header.)
    #define NK_INT8 int8_t
    #define NK_UINT8 uint8_t
    #define NK_INT16 int16_t
    #define NK_UINT16 uint16_t
    #define NK_INT32 int32_t
    #define NK_UINT32 uint32_t
    #define NK_SIZE_TYPE uintptr_t
    #define NK_POINTER_TYPE uintptr_t
    """
    header = opts + open(nuklear_header_filename, 'rU').read()
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
    overview_source = open(nuklear_overview_filename, 'rU').read()
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
    
    # Define some options to prune the header.
    header_only_options = """
    #define NK_STATIC_ASSERT(X) 

    """
    
    # Can avoid the need to preprocess the header by caching it.  It 
    # can be a bit tricky to get pcpp working.
    preprocessed_text = None
    if os.path.exists(cached_preprocessed_header_filename):
        print 
        print "***************************************************************"
        print "NOTE: Using cached preprocessed header from", cached_preprocessed_header_filename
        print "      Any changes to the header will not have been propagated."
        print "***************************************************************"
        print 
        preprocessed_text = open(cached_preprocessed_header_filename, 'rU').read()
    else:
        print "Preprocessing header..."
        preprocessed_text = run_c_preprocessor(header_only_options + header)
        open(cached_preprocessed_header_filename, 'w').write(preprocessed_text)

    # Extract the 'cdef' text from the header file.
    defs = build_nuklear_defs(preprocessed_text, extra_cdef)

    # Now create the FFI builder.
    print "Creating ffi builder..."
    ffibuilder = cffi.FFI()
    ffibuilder.cdef(defs)
    ffibuilder.set_source("_nuklear", source, libraries=[])
    return ffibuilder


if __name__ == '__main__':
    ffibuilder = maker()
    ffibuilder.compile(verbose=True)

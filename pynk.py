"""
A library for interfacing with the nuklear C library from Python.
"""

import collections
import pygame
import unicodedata

from _nuklear import ffi, lib


@ffi.def_extern()
def pynk_text_width_callback(handle, height, text, text_length):
    """ Text measurement callback. """
    pygame_font = ffi.from_handle(handle.ptr)
    python_text = ffi.string(text, text_length)
    width, height = pygame_font.size(python_text)
    return width


class NkPygame(object):
    """ 
    Manages a nuklear context integrated with pygame.

    This class manages the lifetime of a nuklear context and takes care of
    stitching it into pygame - it provides methods for consuming pygame input
    and rendering to a pygame surface, and it sets up any required userdata
    pointers in the context during initialisation.

    However, this is not a high-level wrapper.  You still need to call the
    nuklear C API on the context, which is exposed via a property.
    """

    class KeyMapping(object):
        """ Maps a pygame key press to a nuklear key sequence. """
    
        def __init__(self, pg, nk, pg_mod=pygame.KMOD_NONE):
            """ Map (pg, pg_mod) -> nk, where pg_mod is an optional modifier that
            defaults to KMOD_NONE.  pg can be a sequence in which case both pygame
            keys are mapped to the same thing.  nk can be a sequence in which case
            multiple nk keys are issued in response to the single pygame event. """
            self.pgs = pg
            if not isinstance(self.pgs, collections.Iterable):
                self.pgs = [self.pgs]
            self.nks = nk
            if not isinstance(self.nks, collections.Iterable):
                self.nks = [self.nks]
            self.pg_mod = pg_mod
    
    class KeyMap(object):
        """ Mapping between pygame and nuklear key constants. """
    
        def __init__(self, *keymappings):
            """ Initialise the key map. """
            self.__keys = {}
            for mapping in keymappings:
                for pg in mapping.pgs:
                    self.__keys.setdefault(pg, {})
                    self.__keys[pg][mapping.pg_mod] = mapping
                
        def map_key(self, key, mod):
            """ Return the nuklear key sequence corresponding to a pygame key+modifier. """
            mapping = self.__keys.get(key, {}).get(mod, None)
            if mapping is None:
                mapping = self.__keys.get(key, {}).get(pygame.KMOD_NONE, None)
            if mapping is not None:
                return mapping.nks
            return []

    KEYMAP = KeyMap(
        KeyMapping([pygame.K_RSHIFT, pygame.K_LSHIFT], lib.NK_KEY_SHIFT),
        KeyMapping(pygame.K_DELETE, lib.NK_KEY_DEL),
        KeyMapping(pygame.K_RETURN, lib.NK_KEY_ENTER),
        KeyMapping(pygame.K_TAB, lib.NK_KEY_TAB),
        KeyMapping(pygame.K_BACKSPACE, lib.NK_KEY_BACKSPACE),
        KeyMapping(pygame.K_HOME, [lib.NK_KEY_TEXT_START, lib.NK_KEY_SCROLL_START]),
        KeyMapping(pygame.K_END, [lib.NK_KEY_TEXT_END, lib.NK_KEY_TEXT_START]),
        KeyMapping(pygame.K_PAGEDOWN, lib.NK_KEY_SCROLL_DOWN),
        KeyMapping(pygame.K_PAGEUP, lib.NK_KEY_SCROLL_UP),
        KeyMapping(pygame.K_z, lib.NK_KEY_TEXT_UNDO, pygame.KMOD_CTRL),
        KeyMapping(pygame.K_r, lib.NK_KEY_TEXT_REDO, pygame.KMOD_CTRL),
        KeyMapping(pygame.K_c, lib.NK_KEY_COPY, pygame.KMOD_CTRL),
        KeyMapping(pygame.K_v, lib.NK_KEY_PASTE, pygame.KMOD_CTRL),
        KeyMapping(pygame.K_x, lib.NK_KEY_CUT, pygame.KMOD_CTRL),
        KeyMapping(pygame.K_b, lib.NK_KEY_TEXT_LINE_START, pygame.KMOD_CTRL),
        KeyMapping(pygame.K_e, lib.NK_KEY_TEXT_LINE_END, pygame.KMOD_CTRL),
        KeyMapping(pygame.K_UP, lib.NK_KEY_UP),
        KeyMapping(pygame.K_DOWN, lib.NK_KEY_DOWN), 
        KeyMapping(pygame.K_LEFT, lib.NK_KEY_LEFT), 
        KeyMapping(pygame.K_LEFT, lib.NK_KEY_TEXT_WORD_LEFT, pygame.KMOD_CTRL), 
        KeyMapping(pygame.K_RIGHT, lib.NK_KEY_RIGHT), 
        KeyMapping(pygame.K_RIGHT, lib.NK_KEY_TEXT_WORD_RIGHT, pygame.KMOD_CTRL)
    )

    def __init__(self, font):
        """ 
        Construct an uninitialised NkPygame instance.

        'font' is the pygame font instance to use for the nuklear font.

        The resulting instance will not yet be initialised - attempting to
        get the context or do anything with it will result in exceptions being
        thrown.  To use the instance, setup() must be called.  This can be
        done manually or via a 'with' statement.
        """
        self.__pygame_font = font
        self.__pygame_font_handle = ffi.new_handle(self.__pygame_font)
        self.__nuklear_font = ffi.new("struct nk_user_font*")
        self.__nuklear_font.userdata.ptr = self.__pygame_font_handle
        self.__nuklear_font.height = self.__pygame_font.get_height()
        self.__nuklear_font.width = lib.pynk_text_width_callback
        self.__ctx = None

    @property
    def ctx(self):
        """ Get the nuklear context. It must have been initialised via setup() first. """
        if self.__ctx is None:
            raise Exception("The nuklear context has not been initialised.")
        return self.__ctx

    def setup(self):
        """ Initialise the nuklear context. """
        if self.__ctx is None:
            self.__ctx = ffi.new("struct nk_context*")
            lib.nk_init_default(self.__ctx, self.__nuklear_font)

    def teardown(self):
        """ Tear down the nuklear context. """
        if self.__ctx is not None:
            lib.nk_free(self.__ctx)
            self.__ctx = None

    def __enter__(self):
        "Support 'with' statement."
        self.setup()
        return self

    def __exit__(self, type, value, traceback):
        "Support 'with' statement."
        self.teardown()

    def handle_events(self, events):
        """ Handle a sequence of pygame events. """
        lib.nk_input_begin(self.ctx)
        for e in events:
            self.handle_event(e)
        lib.nk_input_end(self.ctx)

    def handle_event(self, e):
        """ Map a pygame event to nuklear input. """

        if e.type == pygame.KEYDOWN or e.type == pygame.KEYUP:
            consumed = False
            down = e.type == pygame.KEYDOWN
            for nk_key in NkPygame.KEYMAP.map_key(e.key, e.mod):
                lib.nk_input_key(self.ctx, nk_key, down)
                consumed = True
            if not consumed and down and len(e.unicode) == 1:
                # Note: should pass unicode directly, but need to
                # convert wchar_t (which is what cffi converts to)
                # to int or char[4]. wchar_t is 2 bytes on windows
                # for utf-16
                if unicodedata.category(e.unicode)[0] != "C":
                    char = str(e.unicode)
                    if len(char) == 1:
                        lib.nk_input_char(self.ctx, str(e.unicode))
        elif e.type == pygame.MOUSEBUTTONDOWN or e.type == pygame.MOUSEBUTTONUP:
            down = e.type == pygame.MOUSEBUTTONDOWN
            button = lib.NK_BUTTON_LEFT
            if e.button == 1:
                button = lib.NK_BUTTON_LEFT
            elif e.button == 3:
                button = lib.NK_BUTTON_RIGHT
            lib.nk_input_button(self.ctx, button, e.pos[0], e.pos[1], down)
        elif e.type == pygame.MOUSEMOTION:
            lib.nk_input_motion(self.ctx, e.pos[0], e.pos[1])

    def render_to_surface(self, screen):
        """ 
        Render the nuklear context to a pygame surface.
    
        'screen' is a pygame surface.  This function will set the clip region and
        result in the clip region being set to None.
        """

        nuklear_command = lib.nk__begin(self.ctx)
        while nuklear_command:
            if nuklear_command.type == lib.NK_COMMAND_NOP:
                pass
            elif nuklear_command.type == lib.NK_COMMAND_SCISSOR:
                c = ffi.cast("struct nk_command_scissor*", nuklear_command)
                rect = pygame.Rect(c.x, c.y, c.w, c.h)
                screen.set_clip(rect)
            elif nuklear_command.type == lib.NK_COMMAND_LINE:
                c = ffi.cast("struct nk_command_line*", nuklear_command)
                pygame.draw.line(screen, 
                                 (c.color.r, c.color.g, c.color.b), 
                                 (c.begin.x, c.begin.y),
                                 (c.end.x, c.end.y),
                                 c.line_thickness)
            elif nuklear_command.type == lib.NK_COMMAND_RECT:
                c = ffi.cast("struct nk_command_rect*", nuklear_command)
                rect = pygame.Rect(c.x, c.y, c.w, c.h)
                colour = (c.color.r, c.color.g, c.color.b)
                # c.rounding - unsupported.
                pygame.draw.rect(screen, colour, rect, c.line_thickness)
            elif nuklear_command.type == lib.NK_COMMAND_RECT_FILLED:
                c = ffi.cast("struct nk_command_rect_filled*", nuklear_command)
                rect = pygame.Rect(c.x, c.y, c.w, c.h)
                colour = (c.color.r, c.color.g, c.color.b)
                # c.rounding - unsupported.
                pygame.draw.rect(screen, colour, rect, 0)
            elif nuklear_command.type == lib.NK_COMMAND_CIRCLE:
                c = ffi.cast("struct nk_command_circle*", nuklear_command)
                rect = pygame.Rect(c.x, c.y, c.w, c.h)
                colour = (c.color.r, c.color.g, c.color.b)
                pygame.draw.ellipse(screen, colour, rect, c.line_thickness)
            elif nuklear_command.type == lib.NK_COMMAND_CIRCLE_FILLED:
                c = ffi.cast("struct nk_command_circle_filled*", nuklear_command)
                rect = pygame.Rect(c.x, c.y, c.w, c.h)
                colour = (c.color.r, c.color.g, c.color.b)
                pygame.draw.ellipse(screen, colour, rect, 0)
            elif nuklear_command.type == lib.NK_COMMAND_TRIANGLE:
                c = ffi.cast("struct nk_command_triangle*", nuklear_command)
                points = [(c.a.x, c.a.y), (c.b.x, c.b.y), (c.c.x, c.c.y)]
                colour = (c.color.r, c.color.g, c.color.b)
                pygame.draw.polygon(screen, colour, points, c.line_thickness)
            elif nuklear_command.type == lib.NK_COMMAND_TRIANGLE_FILLED:
                c = ffi.cast("struct nk_command_triangle_filled*", nuklear_command)
                points = [(c.a.x, c.a.y), (c.b.x, c.b.y), (c.c.x, c.c.y)]
                colour = (c.color.r, c.color.g, c.color.b)
                pygame.draw.polygon(screen, colour, points, 0)
            elif nuklear_command.type == lib.NK_COMMAND_POLYGON:
                c = ffi.cast("struct nk_command_polygon*", nuklear_command)
                unpacked = ffi.unpack(c.points, c.point_count)
                points = [(p.x, p.y) for p in unpacked]
                colour = (c.color.r, c.color.g, c.color.b)
                pygame.draw.polygon(screen, colour, points, c.line_thickness)
            elif nuklear_command.type == lib.NK_COMMAND_POLYGON_FILLED:
                c = ffi.cast("struct nk_command_polygon_filled*", nuklear_command)
                unpacked = ffi.unpack(c.points, c.point_count)
                points = [(p.x, p.y) for p in unpacked]
                colour = (c.color.r, c.color.g, c.color.b)
                pygame.draw.polygon(screen, colour, points, 0)
            elif nuklear_command.type == lib.NK_COMMAND_POLYLINE:
                c = ffi.cast("struct nk_command_polyline*", nuklear_command)
                unpacked = ffi.unpack(c.points, c.point_count)
                points = [(p.x, p.y) for p in unpacked]
                colour = (c.color.r, c.color.g, c.color.b)
                pygame.draw.polygon(screen, colour, points, c.line_thickness)
            elif nuklear_command.type == lib.NK_COMMAND_TEXT:
                c = ffi.cast("struct nk_command_text*", nuklear_command)
                pygame_font = ffi.from_handle(c.font.userdata.ptr)
                text = ffi.string(c.string, c.length)
                fg_colour = (c.foreground.r, c.foreground.g, c.foreground.b)
                bg_colour = (c.background.r, c.background.g, c.background.b)
                rect = pygame.Rect(c.x, c.y, c.w, c.h)
                rendered = pygame_font.render(text, True, fg_colour, bg_colour)
                screen.blit(rendered, rect.topleft)
            elif nuklear_command.type == lib.NK_COMMAND_CURVE:
                pass
            elif nuklear_command.type == lib.NK_COMMAND_RECT_MULTI_COLOR:
                pass
            elif nuklear_command.type == lib.NK_COMMAND_IMAGE:
                pass
            elif nuklear_command.type == lib.NK_COMMAND_ARC:
                pass
            elif nuklear_command.type == lib.NK_COMMAND_ARC_FILLED:
                pass
            else:
                raise Exception("Unknown nuklear command type.")
            nuklear_command = lib.nk__next(self.ctx, nuklear_command)
    
        # Reset the clipping.
        screen.set_clip(None)

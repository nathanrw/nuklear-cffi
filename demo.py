#!/usr/bin/env python2

"""
A demo of the nuklear-cffi binding.
"""

import pygame

from _nuklear import ffi, lib

@ffi.def_extern
def pynk_text_width_callback(handle, height, text, text_length):
    """ Text measurement callback. """
    pygame_font = ffi.from_handle(handle.ptr)
    width, height = pygame_font.size(text)
    return width

if __name__ == '__main__':

    # Initialise pygame.
    pygame.init()
    screen = pygame.display.set_mode((640, 480))

    # Create a font to use.
    pygame_font = pygame.font.SysFont("Consolas", 12)

    # Expose the font to nuklear.
    nuklear_font = ffi.new("struct nk_user_font*")
    nuklear_font.userdata.ptr = ffi.new_handle(pygame_font)
    nuklear_font.height = pygame_font.get_height()
    nuklear_font.width = lib.pynk_text_width_callback

    # Initialise the nuklear context.
    nuklear_context = ffi.new("struct nk_context*")
    lib.nk_init_default(nuklear_context, nuklear_font)

    # Main loop.
    running = True
    while running:

        # Handle input.
        lib.nk_input_begin(nuklear_context)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
        lib.nk_input_end(nuklear_context)

        # Do drawing.
        screen.fill((0, 0, 0))
        nuklear_command = lib.nk__begin(nuklear_context)
        while nuklear_command:
            if nuklear_command.type == lib.NK_COMMAND_LINE:
                pass
            else:
                # ...
                pass
            nuklear_command = lib.nk__next(nuklear_context, nuklear_command)
        pygame.display.update()

        # Clear the context for the next pass.
        lib.nk_clear(nuklear_context)

    # Shutdown.
    lib.nk_free(nuklear_context)
    pygame.quit()

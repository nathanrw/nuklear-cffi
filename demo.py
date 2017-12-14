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
    pygame.init()
    screen = pygame.display.set_mode((640, 480))

    pygame_font = pygame.font.SysFont("Consolas", 12)

    nuklear_font = ffi.new("struct nk_user_font*")
    nuklear_font.userdata.ptr = ffi.new_handle(pygame_font)
    nuklear_font.height = pygame_font.get_height()
    nuklear_font.width = lib.pynk_text_width_callback

    nuklear_context = ffi.new("struct nk_context*")
    lib.nk_init_default(nuklear_context, nuklear_font)

    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
        screen.fill((0, 0, 0))
        pygame.display.update()
    pygame.quit()

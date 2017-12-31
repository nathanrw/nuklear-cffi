#!/usr/bin/env python2

"""
A demo of the nuklear-cffi binding.
"""

import collections
import pygame
import unicodedata

from _nuklear import ffi, lib

import pynk

if __name__ == '__main__':

    # Initialise pygame.
    pygame.init()
    screen = pygame.display.set_mode((640, 480))

    # Some state for the GUI.
    EASY = 0
    HARD = 1
    op = EASY
    prop = ffi.new("int*", 0)
    winflags = 0
    running = True
    flags = [ (lib.NK_WINDOW_BORDER, "Border"),
              (lib.NK_WINDOW_MOVABLE, "Movable"),
              (lib.NK_WINDOW_SCALABLE, "Scalable"),
              (lib.NK_WINDOW_CLOSABLE, "Scrollable"),
              (lib.NK_WINDOW_MINIMIZABLE, "Minimizable"),
              (lib.NK_WINDOW_TITLE, "Title") ]

    # Initialise nuklear
    font = pygame.font.SysFont("Consolas", 24)
    with pynk.NkPygame(font) as nkpy:
        while running:

            # Handle input.
            events = []
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
                else:
                    events.append(e)
            nkpy.handle_events(events)

            # Show the demo GUI.
            if lib.nk_begin(nkpy.ctx, "Demo", lib.nk_rect(50, 50, 200, 200), winflags):
                lib.nk_layout_row_static(nkpy.ctx, 30, 80, 1)
                if lib.nk_button_label(nkpy.ctx, "quit"):
                    running = False
                lib.nk_layout_row_dynamic(nkpy.ctx, 30, 2)
                if lib.nk_option_label(nkpy.ctx, "easy", op == EASY): 
                    op = EASY
                if lib.nk_option_label(nkpy.ctx, "hard", op == HARD): 
                    op = HARD
                lib.nk_layout_row_dynamic(nkpy.ctx, 22, 1)
                lib.nk_property_int(nkpy.ctx, "Compression:", 0, prop, 100, 10, 1)
                for flag in flags:
                    lib.nk_layout_row_dynamic(nkpy.ctx, 22, 1)
                    if lib.nk_check_label(nkpy.ctx, flag[1], winflags & flag[0]): 
                        winflags |= flag[0]
                    else:
                        winflags &= ~flag[0]
            lib.nk_end(nkpy.ctx)

            # Draw
            screen.fill((0, 0, 0))
            nkpy.render_to_surface(screen)
            pygame.display.update()

            # Clear the context for the next pass.
            lib.nk_clear(nkpy.ctx)

    # Shutdown.
    pygame.quit()

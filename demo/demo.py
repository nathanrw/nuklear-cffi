#!/usr/bin/env python2

"""
A demo of the nuklear-cffi binding.
"""

import pygame

import pynk
import pynk.nkpygame

from overview import Overview

if __name__ == '__main__':

    # Initialise pygame.
    pygame.init()
    screen = pygame.display.set_mode((1024, 768))

    # Some state for the GUI.
    EASY = 0
    HARD = 1
    op = EASY
    prop = pynk.ffi.new("int*", 0)
    winflags = 0
    running = True
    flags = [ (pynk.lib.NK_WINDOW_BORDER, "Border"),
              (pynk.lib.NK_WINDOW_MOVABLE, "Movable"),
              (pynk.lib.NK_WINDOW_SCALABLE, "Scalable"),
              (pynk.lib.NK_WINDOW_CLOSABLE, "Scrollable"),
              (pynk.lib.NK_WINDOW_MINIMIZABLE, "Minimizable"),
              (pynk.lib.NK_WINDOW_TITLE, "Title") ]

    # Initialise nuklear
    font = pynk.nkpygame.NkPygameFont(pygame.font.SysFont("Consolas", 14))
    with pynk.nkpygame.NkPygame(font) as nkpy:

        overview = Overview()
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
            if pynk.lib.nk_begin(nkpy.ctx, "Demo", pynk.lib.nk_rect(50, 50, 300, 300), winflags):
                pynk.lib.nk_layout_row_static(nkpy.ctx, 30, 80, 1)
                if pynk.lib.nk_button_label(nkpy.ctx, "quit"):
                    running = False
                pynk.lib.nk_layout_row_dynamic(nkpy.ctx, 30, 2)
                if pynk.lib.nk_option_label(nkpy.ctx, "easy", op == EASY): 
                    op = EASY
                if pynk.lib.nk_option_label(nkpy.ctx, "hard", op == HARD): 
                    op = HARD
                pynk.lib.nk_layout_row_dynamic(nkpy.ctx, 22, 1)
                pynk.lib.nk_property_int(nkpy.ctx, "Compression:", 0, prop, 100, 10, 1)
                for flag in flags:
                    pynk.lib.nk_layout_row_dynamic(nkpy.ctx, 22, 1)
                    if pynk.lib.nk_check_label(nkpy.ctx, flag[1], winflags & flag[0]): 
                        winflags |= flag[0]
                    else:
                        winflags &= ~flag[0]
            pynk.lib.nk_end(nkpy.ctx)

            # Show the built-in overview GUI.
            pynk.lib.pynk_overview(nkpy.ctx)

            # Show our version written in Python.
            overview.overview(nkpy.ctx)

            # Draw
            screen.fill((0, 0, 0))
            nkpy.render_to_surface(screen)
            pygame.display.update()

            # Clear the context for the next pass.
            pynk.lib.nk_clear(nkpy.ctx)

    # Shutdown.
    pygame.quit()

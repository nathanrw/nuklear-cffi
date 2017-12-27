#!/usr/bin/env python2

"""
A demo of the nuklear-cffi binding.
"""

import pygame

from _nuklear import ffi, lib

@ffi.def_extern()
def pynk_text_width_callback(handle, height, text, text_length):
    """ Text measurement callback. """
    pygame_font = ffi.from_handle(handle.ptr)
    python_text = ffi.string(text)
    width, height = pygame_font.size(python_text)
    return width

if __name__ == '__main__':

    # Initialise pygame.
    pygame.init()
    screen = pygame.display.set_mode((640, 480))

    # Create a font to use.
    pygame_font = pygame.font.SysFont("Consolas", 12)
    pygame_font_handle = ffi.new_handle(pygame_font)

    # Expose the font to nuklear.
    nuklear_font = ffi.new("struct nk_user_font*")
    nuklear_font.userdata.ptr = pygame_font_handle
    nuklear_font.height = pygame_font.get_height()
    nuklear_font.width = lib.pynk_text_width_callback

    # Initialise the nuklear context.
    ctx = ffi.new("struct nk_context*")
    lib.nk_init_default(ctx, nuklear_font)

    # Some state for the GUI.
    EASY = 0
    HARD = 1
    op = EASY
    prop = ffi.new("int*", 0)

    # Main loop.
    running = True
    while running:

        # Handle input.
        lib.nk_input_begin(ctx)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
        lib.nk_input_end(ctx)

        # Show the demo GUI.
        if lib.nk_begin(ctx, "Demo", lib.nk_rect(50, 50, 200, 200),
                        lib.NK_WINDOW_BORDER|lib.NK_WINDOW_MOVABLE|lib.NK_WINDOW_SCALABLE|\
                        lib.NK_WINDOW_CLOSABLE|lib.NK_WINDOW_MINIMIZABLE|lib.NK_WINDOW_TITLE):
            lib.nk_layout_row_static(ctx, 30, 80, 1)
            if lib.nk_button_label(ctx, "button"):
                print "button pressed"
            lib.nk_layout_row_dynamic(ctx, 30, 2)
            if lib.nk_option_label(ctx, "easy", op == EASY): op = EASY
            if lib.nk_option_label(ctx, "hard", op == HARD): op = HARD
            lib.nk_layout_row_dynamic(ctx, 22, 1)
            lib.nk_property_int(ctx, "Compression:", 0, prop, 100, 10, 1)
        lib.nk_end(ctx)

        # Clear the screen.
        screen.fill((0, 0, 0))

        # Do nuklear drawing.
        nuklear_command = lib.nk__begin(ctx)
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
            nuklear_command = lib.nk__next(ctx, nuklear_command)

        # Update the display.
        screen.set_clip(None)
        pygame.display.update()

        # Clear the context for the next pass.
        lib.nk_clear(ctx)

    # Shutdown.
    lib.nk_free(ctx)
    pygame.quit()

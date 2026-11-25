"""Haru's home (version 2, the big house): one floor plan for every level (metres at 1:10; +x to the right,
+y from the open front to the back). About 10 x 12 m. The small house in ../house stays as a second location.

Grid: three columns, three rows.
    column A x 0.00..0.40    column B x 0.40..0.60 (the hall and stairs spine)    column C x 0.60..1.00
    row front y 0.00..0.45   row middle y 0.45..0.80                               row back y 0.80..1.20

Levels (floor z):  basement -0.26, ground 0.0, upstairs 0.26, attic 0.52.

GROUND
    A front  living room          A middle dining room          A back  kitchen (back door, west wall)
    B 0..0.80 front hall: main stairs up (x 0.50..0.60, y 0.12..0.42), walkway beside them (x 0.40..0.50),
              under-stairs cupboard (door on x 0.50 at y 0.30..0.38), the front door in the hall's front wall
              (y 0, x 0.45..0.55); that wall is a "wild wall" a shot can hide, like every front wall
    B back    back stairs up (x 0.40..0.48, y 0.84..1.14) from the kitchen, pantry (x 0.48..0.60, y 0.80..1.20)
    C front  study                C middle garage                C back  laundry (basement stairs down, garden door)
UPSTAIRS
    A front  Haru's bedroom       A middle bathroom             A back  guest bedroom
    B         the landing, full depth (x 0.40..0.60): main stairwell, back stairwell, linen cupboard
    C front + middle  Mum's bedroom                              C back  second bathroom
ATTIC      the whole footprint under a pitched roof (ridge along y at x 0.50), crawl-spaces behind small doors
BASEMENT   boiler room, storage, a low crawlspace

The loop (for chases): hall -> main stairs -> landing -> back stairs -> kitchen -> dining room -> living room -> hall.
"""
UP = 0.26
LEVEL = {'basement': -0.26, 'ground': 0.0, 'upstairs': UP, 'attic': 2 * UP}
FOOTPRINT = (0.0, 0.0, 1.0, 1.2)
COLS = {'A': (0.0, 0.40), 'B': (0.40, 0.60), 'C': (0.60, 1.0)}
ROWS = {'front': (0.0, 0.45), 'middle': (0.45, 0.80), 'back': (0.80, 1.20)}


def rect(col, row):
    (x0, x1), (y0, y1) = COLS[col], ROWS[row]
    return (x0, y0, x1, y1)


# ground floor rooms (x0, y0, x1, y1)
GROUND = {
    'living_room': rect('A', 'front'), 'dining_room': rect('A', 'middle'), 'kitchen': rect('A', 'back'),
    'hall': (0.40, 0.0, 0.60, 0.80), 'back_stairs': (0.40, 0.80, 0.48, 1.20), 'pantry': (0.48, 0.80, 0.60, 1.20),
    'study': rect('C', 'front'), 'garage': rect('C', 'middle'), 'laundry': rect('C', 'back'),
}
MAIN_STAIRS = (0.50, 0.12, 0.60, 0.42)        # x0, y_bottom, x1, y_top (rising toward the back)
BACK_STAIRS = (0.40, 0.84, 0.48, 1.14)        # rising toward the back, entered from the kitchen at y 0.84
UNDER_STAIRS_DOOR = (0.30, 0.38)              # on the wall x 0.50, y span

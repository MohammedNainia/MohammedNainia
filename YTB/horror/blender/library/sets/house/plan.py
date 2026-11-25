"""Haru's house: the one floor plan every room is built on (metres at 1:10; +y runs from the open front to the back).

The house is a doll's house: the front (y = 0) is open so cameras can look in, every other wall is real, and doors
line up between rooms so Haru can walk through the house. Each room module builds itself at its own floor level 0;
house.py places it at the level below.

    level        floor z   rooms (x0, y0, x1, y1)
    ground       0.0       living room (-0.245, 0, 0.065, 0.25), kitchen (-0.245, 0.25, 0.065, 0.6),
                           hall (0.065, 0, 0.165, 0.6) with the front door, the foot of the stairs
    upstairs     0.26      bedroom (-0.245, 0, -0.065, 0.32), bathroom (-0.245, 0.32, -0.065, 0.6),
                           hallway (-0.065, 0, 0.065, 0.6) + stairwell (0.065, 0.15, 0.165, 0.45)
    attic        0.26      (the attic module builds its floor on top of the upstairs ceiling, 0.258 above it)

Doors (wall, along-wall span from the wall's start):
    hallway west wall x=-0.065:  bedroom y 0.06..0.14, bathroom y 0.38..0.46
    hall west wall x=0.065:      living room y 0.08..0.16 (the stairs fill the hall behind it: the kitchen is
                                 reached through the living room)
    hall east wall x=0.165:      front door y 0.03..0.11
    kitchen west wall x=-0.245:  back door y 0.35..0.43
    kitchen south wall y=0.25:   to the living room x -0.045..0.035
Stairs: from the upstairs floor at y 0.45 down to the ground floor at y 0.15 (13 steps of 2 cm), inside x 0.065..0.165.

Interior walls are built by one room only (so they are not doubled): the kitchen builds the kitchen / living room wall
(y 0.25), the bedroom builds the bedroom / bathroom wall (y 0.32), the hallway builds the hallway / bedroom and
bathroom wall (x -0.065), the hall builds nothing on x 0.065 (the kitchen and living room east walls are theirs).
"""
UP = 0.26           # upstairs floor height above the ground floor
LEVEL = {'living_room': 0.0, 'kitchen': 0.0, 'hall': 0.0, 'bedroom': UP, 'bathroom': UP, 'hallway': UP, 'attic': UP}
FRONT_Y = 0.0
FOOTPRINT = (-0.245, 0.0, 0.165, 0.6)

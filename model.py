"""
Workshop trays: shallow stacking trays for the screws, small electronic parts
and small prints on a workshop desk.

Every tray is the same size, 120 mm square, so any tray stacks on any other and
a few laid side by side fill a patch of desk. Dividers split a tray into
compartments: two, four, six or nine, or none for prints and boards.

Trays stack in a drawer without sliding off each other. A low tongue runs round
the inside edge of every rim, and a matching groove runs under every tray. The
tray above sits flat on the rim with the tongue in its groove, so the outside
walls stay flush and a stack looks like one block. The dividers run up to the
rim, so the tray above closes each compartment like a lid and screws can't hop
from one to the next when the drawer shuts.

Laid side by side on the desk, trays lock together. Each side has a dovetail
tab and a matching slot standing out from the wall: facing any side from
outside, the tab is on the left and the slot on the right, so any side of any
tray joins any side of another, whichever way round they're turned. Lower a
tray beside another and the tabs slide down into the slots; lift it straight
up to take it away. Joined trays stand SIDE_GAP apart.

The magnet version joins trays with flush walls and no tabs. It buries 6 x 2 mm
disc magnets in the plastic while the print is paused. Two on each side stand on
edge in the wall, facing out, and join trays side by side. One or more lie flat
in the floor under each compartment and hold small steel parts down. Its floor
is thicker, to bury them, so it stands 2 mm taller than the plain version, and
both stack on each other. To print it, add two pauses in Bambu Studio, on the
preview's layer slider: one at the first layer at or above FLOOR_PAUSE, for the
floor magnets, and one at the first layer at or above WALL_PAUSE, for the wall
magnets. The script prints both heights. Facing any side from outside, the left
wall magnet has one pole out and the right one the other, so any side of any
tray pulls to any side of another, whichever way round. To get that right
without knowing which pole is which, mark the top face of a stack of magnets:
put every left magnet in marked face out, and every right one marked face in.
Floor magnets go either way up. Measure the magnets before printing, since
cheap ones are often a tenth of a millimetre off, and change MAGNET_D and
MAGNET_T to match.

The tall tray is the same in every way but 50 mm deep, enough for a NEMA 17
stepper motor lying on its side, or a servo standing up. The lid is a flat
plate with the groove underneath, so it locks onto any tray's rim, the tongue
on top, so another tray can stack on a lidded one, and the same tabs and slots,
which are also what you lift it by.

Every inside corner is the same curve, round in plan and from the floor up the
wall, so each corner is a small bowl a fingertip sweeps a screw out of.

Run from this folder:

    uv run model.py
        the standard set below, the fit test and the pictures
    uv run model.py --dividers 4x2 --depth 15 [--magnets]
        one tray of your own: compartments across x deep, inside depth in mm

It writes, next to this script:
    stl/*.stl                     each tray standing on its floor, ready for a slicer
    stl/magnets/*.stl             the magnet version of each
    pictures/trays.png            the set stacked and laid out, a tray's underside, and cuts through two stacked trays
    pictures/trays-magnets.png    the magnet version, and a cut through two joined trays showing the magnets
    pictures/tall-and-lid.png     the tall tray with a motor in it, and the lid

Every tray prints the way it stands, in PLA, with no supports. The groove's
roof is a short bridge, which needs nothing under it.

Coordinates, in millimeters: X across the tray, Y from front to back, Z up.
The floor's underside is at Z = 0 and the rim at Z = FLOOR + depth.

All numbers are a first design, untested in print. Print the fit test, two
small trays with the same rim and groove, before a full set: if they're tight
or loose, change FIT and print them again.
"""

from pathlib import Path
import argparse
import sys

from build123d import Axis, Box, Cylinder, Plane, Polygon, Pos, RectangleRounded, Rot, export_stl, extrude, loft

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from shade import render, sheet  # noqa: E402

OUT = HERE / "stl"

# ---------------------------------------------------------------------------
# The design, in one place
# ---------------------------------------------------------------------------

SIZE = 120.0  # every tray, outside, square
DEPTH = 20.0  # inside, from the floor to the rim
CURVE = 10.0  # every inside corner, in plan and from the floor up the wall
WALL = 2.4  # six lines of a 0.4 mm nozzle
FLOOR = 1.6
DIVIDER = 1.6  # four lines
DIVIDER_DROP = 0.4  # dividers stop this far under the rim, so a stray blob can't hold the tray above off it

# The tongue and groove. The tongue stands on the inner half of the rim, its
# inside face carrying on the wall's. The groove under the floor takes it with
# FIT to spare all round, and a little more height so the tray above rests on
# the outer half of the rim, not on the tongue's tip.
TONGUE_W, TONGUE_H = 1.2, 1.6
TONGUE_LEAD = 0.5  # 45 degree chamfer on the tongue's top outer edge, so a tray finds its place
FIT = 0.25
GROOVE_LEAD = 0.3  # 45 degree chamfer at the groove's mouth, which also keeps the first layer's squash out of it

# The side join: a dovetail tab and slot on each side, a quarter of the way in
# from each corner, standing SIDE_GAP out from the wall. The tab narrows to its
# neck at the wall; the slot is the same shape with JOIN_FIT to spare.
SIDE_GAP = 3.0  # how far the tab and slot stand out, and so the gap between joined trays
TAB_NECK, TAB_HEAD = 5.0, 8.0  # the tab's width at the wall and at its outer end
SLOT_W = 12.0  # the block the slot is cut in
JOIN_FIT = 0.25
SLOT_SHORT = 4.0  # slots stop this far under the rim, so a tray being lowered catches one joint, then the other

# The magnet version. Wall magnets stand on edge a quarter of the way in from
# each corner, low in the wall where the inside curve leaves it thick enough to
# bury them. Floor magnets lie flat in the thicker floor, under the middle of
# each compartment.
MAGNET_D, MAGNET_T = 6.0, 2.0  # the magnets as listed: measure yours and change these
MAGNET_FIT = 0.2  # added to a pocket's width and thickness, for a snug push fit
MAGNET_HEADROOM = 0.3  # a pocket is this much deeper than its magnet, so the nozzle passes clear over it
MAGNET_SKIN = 0.6  # the least plastic between a magnet and the outside
MAGNET_FLOOR = 3.6  # the magnet version's floor: a skin, a lying magnet and its headroom, and a skin over it
WALL_MAGNET_Z = 2.4  # the bottom of the wall pockets, clear of the groove's roof at 1.8 mm
FLOOR_MAGNET_SPAN = 60.0  # one floor magnet per compartment, and another for each further span this long
FLOOR_PAUSE = MAGNET_SKIN + MAGNET_T + MAGNET_HEADROOM  # the floor pockets' top: pause here to drop the floor magnets in
WALL_PAUSE = WALL_MAGNET_Z + MAGNET_D + MAGNET_FIT + MAGNET_HEADROOM  # the wall pockets' top

BED = (256.0, 256.0, 260.0)  # the Bambu Lab X2D's build volume

# The standard set: (name, compartments across, compartments deep, depth).
SET = [
    ("open", 1, 1, DEPTH),
    ("two", 2, 1, DEPTH),
    ("four", 2, 2, DEPTH),
    ("six", 3, 2, DEPTH),
    ("nine", 3, 3, DEPTH),
    ("open-deep", 1, 1, 30.0),
    ("tall", 1, 1, 50.0),
]
LID_T = 3.6  # the lid's plate: the groove underneath, and 1.8 mm over it
FIT_TEST = 50.0  # the fit test: two small trays this size, with the same rim and groove

# Colours for the picture, after the spools in the printer: white, light blue and tan PLA, and the magnets.
WHITE, BLUE, TAN = (0.93, 0.93, 0.91), (0.6, 0.78, 0.92), (0.84, 0.72, 0.54)
STEEL = (0.32, 0.33, 0.36)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def rounded(x0, x1, y0, y1, z0, z1, r):
    """A box with its four vertical edges rounded."""
    b = box(x0, x1, y0, y1, z0, z1)
    return b.fillet(r, b.edges().filter_by(Axis.Z))


def inset(size, z0, z1, by, r_out):
    """A rounded square `by` in from a tray's outline, from z0 to z1."""
    return rounded(by, size - by, by, size - by, z0, z1, r_out - by)


def taper(size, z0, by0, z1, by1, r_out):
    """A rounded square by0 in from a tray's outline at z0, changing straight to by1 in at z1."""
    faces = [
        Plane.XY.offset(z) * Pos(size / 2, size / 2) * RectangleRounded(size - 2 * by, size - 2 * by, r_out - by)
        for z, by in ((z0, by0), (z1, by1))
    ]
    return loft(faces)


def bowl(x0, x1, y0, y1, z0, z1, r):
    """A box with its vertical edges and its bottom edges rounded alike, so each bottom corner is a quarter sphere."""
    b = box(x0, x1, y0, y1, z0, z1)
    return b.fillet(r, b.edges().filter_by(Axis.Z) + b.edges().group_by(Axis.Z)[0])


# ---------------------------------------------------------------------------
# The tray
# ---------------------------------------------------------------------------


def side_spots(size=SIZE):
    """The two joining spots on each side, as (x, y, angle, left). angle turns a shape drawn on the front
    wall to its side; left is the spot on the left as you face that side from outside."""
    spots = []
    for k in range(4):
        for u in (size / 4, size * 3 / 4):
            x, y = [(u, 0), (size, u), (size - u, size), (0, size - u)][k]
            spots.append((x, y, 90 * k, u < size / 2))
    return spots


def on_wall(shape, x, y, angle, z=0.0):
    """Turn a shape drawn on the front wall, at x = 0 and standing out towards -Y, so it sits on the wall at (x, y)."""
    return Pos(x, y, z) * Rot(0, 0, angle) * shape


def tab_width(g):
    """The tab's width at g out from its own wall."""
    return TAB_NECK + (TAB_HEAD - TAB_NECK) * g / SIDE_GAP


def plan(points, z0, z1):
    """A prism standing from z0 to z1 on an outline in plan."""
    return extrude(Plane.XY.offset(z0) * Polygon(*points, align=None), amount=z1 - z0, dir=(0, 0, 1))


def tab(h):
    """A dovetail tab on the front wall, the full height of the tray."""
    out = SIDE_GAP - JOIN_FIT  # stops short of the other tray's wall
    w0, w1 = tab_width(0) / 2, tab_width(out) / 2
    return plan([(-w0, 0.5), (w0, 0.5), (w0, 0), (w1, -out), (-w1, -out), (-w0, 0)], 0, h)


def slot(h, short=SLOT_SHORT):
    """The slot a tab slides into, on the front wall. The tab's wall is SIDE_GAP out, so g there is 0."""
    out = SIDE_GAP - JOIN_FIT
    top = h - short
    block = plan([(-SLOT_W / 2, 0.5), (SLOT_W / 2, 0.5), (SLOT_W / 2, -out), (-SLOT_W / 2, -out)], 0, top)
    w0 = tab_width(SIDE_GAP) / 2 + JOIN_FIT  # at this wall
    w1 = tab_width(-0.2) / 2 + JOIN_FIT  # just past the block's outer face
    return block - plan([(-w0, 0.01), (w0, 0.01), (w1, -SIDE_GAP - 0.2), (-w1, -SIDE_GAP - 0.2)], -1, top + 1)


def compartments(cols, rows, size=SIZE):
    """Each compartment's corner and size in plan, as (x0, y0, width, depth)."""
    iw = size - 2 * WALL
    cw, cd = (iw - (cols - 1) * DIVIDER) / cols, (iw - (rows - 1) * DIVIDER) / rows
    return [(WALL + i * (cw + DIVIDER), WALL + j * (cd + DIVIDER), cw, cd) for i in range(cols) for j in range(rows)]


def floor_spots(cols, rows, size=SIZE):
    """Where the floor magnets go: spread evenly under each compartment, one per FLOOR_MAGNET_SPAN or part of one."""
    spots = []
    for x0, y0, cw, cd in compartments(cols, rows, size):
        nx, ny = max(1, round(cw / FLOOR_MAGNET_SPAN)), max(1, round(cd / FLOOR_MAGNET_SPAN))
        spots += [(x0 + cw * (i + 0.5) / nx, y0 + cd * (j + 0.5) / ny) for i in range(nx) for j in range(ny)]
    return spots


def wall_magnet_skin(r):
    """The plastic left between a wall magnet's pocket and the inside of the tray, at the pocket's top corner."""
    z = WALL_PAUSE - MAGNET_FLOOR  # the pocket's top, above the inside floor
    curve_in = r - (r * r - (r - z) ** 2) ** 0.5 if z < r else 0.0
    return WALL + curve_in - (MAGNET_SKIN + MAGNET_T + MAGNET_FIT)


def tray(cols=1, rows=1, depth=DEPTH, curve=CURVE, size=SIZE, magnets=False, join=None):
    """A tray split into cols x rows compartments, standing on its floor. The magnet version
    buries magnets in its walls and floor in place of the tabs and slots."""
    join = not magnets if join is None else join
    floor = MAGNET_FLOOR if magnets else FLOOR
    h, t, ro = floor + depth, WALL, curve + WALL
    p = rounded(0, size, 0, size, 0, h, ro)

    # The inside: one bowl-cornered pocket per compartment, up to the dividers' tops, then open to the rim.
    top = h - DIVIDER_DROP
    rooms = compartments(cols, rows, size)
    r = min(curve, rooms[0][2] / 2 - 0.01, rooms[0][3] / 2 - 0.01)
    for x0, y0, cw, cd in rooms:
        p -= bowl(x0, x0 + cw, y0, y0 + cd, floor, top + 1, r)
    p -= inset(size, top, h + 1, t, ro)

    p = locking(p, size, h, ro)
    if join:
        p = joining(p, size, h)

    # The magnet pockets: closed in by the print once it carries on after each pause.
    if magnets:
        skin = wall_magnet_skin(r)
        assert skin >= MAGNET_SKIN, f"only {skin:.2f} mm inside the wall magnets: use a bigger curve"
        assert MAGNET_FLOOR - FLOOR_PAUSE >= MAGNET_SKIN, "the floor is too thin to bury the floor magnets"
        w, d = (MAGNET_D + MAGNET_FIT) / 2, MAGNET_T + MAGNET_FIT
        slot_ = box(-w, w, MAGNET_SKIN, MAGNET_SKIN + d, WALL_MAGNET_Z, WALL_PAUSE)
        for x, y, angle, _ in side_spots(size):
            p -= on_wall(slot_, x, y, angle)
        for x, y in floor_spots(cols, rows, size):
            p -= Pos(x, y, (MAGNET_SKIN + FLOOR_PAUSE) / 2) * Cylinder((MAGNET_D + MAGNET_FIT) / 2, FLOOR_PAUSE - MAGNET_SKIN)
    return p


def locking(p, size, h, ro):
    """Add the tongue on the rim at height h, and cut the groove underneath, where the tongue of the tray below goes."""
    t = WALL
    tongue = inset(size, h - 0.01, h + TONGUE_H, t - TONGUE_W, ro)
    tongue = tongue.chamfer(TONGUE_LEAD, None, tongue.edges().group_by(Axis.Z)[-1])
    p += tongue - inset(size, h - 1, h + TONGUE_H + 1, t, ro)
    a, b = t - TONGUE_W - FIT, t + FIT  # the groove's outer and inner edges, in from the outline
    g, top = GROOVE_LEAD, TONGUE_H + 0.2
    outer = taper(size, -0.01, a - g - 0.01, g, a, ro) + inset(size, g - 0.01, top, a, ro)
    inner = taper(size, -0.02, b + g + 0.02, g, b, ro) + inset(size, g - 0.01, top + 1, b, ro)
    return p - (outer - inner)


def joining(p, size, h, short=SLOT_SHORT):
    """Add the side join, a tab on the left of each side and a slot on the right, standing h tall."""
    for x, y, angle, left in side_spots(size):
        p += on_wall(tab(h) if left else slot(h, short), x, y, angle)
    return p


def lid(size=SIZE, curve=CURVE, join=True):
    """A flat lid: the groove underneath locks it onto a tray's rim, and the tongue on top takes another tray.
    Its slots run its full thickness, so a tray beside it can be lowered past."""
    ro = curve + WALL
    p = locking(rounded(0, size, 0, size, 0, LID_T, ro), size, LID_T, ro)
    return joining(p, size, LID_T, short=0.0) if join else p


def nema17(x, y, z):
    """A NEMA 17 stepper motor lying on its side, its shaft along +X, for the picture: a 48 mm body."""
    body = box(x - 24, x + 24, y - 21.15, y + 21.15, z, z + 42.3)
    boss = Pos(x + 25, y, z + 21.15) * Rot(0, 90, 0) * Cylinder(11, 2)
    shaft = Pos(x + 38, y, z + 21.15) * Rot(0, 90, 0) * Cylinder(2.5, 24)
    return body + boss + shaft


def magnets(cols, rows, size=SIZE):
    """A magnet tray's magnets, wall then floor, for the picture."""
    disc = Pos(0, MAGNET_SKIN + MAGNET_FIT / 2 + MAGNET_T / 2, WALL_MAGNET_Z + MAGNET_D / 2) * Rot(90, 0, 0) * Cylinder(MAGNET_D / 2, MAGNET_T)
    wall = [on_wall(disc, x, y, angle) for x, y, angle, _ in side_spots(size)]
    return wall + [Pos(x, y, MAGNET_SKIN + MAGNET_T / 2) * Cylinder(MAGNET_D / 2, MAGNET_T) for x, y in floor_spots(cols, rows, size)]


def height(depth=DEPTH, magnets=False):
    """What a tray of this depth adds to a stack: the tray above sits on its rim."""
    return (MAGNET_FLOOR if magnets else FLOOR) + depth


# ---------------------------------------------------------------------------
# Build and export
# ---------------------------------------------------------------------------


def export(name, part, folder=OUT):
    """Write a tray's STL, centered on the plate, and check it fits the printer."""
    bb = part.bounding_box()
    flat = Pos(-(bb.min.X + bb.max.X) / 2, -(bb.min.Y + bb.max.Y) / 2, -bb.min.Z) * part
    size = bb.size
    fits = size.X <= BED[0] - 4 and size.Y <= BED[1] - 4 and size.Z <= BED[2]
    print(f"{name:12} {size.X:6.1f} x {size.Y:5.1f} x {size.Z:4.1f}  {part.volume / 1000:6.1f} cm3  valid {part.is_valid}  fits {fits}")
    assert fits, f"{name} is too big for the printer"
    folder.mkdir(parents=True, exist_ok=True)
    export_stl(flat, folder / f"{name}.stl", tolerance=0.02, angular_tolerance=0.1)


def picture(path):
    """The set stacked and laid out on the desk, a tray from underneath, and a cut through two stacked trays and their joint."""
    at = lambda shape, x, y, z=0.0: Pos(x, y, z) * shape  # noqa: E731
    trays = {name: tray(c, r, d) for name, c, r, d in SET}
    s = height()

    scene = []
    for n, (name, col) in enumerate([("open", WHITE), ("two", BLUE), ("four", TAN)]):
        scene.append((at(trays[name], 0, 0, n * s), col))
    scene.append((at(trays["nine"], 0, 0, 3 * s + 26), WHITE))  # lifted off the top
    x0, y0 = SIZE + 55, -70  # on the desk, joined
    for n, (name, col) in enumerate([("open-deep", TAN), ("six", BLUE), ("four", WHITE), ("two", TAN)]):
        scene.append((at(trays[name], x0 + (n % 2) * (SIZE + SIDE_GAP), y0 + (n // 2) * (SIZE + SIDE_GAP)), col))
    look = (x0, 50, 40)
    render(scene, path.with_suffix(".set.png"), eye=(look[0] + 1500, look[1] - 1875, look[2] + 1725), target=look, size=(1300, 1000), scale=2.0)

    flipped = Pos(0, SIZE, height()) * Rot(180, 0, 0) * trays["four"]  # turned over in the hand
    look = (SIZE / 2, SIZE / 2, 10)
    render([(flipped, BLUE)], path.with_suffix(".under.png"), eye=(look[0] + 1500, look[1] - 1875, look[2] + 1725), target=look, size=(900, 860), scale=3.0)

    # Two trays stacked, cut straight across through a compartment, the wall and a divider, seen from the front.
    yc = SIZE * 0.45  # clear of the tabs and slots
    keep = box(-3, 72, yc, SIZE + 5, -5, 80)
    face = box(-3, 72, yc - 0.01, yc + 0.3, -5, 80)
    cut = []
    for z, col in ((0, TAN), (s, BLUE)):
        part = at(trays["four"], 0, 0, z)
        cut += [(part & keep, col), (part & face, tuple(c * 0.62 for c in col))]
    look = (35, yc, s)
    render(cut, path.with_suffix(".cut.png"), eye=(look[0] + 150, look[1] - 1500, look[2] + 260), target=look, size=(1100, 860), tolerance=0.01)

    # The joint, enlarged: the same cut, close in on the wall.
    yj = 40.0  # clear of the slot, the tab and the divider
    keep = box(-1.5, 9, yj, yj + 12, s - 6, s + 4.5)
    face = box(-1.5, 9, yj - 0.01, yj + 0.08, s - 6, s + 4.5)
    joint = []
    for z, col in ((0, TAN), (s, BLUE)):
        part = at(trays["four"], 0, 0, z)
        joint += [(part & keep, col), (part & face, tuple(c * 0.62 for c in col))]
    look = (4, yj, s)
    render(joint, path.with_suffix(".joint.png"), eye=(look[0] + 250, look[1] - 1500, look[2] + 200), target=look, size=(900, 860), tolerance=0.004)

    # Two trays joined, cut across low down and seen from above: the tab of one locked in the slot of the other.
    zc = 8.0
    keep = box(SIZE - 22, SIZE + SIDE_GAP + 22, 14, 106, -1, zc)
    face = box(SIZE - 22, SIZE + SIDE_GAP + 22, 14, 106, zc - 0.08, zc)
    side = []
    for x, col in ((0, TAN), (SIZE + SIDE_GAP, BLUE)):
        part = at(trays["four"], x, 0)
        side += [(part & keep, col), (part & face, tuple(c * 0.62 for c in col))]
    look = (SIZE + SIDE_GAP / 2, 60, 0)
    render(side, path.with_suffix(".side.png"), eye=(look[0], look[1], 1000), target=look, up=(0, 1, 0), size=(900, 1100), tolerance=0.01)

    sheet(
        path,
        "Workshop trays",
        [
            (path.with_suffix(".set.png"), ["THE SET", "Every tray is 120 mm square, so any one stacks on any other,", "and a tab and slot on every side join trays side by side."]),
            (path.with_suffix(".under.png"), ["UNDERNEATH", "A groove runs round the floor", "for the tongue on the rim below."]),
            (path.with_suffix(".cut.png"), ["A CUT THROUGH TWO STACKED TRAYS", "The walls are flush, and the divider meets", "the floor of the tray above."]),
            (path.with_suffix(".joint.png"), ["THE JOINT, ENLARGED", "The tongue on the rim below sits in the groove,", "with 0.25 mm to spare all round."]),
            (path.with_suffix(".side.png"), ["TWO TRAYS JOINED, FROM ABOVE", "Each side's tab, on its left, slides down into", "the other tray's slot. Lift a tray to part them."]),
        ],
        columns=2,
        date="2026-10-25",
    )
    for p in (path.with_suffix(f".{v}.png") for v in ("set", "under", "cut", "joint", "side")):
        p.unlink()


def picture_magnets(path):
    """The magnet version stacked and joined, and a cut through two joined trays showing their magnets."""
    at = lambda shape, x, y, z=0.0: Pos(x, y, z) * shape  # noqa: E731
    four, six = tray(2, 2, magnets=True), tray(3, 2, magnets=True)
    s = height(magnets=True)
    scene = [(at(tray(1, 1, magnets=True), 0, 0), WHITE), (at(four, 0, 0, s + 22), TAN)]  # one lifted off another
    x0, y0 = SIZE + 55, -70  # on the desk, joined flush
    scene += [(at(six, x0, y0), BLUE), (at(four, x0 + SIZE, y0), WHITE), (at(four, x0, y0 + SIZE), TAN)]
    look = (x0, 20, 30)
    render(scene, path.with_suffix(".set.png"), eye=(look[0] + 1500, look[1] - 1875, look[2] + 1725), target=look, size=(1300, 1000), scale=2.0)

    # Two four-compartment trays side by side, cut through a pair of wall magnets and a row of floor magnets.
    yc = SIZE / 4 + 0.4
    keep = box(SIZE - 52, SIZE + 52, yc, SIZE + 5, -1, 40)
    face = box(SIZE - 52, SIZE + 52, yc - 0.01, yc + 0.3, -1, 40)
    cut = []
    for x, col in ((0, TAN), (SIZE, BLUE)):
        part = at(four, x, 0)
        cut += [(part & keep, col), (part & face, tuple(c * 0.62 for c in col))]
        cut += [(at(m, x, 0) & keep, STEEL) for m in magnets(2, 2)]
    look = (SIZE, yc, 8)
    render(cut, path.with_suffix(".cut.png"), eye=(look[0] + 250, look[1] - 1500, look[2] + 420), target=look, size=(1300, 800), tolerance=0.01)

    sheet(
        path,
        "Workshop trays with magnets",
        [
            (path.with_suffix(".set.png"), ["THE MAGNET VERSION", "Flush walls with no tabs: magnets join trays side by side.", "It still stacks on a tongue and groove."]),
            (path.with_suffix(".cut.png"), ["A CUT THROUGH TWO JOINED TRAYS", f"Wall magnets face each other through {2 * MAGNET_SKIN:.1f} mm of plastic.", "Floor magnets lie under each compartment."]),
        ],
        columns=1,
        date="2026-10-25",
    )
    for p in (path.with_suffix(f".{v}.png") for v in ("set", "cut")):
        p.unlink()


def picture_tall(path):
    """The tall tray with a NEMA 17 in it and its lid lifted off, and a lidded tall tray joined to a shallow one."""
    at = lambda shape, x, y, z=0.0: Pos(x, y, z) * shape  # noqa: E731
    tall, cap, four = tray(1, 1, 50.0), lid(), tray(2, 2)
    h = height(50.0)
    scene = [(tall, TAN), (nema17(44, SIZE / 2, FLOOR), STEEL), (at(cap, 0, 0, h + 34), WHITE)]
    x0, y0 = SIZE + 55, -70
    scene += [(at(tall, x0, y0), BLUE), (at(cap, x0, y0, h), WHITE), (at(four, x0 + SIZE + SIDE_GAP, y0), TAN)]
    scene += [(at(cap, x0 + SIZE + SIDE_GAP, y0, height()), WHITE)]
    look = (x0, 20, 40)
    render(scene, path.with_suffix(".set.png"), eye=(look[0] + 1500, look[1] - 1875, look[2] + 1725), target=look, size=(1300, 1000), scale=2.0)
    sheet(
        path,
        "Workshop trays: the tall tray and the lid",
        [(path.with_suffix(".set.png"), ["The tall tray is 50 mm deep inside: a NEMA 17 motor lies on its side with room to spare.",
                                          "The lid locks onto any tray, takes another tray on top, and joins its neighbours."])],
        columns=1,
        date="2026-10-25",
    )
    path.with_suffix(".set.png").unlink()


def counts(text):
    a, b = text.lower().split("x")
    return int(a), int(b)


def main():
    ap = argparse.ArgumentParser(description="Stacking workshop trays. With no options, writes the standard set, the fit test and the picture.")
    ap.add_argument("--dividers", type=counts, help="compartments across x deep, e.g. 4x2")
    ap.add_argument("--depth", type=float, default=DEPTH, help=f"inside depth in mm, floor to rim (default {DEPTH:g})")
    ap.add_argument("--curve", type=float, default=CURVE, help=f"inside corner radius in mm (default {CURVE:g})")
    ap.add_argument("--magnets", action="store_true", help="the magnet version, with magnets in the walls and floor in place of tabs")
    ap.add_argument("--name", help="file name, without .stl")
    args = ap.parse_args()

    pauses = f"pause for the floor magnets at the first layer at or above {FLOOR_PAUSE:.2f} mm, and for the wall magnets at {WALL_PAUSE:.2f} mm"
    OUT.mkdir(parents=True, exist_ok=True)
    if args.dividers or args.depth != DEPTH or args.curve != CURVE or args.magnets:
        c, r = args.dividers or (1, 1)
        name = args.name or f"tray-{c}x{r}-{args.depth:g}mm" + ("-magnets" if args.magnets else "")
        export(name, tray(c, r, args.depth, args.curve, magnets=args.magnets), OUT / "magnets" if args.magnets else OUT)
        if args.magnets:
            print(f"{len(magnets(c, r))} magnets; {pauses}")
        return

    for name, c, r, depth in SET:
        export(name, tray(c, r, depth))
    export("lid", lid())
    export("fit-test", tray(1, 1, 8.0, 8.0, FIT_TEST, join=False))
    print(f"each tray adds {height():.1f} mm to a stack, and the deep one {height(30.0):.1f} mm")
    print("the magnet version:")
    for name, c, r, depth in SET:
        export(name, tray(c, r, depth, magnets=True), OUT / "magnets")
        print(f"{'':12} {len(magnets(c, r))} magnets")
    export("lid", lid(join=False), OUT / "magnets")
    print(f"{'':12} no magnets: a flush lid for the magnet trays")
    print(f"each magnet tray adds {height(magnets=True):.1f} mm to a stack; {pauses}")
    (HERE / "pictures").mkdir(exist_ok=True)
    picture(HERE / "pictures" / "trays.png")
    picture_magnets(HERE / "pictures" / "trays-magnets.png")
    picture_tall(HERE / "pictures" / "tall-and-lid.png")
    print("written to", HERE)


if __name__ == "__main__":
    main()

"""Footprint placement for minipc-power: ref -> (x, y, rotation) in mm relative to the board's top-left corner.

Three bands (see docs/layout-plan.md):
  A (top):    12 V boost (left) and 5 V boost (right), output pads on the top edge above each output FET
  B (middle): USB-C on the left edge, PD sink, charger, 3.3 V buck-boost, protection next to the battery pads
  C (bottom): switch / status / 3.3 V output / NTC pads on the bottom edge, their small parts just above
Converters follow their datasheet layout examples (TPS61178 fig. 36, TPS61088-Q1 fig. 21, TPS63802 fig. 12-1).
"""
ORIGIN = (100.0, 100.0)
BOARD = (52.0, 36.0)
CORNER_R = 1.0

PLACE = {
    'H1': (2.8, 2.8), 'H2': (49.2, 33.2),
    # ================= band A: 12 V (TPS61178, rot 0 = datasheet fig. 36: L left, VOUT/FET/COUT2 right)
    'L2': (5.6, 9.6, 0),
    'U4': (13.4, 9.6, 0),
    'C11': (10.8, 6.6, 90),                              # BST - SW
    'C12': (14.4, 6.4, 0),                               # VCC
    'C9': (3.4, 14.6, 0), 'C10': (7.2, 14.6, 0),        # VIN (input current is continuous in a boost)
    'R11': (11.6, 13.2, 90), 'R12': (12.8, 13.2, 90),   # FREQ, ILIMIT
    'R15': (14.0, 13.2, 90), 'C13': (15.2, 13.2, 90),    # COMP network
    'R13': (17.0, 15.2, 0), 'R14': (17.0, 14.0, 0),     # FB divider (top from +12V)
    'C14': (17.2, 8.0, 90), 'C15': (17.2, 11.6, 90),    # COUT1 at the VOUT bar
    'R16': (19.4, 5.6, 0), 'C16': (19.4, 6.8, 0),       # Rgate / Cgate (source - gate)
    'Q4': (21.2, 9.8, 180),                              # S pad left, D/G right
    'C17': (25.2, 7.4, 90), 'C18': (25.2, 12.2, 90), 'C19': (21.0, 13.6, 0),
    'J6': (21.0, 2.8), 'J15': (25.0, 2.8),
    # ================= band A: 5 V (TPS61088-Q1, rot 0 = datasheet fig. 21: L up-left, CIN low-left, COUT right)
    'L3': (31.4, 9.6, 0),
    'U5': (40.0, 10.6, 0),
    'C20': (28.6, 14.6, 0), 'C21': (32.2, 14.6, 0), 'C22': (35.8, 14.6, 0), 'C23': (37.0, 16.2, 0),
    'C24': (36.6, 9.6, 90), 'R17': (36.6, 7.2, 90),     # BOOT, FSW (to SW)
    'C25': (39.2, 6.6, 0), 'C26': (39.2, 5.0, 0),       # VCC
    'C27': (38.6, 14.6, 90), 'R18': (43.4, 7.2, 0),    # SS, ILIM
    'R21': (43.4, 11.2, 0), 'C28': (43.4, 12.4, 0), 'C29': (43.4, 13.6, 0),
    'R19': (43.4, 8.4, 0), 'R20': (43.4, 9.6, 0),     # FB divider at the VOUT side
    'C30': (46.2, 9.0, 90), 'C31': (49.6, 9.0, 90),
    'R22': (44.6, 15.6, 90), 'C32': (45.8, 15.6, 90), 'Q5': (48.6, 14.6, 90), 'R23': (47.0, 17.6, 0),
    'Q6': (41.4, 17.6, 0),
    'J7': (44.4, 2.8), 'J16': (48.4, 2.8),
    # ================= band B: USB-C + PD sink
    'J1': (3.6, 21.5, 270),
    'U1': (11.4, 21.5, 180), 'R1': (11.4, 24.2, 0), 'C1': (11.4, 19.0, 0), 'D1': (11.6, 16.9, 0),
    # ================= band B: charger (BQ25606 rot 0: VBUS/PMID top-left, SW top-right, SYS/BAT right)
    'U2': (18.6, 21.6, 0),
    'C2': (14.6, 19.6, 90), 'C3': (17.4, 17.6, 0), 'C4': (20.4, 17.4, 90), 'C7': (14.6, 24.0, 90),
    'L1': (25.9, 19.8, 0), 'C5': (23.4, 24.6, 0), 'C6': (26.8, 24.6, 0),
    'R2': (17.6, 25.4, 90), 'R3': (18.8, 25.4, 90), 'R4': (20.0, 25.4, 90), 'R5': (21.2, 25.4, 90),
    'LED1': (13.0, 26.6, 0), 'R6': (13.0, 28.0, 0),
    # ================= band B: 3.3 V buck-boost (TPS63802 rot 0: L1/L2 on the right column)
    'U6': (30.0, 27.6, 0), 'L4': (35.4, 27.8, 0), 'C33': (30.2, 24.6, 0), 'C34': (30.0, 30.4, 0),
    'R24': (26.4, 27.4, 0), 'R25': (26.4, 28.6, 0), 'R26': (26.4, 26.2, 0),
    # ================= band B: protection (battery pads on the right edge)
    'J2': (49.6, 21.6), 'J3': (49.6, 27.0),
    'F1': (43.4, 21.6, 0),
    'Q1': (46.2, 27.0, 0), 'Q2': (43.2, 27.0, 0), 'Q3': (40.2, 27.0, 0),
    'U3': (43.0, 31.0, 0), 'R7': (40.2, 30.4, 90), 'C8': (41.2, 33.6, 0), 'R8': (45.6, 30.6, 90),
    'R9': (47.0, 30.4, 90), 'R10': (44.6, 33.6, 0),
    # ================= band C: bottom-edge pads and their parts
    'J9': (4.6, 33.2), 'J10': (8.2, 33.2), 'J11': (11.8, 33.2), 'J12': (15.4, 33.2), 'J13': (19.0, 33.2),
    'J14': (22.6, 33.2), 'J8': (26.8, 33.2), 'J17': (30.8, 33.2), 'J4': (34.4, 33.2), 'J5': (38.0, 33.2),
    'R27': (5.4, 29.2, 0), 'R28': (5.4, 30.4, 0), 'C35': (7.6, 29.2, 0),
    'R29': (18.4, 29.6, 0), 'R30': (20.8, 29.6, 0), 'C36': (20.8, 28.4, 0),
}

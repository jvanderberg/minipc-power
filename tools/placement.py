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
    # C_OUT1 (C14, C15) VOUT pad on the VOUT bar, GND pad on the PGND bar's copper (smallest SW-rectifier-COUT loop);
    # FREQ / ILIM / COMP / FB parts in pin order under the bottom row, ground pads down onto a separate AGND bus
    'L2': (5.15, 9.6, 0),
    'U4': (12.95, 9.6, 0),
    'C11': (10.35, 6.6, 90),                              # BST - SW
    'C12': (15.0, 5.6, 0),                               # VCC
    'C9': (2.95, 14.6, 0), 'C10': (6.75, 14.6, 0),        # VIN (input current is continuous in a boost)
    'R11': (11.6, 13.25, 270), 'R12': (13.1, 13.25, 270),   # FREQ, ILIMIT
    'R15': (14.6, 13.25, 270), 'C13': (15.7, 13.25, 270),    # COMP network
    'R13': (17.9, 13.25, 90), 'R14': (16.8, 13.25, 270),     # FB divider (top from +12V)
    'C14': (16.05, 10.0, 270), 'C15': (18.1, 10.0, 270),    # COUT1 at the VOUT bar
    'R16': (18.4, 7.1, 90), 'C16': (17.35, 7.1, 90),       # Rgate / Cgate (source - gate)
    'Q4': (21.2, 9.8, 180),                              # S pad left, D/G right
    'C17': (25.2, 8.4, 90), 'C18': (25.2, 13.2, 90), 'C19': (21.0, 13.6, 180),
    'J6': (21.0, 2.8), 'J15': (25.0, 2.8),
    # ================= band A: 5 V (TPS61088-Q1, rot 0 = datasheet fig. 21: L up-left, CIN low-left, COUT right)
    # FSW / BOOT parts upright in the L3-IC gap (SW ends on the SW pour), VIN cap C23 under VIN pin 9, ILIM/COMP/FB column
    # top-right in pin order, C_OUT VOUT-up beside the VOUT pins with GND on the PGND pour from the EP's bottom tab.
    # Load switch Q5 top-right: source on the VOUT pour, drains straight up to the +5V pad (J7 / J16 swapped for this)
    'L3': (31.4, 9.6, 0),
    'U5': (40.3, 10.6, 0),
    'C20': (28.6, 14.6, 0), 'C21': (32.2, 14.6, 0), 'C22': (35.8, 14.6, 0), 'C23': (38.3, 14.3, 270),
    'C24': (37.1, 12.3, 90), 'R17': (37.1, 8.0, 90),     # BOOT, FSW (to SW)
    'C25': (39.5, 6.6, 0), 'C26': (39.5, 5.0, 0),       # VCC
    'C27': (39.85, 14.3, 270), 'R18': (44.1, 5.55, 0),    # SS, ILIM
    'R21': (44.1, 7.65, 0), 'C28': (46.4, 7.65, 0), 'C29': (44.1, 6.6, 0),
    'R19': (43.6, 10.4, 90), 'R20': (44.1, 8.7, 0),     # FB divider at the VOUT side
    'C30': (46.5, 13.3, 270), 'C31': (49.9, 13.3, 270),
    'R22': (46.9, 5.6, 90), 'C32': (45.85, 5.6, 90), 'Q5': (49.4, 7.4, 270), 'R23': (47.0, 17.6, 180),
    'Q6': (44.0, 17.6, 0),
    'J7': (48.4, 2.8), 'J16': (44.4, 2.8),
    # ================= band B: USB-C + PD sink
    'J1': (3.6, 21.5, 270),
    'U1': (11.4, 21.5, 90), 'R1': (10.7, 24.0, 270), 'C1': (13.9, 22.3, 90), 'D1': (11.6, 16.9, 0),
    # ================= band B: charger (BQ25606 rot 0: VBUS/PMID top-left, SW top-right, SYS/BAT right)
    # datasheet fig. 12-2: C_SYS (C5) against SYS/GND pins with a top-layer ground tie; ILIM/ICHG/TS resistors in a row
    # under the bottom pins, their ground straight down from GND pin 9 (analog ground, single point at the thermal pad)
    'U2': (18.6, 22.2, 0),
    'C2': (14.7, 19.2, 90), 'C3': (17.2, 17.4, 90), 'C4': (19.4, 19.05, 0), 'C7': (19.05, 17.0, 90),
    'L1': (27.9, 19.25, 0), 'C5': (22.35, 21.35, 90), 'C6': (23.45, 24.65, 270),
    'R2': (17.7, 26.0, 270), 'R3': (19.5, 26.0, 270), 'R4': (21.9, 26.0, 90), 'R5': (20.7, 26.0, 270),
    'LED1': (13.0, 26.6, 0), 'R6': (13.0, 28.0, 180),
    # ================= band B: 3.3 V buck-boost (TPS63802 rot 0: L1/L2 on the right column)
    # as datasheet fig. 12-1 / WEBENCH d36: L4 upright right of the power column (pads level with L1 / L2 pins), C_IN over
    # VIN, C_OUT under VOUT, FB / PG / EN parts on the left away from L1 / L2
    'U6': (30.0, 27.6, 0), 'L4': (34.7, 27.7, 270), 'C33': (30.2, 24.6, 180), 'C34': (30.0, 30.4, 0),
    'R24': (26.4, 28.65, 0), 'R25': (27.9, 27.85, 90), 'R26': (26.4, 29.75, 180),
    # ================= band B: protection (battery pads on the right edge)
    # FETs alternate 270 / 90 / 270 so facing columns share a net: Q3|Q2 drains (MID), Q2|Q1 sources (CELLN), Q1|J3 drains
    # (BATN); each gap is a 1.4 mm pour and the gates sit at the gap ends (Q1/Q3 top, Q2 bottom)
    'J2': (49.6, 21.6), 'J3': (49.6, 27.0),
    'F1': (43.4, 21.6, 180),
    'Q1': (46.2, 27.0, 270), 'Q2': (43.2, 27.0, 90), 'Q3': (40.2, 27.0, 270),
    'U3': (44.6, 31.0, 0), 'R7': (49.9, 29.6, 180), 'C8': (47.9, 29.6, 180), 'R8': (41.5, 31.0, 180),
    'R9': (43.4, 24.1, 0), 'R10': (44.85, 24.6, 270),
    # ================= band C: bottom-edge pads and their parts
    'J9': (4.6, 33.2), 'J10': (8.2, 33.2), 'J11': (11.8, 33.2), 'J12': (15.4, 33.2), 'J13': (19.0, 33.2),
    'J14': (22.6, 33.2), 'J8': (26.8, 33.2), 'J17': (30.8, 33.2), 'J4': (34.4, 33.2), 'J5': (38.0, 33.2),
    'R27': (5.4, 29.2, 0), 'R28': (5.4, 30.4, 0), 'C35': (7.6, 29.2, 0),
    'R29': (20.8, 29.6, 180), 'R30': (18.4, 29.6, 180), 'C36': (20.8, 28.4, 0),
}


# KiCad 10.0.1's library footprints reference 3D models that are not installed; use the JLCImport models instead.
# (file, offset xyz mm, rotation xyz deg) - offsets corrected for the KiCad footprint origin (see git log)
MODEL_OVERRIDE = {
    'Fuse_Littelfuse-NANO2-451_453': ('${KIPRJMOD}/JLCImport.3dshapes/0451010_MRL.wrl', (0.702, 0, 1.35), (0, 0, 0)),
    'USB_C_Receptacle_HRO_TYPE-C-31-M-12': ('${KIPRJMOD}/JLCImport.3dshapes/TYPE-C-31-M-12.wrl', (0, -0.879, 0),
                                            (0, 0, -180)),
}

# Solder-pad labels: ref -> (text, dx, dy[, rotation deg]) from the pad centre. Square pads = positive / signal, round = GND / negative.
_T, _B = 2.6, 2.15                    # label offset below top-edge pads / below bottom-edge pads (edge strip)
PAD_LABELS = {
    # the 5 V network fills the space under J16 / J7: labels beside the pads instead (+5V upright at the edge)
    'J6': ('+12V', 0, _T), 'J15': ('GND', 0, _T), 'J7': ('+5V', 2.0, 0, 90), 'J16': ('GND', -2.85, 0),
    'J8': ('+3V3', 0, _B), 'J17': ('GND', 0, _B),
    'J2': ('BAT+', 0, -2.9), 'J3': ('BAT-', 0, -2.25),          # both above their pads (R7/C8 sit below J3)
    'J4': ('NTC', 0, _B), 'J5': ('NTC', 0, _B),
    'J9': ('SW', 0, _B), 'J10': ('SW', 0, _B), 'J11': ('CHG', 0, _B), 'J12': ('PG', 0, _B),
    'J13': ('VBAT', 0, _B), 'J14': ('PG3', 0, _B),
}
SILK_NOTES = []

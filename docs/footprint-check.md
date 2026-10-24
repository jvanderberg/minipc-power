# Footprint checks against datasheet land patterns (2026-10-24)

Standard KiCad footprints are used wherever the package is standard (owner's rule). The part-specific imported
footprints were compared pad by pad with the datasheet's land pattern:

| Part | Footprint | Datasheet pattern | Result |
|---|---|---|---|
| TPS61178 | JLCImport:TPS61178RNWR | RNW0013A (SLVSDA7E p38) | Matches: pads 1-5 / 9-13 0.7x0.25 at 0.5 pitch, bars 6-8 3.4x0.25 at 0.55 pitch; footprint is the pattern rotated 90 deg, pin 1 consistent |
| TPS63802 | JLCImport:TPS63802DLAR | DLA0010A (p36) | Matches relative geometry (left pads 0.6, right 0.9, pad 8 1.3 wide, 0.5 pitch). Whole pattern offset +0.075 mm in x from the package centre (harmless). Pad height 0.30 vs 0.25 in TI's pattern (gap 0.20 mm) |
| CH224Q | JLCImport:CH224Q_C46061833 | CH224 DS V2.1 s9.2 DFN10 | Matches: 0.4 pitch, pin 1 bottom-left, 6-10 top row right-to-left; pads 0.22x0.51 for 0.2x0.3 leads; EP pad 1.4x0.9 for a 1.5x0.9 package pad |
| FXL0630 / FXL0530 inductors | JLCImport | FXL series datasheet | Two pads at +/-3.0 mm (0630) / +/-2.05 mm (0530); body 7.0x6.6 / 5.4x5.2 |

Courtyards were added to all imported footprints by `tools/add_courtyard.py` (pads + body + 0.25 mm).

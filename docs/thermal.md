# Thermal analysis

Added 2026-10-25. The 2026-10-24 review listed copper loss but no heat budget: the kicad-skills review had no thermal
model ("temperature rise needs judgment") and its checklist item (list every part over 0.25 W) was not done. This file
is that budget. Hand calculation from datasheet values; a layered solver is being added to kicad-skills and should
replace the board-level numbers here when it lands.

Design corner (power-design.md): closed plastic box, little or no airflow, 50 C air inside the box.

## 1. Where the heat is

Battery path resistance on the board (hot): Q1 + Q2 + Q3 CSD13202Q2 3 x 8.4 mOhm typ at Vgs 3 V x 1.3 at Tj ~100 C
(CSD13202Q2 datasheet: normalized RDS(on) vs temperature; 10.4 mOhm max at 25 C), BATFET in U2 ~24 mOhm (SLUSCK6C RON(BAT-SYS) 19.5 typ, 30 max over
temperature), F1 5.6 mOhm cold (Littelfuse 451 table) x 1.2, copper ~9.5 mOhm (power.py: 0.3 W at 5.6 A) x 1.15: about
**74 mOhm**. Battery current from I x (Vcell - I x R) = P_out / 0.92 with 25 mOhm of cells and wiring off the board
(path_budget.py's form). Converter losses from WEBENCH / power-design s4-s8; charger buck ~90 % at 9 V.

| Case | Battery A | Q1-Q3 | BATFET | F1 + Cu | Converters | Charger | **Board total** |
|---|---|---|---|---|---|---|---|
| A: 15 W out, empty cell 3.0 V | 7.2 | 1.72 W | 1.26 W | 0.92 W | 1.10 W | - | **5.0 W** |
| B: 15 W out, mid cell 3.7 V | 5.1 | 0.82 | 0.63 | 0.47 | 1.10 | - | **3.0 W** |
| C: typical 6.5 W out, 3.7 V | 2.0 | 0.13 | 0.10 | 0.07 | 0.50 | - | **0.8 W** |
| D: USB 9 V, charging 1.44 A + typical load | 1.4 (charge) | 0.06 | 0.05 | 0.03 | 0.50 | 1.40 | **2.0 W** |

The battery path, not the converters, is the largest source at high load: it grows with I^2 while the converters grow
about linearly. power-design s8 (converters only, ~1.1 W at 15 W) understated the 15 W case by a factor of 4-5.

## 2. Board temperature

Heat leaves a board in a closed box by convection and radiation from both faces. Effective h for a small board in
still air, radiation included: about 10 (pessimistic) to 20 W/m^2K. 52 x 36 mm, both faces 3.7e-3 m^2:

| h (W/m^2K) | Board to box air | A 5.0 W | B 3.0 W | C 0.8 W | D 2.0 W |
|---|---|---|---|---|---|
| 10 | 26.7 K/W | +134 K | +80 K | +21 K | +55 K |
| 15 | 17.8 K/W | +89 K | +53 K | +14 K | +37 K |
| 20 | 13.4 K/W | +67 K | +40 K | +11 K | +27 K |

Board average above the 50 C box air; the box air itself rises with the dissipation too. The wires to the pack and the
LCD conduct some heat away (not counted: optimistic for a small pack, pessimistic for a large one). Heat capacity of
board + parts ~9 J/K, so the time constant is 2-4 minutes: peaks of seconds (speaker, Wi-Fi TX) average out, minutes do
not.

What this means:
- **Typical use (C) is fine:** board ~60-70 C at 50 C box air.
- **15 W is a peak, not a continuous rating.** At B the board sits at 90-130 C; at A (empty cell) 117-184 C. The
  sustainable board loss for <= 85 C at 50 C air is 1.3-2.6 W, which is roughly **10-12 W out at a mid cell and 8-10 W
  at an empty one**. The 15 W budget (requirements s4) needs either a derate to ~10 W continuous with 15 W for short
  peaks, or a lower-loss battery path (below).
- **Charging while running in a 50 C box (D) is thermally limited.** Board 77-105 C; U2's junction adds psi-JB 9.2 C/W
  x ~1.5 W = +14 C, so U2 reaches its 110 C thermal regulation and folds the charge current back. That is safe (it is
  the designed backstop) but charging is slower. More importantly the **cells** must not be charged above 45 C (the
  BQ25606's JEITA T3 cuts the voltage to 4.05 V above 45 C and stops at 60 C only if TS sees a real NTC): fit the 103AT
  NTC on the pack, touching a cell. A fixed resistor in its place (review-2026-10-24 "other notes") disables that
  protection, which matters once the pack shares a hot box with this board.

## 3. Local hot spots

| Part | Heat path | At B | At A |
|---|---|---|---|
| Q1-Q3 (SON 2x2) | own F.Cu pours only (MID 10, CELLN 13, BATN 16 mm^2; not GND, so no vias to the plane): through 0.21 mm prepreg to In1, ~13 K/W for the group of three, plus RthJC 6.4 C/W each. The datasheet's 60 C/W RthJA assumes 1 in^2 of 2 oz copper; on minimum copper it gives 210 C/W | Tj ~ board + 13 K | Tj ~ board + 26 K: over the 150 C limit at h <= 15 |
| U2 (BQ25606) | EP with 9 thermal vias to In1 (the footprint's pattern); BATFET + buck in one die | board + psi-JB x P | board + 1.26 W x 9.2 ~ +12 K |
| U5 (TPS61088-Q1) | EP with 8 thermal vias, PGND5 pour (34 mm^2), NC 11/12 now on GND | WEBENCH Tj 74-78 C at 25 C air: add the board rise instead | |
| U4, U6 | no EP (bar pins / centre via); losses 0.33 / 0.48 W at their corners | | |

## 4. Stitching vias: what they do and do not do here

Without any via, the dielectric itself couples the layers: F.Cu GND to In1 0.6 K/W over its 960 mm^2, In1 to In2
1.6 K/W and In2 to B.Cu 0.3 K/W over the board. Those are small next to the 13-27 K/W from the board to the air, so
**stitching does not lower the board temperature**; it helps local spreading (a hot part's copper into the planes) and,
mainly, the ground return and emissions at the edge.

The board had 48 GND vias, almost all at capacitor pads: 6 within 3 mm of the edge on a 174 mm perimeter, edge gaps
of 57 / 42 / 41 / 19 mm (planes.py). route_plan.stitch_grid() now adds a GND via ring along the edge (4 mm pitch) and a
5 mm interior grid wherever both outer layers are GND pour (never in another net's pour, an AGND keepout or between a
part's pads), plus a second via at the two capacitor-pad islands that had one. Result (planes.py): 46 vias added (145 in all), 34 GND vias within 3 mm of the edge (was 6), longest edge
gap 17 mm (was 57; the rest sit where the battery, +5 V and bottom-edge pads take the edge), no GND piece left on a
single via (was 2). DRC, ERC, board_lint, pin and field checks clean; VSYS and ground-return drops unchanged or lower.

## 5. Options to lower the heat (owner decisions)

- Derate: 10 W continuous, 15 W peaks of under a minute (requirements s4, power-design s8).
- Drop Q1 (reverse-block) if the pack is keyed and pre-wired (it is there because loose cells are soldered to
  the pads; see power-design s3): -1/3 of the FET loss, 0.57 W at A.
- Lower-RDS(on) protection FETs in a package with a real drain pad (e.g. SON 3.3 x 3.3, ~3-4 mOhm at Vgs 3 V): the
  three FETs' 1.72 W at A drops to ~0.7 W, and the larger pads spread it.
- Copper for the protection chain on B.Cu too (same-net pours under Q1-Q3, joined by via arrays): doubles their spreading
  area; needs the BAT pour and the EN / TS / Q3-gate tracks moved.
- The BATFET (in U2, 1.26 W at A) is fixed by the charger choice; only a lower battery current helps (derate, or a
  higher cell voltage window).

## 6. Bench checks

Thermocouple or IR camera on Q1-Q3, U2, U5 and the board centre, in the closed box: (1) 15 W for 10 minutes from a
3.3 V-equivalent cell (current-limited supply through the pack pads), (2) charging at 1.44 A with the typical load,
box at room temperature first, then in a warm place. Record when U2 starts thermal regulation (charge current drops).

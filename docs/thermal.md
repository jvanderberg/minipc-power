# Thermal analysis

Added 2026-10-25. The 2026-10-24 review listed copper loss but no heat budget: the kicad-skills review had no thermal
model ("temperature rise needs judgment") and its checklist item (list every part over 0.25 W) was not done. This file
is that budget. Hand calculation from datasheet values; a layered solver is being added to kicad-skills and should
replace the board-level numbers here when it lands.

Design corner (power-design.md): closed plastic box, little or no airflow, 50 C air inside the box.

## 1. Where the heat is

Battery path resistance on the board (hot): Q1 + Q2 + Q3 DMN1004UFV 3 x ~3.1 mOhm typ at Vgs 3 V (datasheet: 3.2 typ /
5.1 max at 2.5 V, 2.8 / 3.8 at 4.5 V) x 1.3 at Tj ~100 C, BATFET in U2 ~24 mOhm (SLUSCK6C RON(BAT-SYS) 19.5 typ, 30 max
over temperature), F1 5.6 mOhm cold (Littelfuse 451 table) x 1.2, copper ~8.5 mOhm (power.py runs) x 1.15: about
**53 mOhm**, of which the FETs are 12. Until 2026-10-25 the FETs were CSD13202Q2 (8.4 mOhm typ at 3 V each, 33 of a
74 mOhm path); the "was" rows below are that board. Battery current from I x (Vcell - I x R) = P_out / 0.92 with 25 mOhm of cells and wiring off the board
(path_budget.py's form). Converter losses from WEBENCH / power-design s4-s8; charger buck ~90 % at 9 V.

| Case | Battery A | Q1-Q3 | BATFET | F1 + Cu | Converters | Charger | **Board total** | was |
|---|---|---|---|---|---|---|---|---|
| A: 15 W out, empty cell 3.0 V | 6.6 | 0.53 W | 1.06 W | 0.73 W | 1.10 W | - | **3.4 W** | 5.0 W (Q1-Q3 1.72) |
| B: 15 W out, mid cell 3.7 V | 4.9 | 0.28 | 0.59 | 0.40 | 1.10 | - | **2.4 W** | 3.0 W |
| C: typical 6.5 W out, 3.7 V | 2.0 | 0.05 | 0.10 | 0.07 | 0.50 | - | **0.7 W** | 0.8 W |
| D: USB 9 V, charging 1.44 A + typical load | 1.4 (charge) | 0.02 | 0.05 | 0.03 | 0.50 | 1.40 | **2.0 W** | 2.0 W |

The battery path, not the converters, is the largest source at high load: it grows with I^2 while the converters grow
about linearly. power-design s8 (converters only, ~1.1 W at 15 W) understated the 15 W case by a factor of 3-5. With
the DMN1004UFV the BATFET inside U2 (fixed by the charger choice) is now the largest single source.

## 2. Board temperature

Heat leaves a board in a closed box by convection and radiation from both faces. Effective h for a small board in
still air, radiation included: about 10 (pessimistic) to 20 W/m^2K. 52 x 36 mm, both faces 3.7e-3 m^2:

| h (W/m^2K) | Board to box air | A 3.4 W | B 2.4 W | C 0.7 W | D 2.0 W |
|---|---|---|---|---|---|
| 10 | 26.7 K/W | +91 K | +64 K | +19 K | +55 K |
| 15 | 17.8 K/W | +61 K | +43 K | +12 K | +37 K |
| 20 | 13.4 K/W | +46 K | +32 K | +9 K | +27 K |

h is the dominant uncertainty. kicad-skills' layered thermal solver (branch `thermal`, not merged yet) defaults to
h = 5-10 W/m^2K for a closed box, which roughly doubles these rises; the bench check (s6) settles it.

Board average above the 50 C box air; the box air itself rises with the dissipation too. The wires to the pack and the
LCD conduct some heat away (not counted: optimistic for a small pack, pessimistic for a large one). Heat capacity of
board + parts ~9 J/K, so the time constant is 2-4 minutes: peaks of seconds (speaker, Wi-Fi TX) average out, minutes do
not.

What this means:
- **Typical use (C) is fine:** board ~60-70 C at 50 C box air.
- **15 W is still a peak, not a continuous rating.** At B the board sits at 82-114 C; at A (empty cell) 96-141 C
  (was 90-130 / 117-184 C with the CSD13202Q2). The sustainable board loss for <= 85 C at 50 C air is 1.3-2.6 W,
  roughly **10-15 W out at a mid cell and 8-12 W at an empty one**, at the h above. Treat 10 W continuous with 15 W for
  short peaks as the rating until the bench check.
- **Charging while running in a 50 C box (D) is thermally limited.** Board 77-105 C; U2's junction adds psi-JB 9.2 C/W
  x ~1.5 W = +14 C, so U2 reaches its 110 C thermal regulation and folds the charge current back. That is safe (it is
  the designed backstop) but charging is slower. More importantly the **cells** must not be charged above 45 C (the
  BQ25606's JEITA T3 cuts the voltage to 4.05 V above 45 C and stops at 60 C only if TS sees a real NTC): fit the 103AT
  NTC on the pack, touching a cell. A fixed resistor in its place (review-2026-10-24 "other notes") disables that
  protection, which matters once the pack shares a hot box with this board.

## 3. Local hot spots

| Part | Heat path | At B | At A |
|---|---|---|---|
| Q1-Q3 (DMN1004UFV, PowerDI3333-8) | own-net pours on F.Cu (MID ~20, CELLN ~5, BATN ~25 mm^2) with same-net islands on B.Cu under them (MID_B, CELLN_B, BATN_B), joined by 13 vias in the gaps between the pads and by J3's barrel; not GND, so no vias to the plane, but both faces now couple to the inner planes through 0.21 mm prepreg. RthJC 3.4 C/W each | 0.09 W each: Tj ~ board + 2 K | 0.18 W each: Tj ~ board + 4 K (was 0.57 W each, +26 K, over 150 C at h <= 15) |
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

## 5. Options to lower the heat

Done (2026-10-25):
- Lower-RDS(on) protection FETs: DMN1004UFV (C316138) in PowerDI3333-8, 3.4 C/W to the drain pad. Q1-Q3 at A: 1.72 W ->
  0.53 W; board 5.0 -> 3.4 W. The protection block was re-laid out (power-design s3, layout-compliance). A Vishay
  SiSS80DN (2.0 mOhm at 2.5 V) was chosen first, then dropped: it is stocked on LCSC China only, not for JLCPCB global
  assembly. The protector stays HY2113-MB1A (its trip moves up, power-design s3).
- Same-net copper on B.Cu under Q1-Q3, joined by vias.

Still open (owner decisions):
- Derate: 10 W continuous, 15 W peaks of under a minute (requirements s4, power-design s8).
- Drop Q1 (reverse-block) if the pack is keyed and pre-wired (it is there because loose cells are soldered to
  the pads; see power-design s3): -1/3 of the FET loss, ~0.18 W at A.
- The BATFET (in U2, 1.06 W at A) is fixed by the charger choice; only a lower battery current helps (derate, or a
  higher cell voltage window).

## 6. Bench checks

Thermocouple or IR camera on Q1-Q3, U2, U5 and the board centre, in the closed box: (1) 15 W for 10 minutes from a
3.3 V-equivalent cell (current-limited supply through the pack pads), (2) charging at 1.44 A with the typical load,
box at room temperature first, then in a warm place. Record when U2 starts thermal regulation (charge current drops).

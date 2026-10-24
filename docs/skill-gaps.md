# kicad-skills gaps found while designing minipc-power

Running log of problems found in https://github.com/jvanderberg/kicad-skills (commit 3ba7b5f) while using it on this
board: things the skills miss, get wrong, or state without support. Each entry names the skill/file, what happened,
and a suggested fix.

Severity: **high** = would lead to a wrong or unsafe design if followed; **medium** = missing guidance that cost real
time or needed outside knowledge; **low** = friction, wording, tooling.

## Planning / interview (kicad-new-board)

1. **medium - No path for multi-amp 1S boards (power banks, handhelds).** `pcb-battery-power/SKILL.md` s4 makes a
   *linear* charger with power path the default for USB-powered 1S boards, and the scope note jumps from "1S hobby"
   straight to "tens of amps / e-bike packs - use a certified BMS". A 1S2P 18650 pack feeding a 5 V + 12 V boost at
   ~10-15 W (3-5 A from the cell) sits in between and is a very common hobby build (handheld emulators, portable
   displays, power banks). Nothing covers: switching NVDC chargers (BQ25895-class), power-bank SoCs (IP53xx, SW62xx),
   protector overcurrent thresholds vs a multi-amp boost load, or cell-current/derating for parallel cells.
   *Fix:* a "high-power 1S" section: switching charger with NVDC power path, protector + FET sized for boost peak
   current, parallel-cell matching, boost-from-cell current math (Iin = Pout / (eff x Vcell_min)).

2. **medium - The 15 W ceiling of 5 V USB-C is never applied to "charge while running".** `charging.md:102` says
   PD is needed above 15 W, but neither the interview guide nor the battery skill tells the planner to add the
   system load to the charge power and compare with what the input can deliver. Interview default "5 V, up to 1.5 A"
   (7.5 W) is below this board's load alone, so the default would have produced a board that discharges while
   plugged in. *Fix:* in interview step 4, require input power >= (system peak / eff) + (charge current x 4.2 V / eff)
   and recommend a PD sink when it fails.

3. **low - Interview has no "heat / enclosure thermal budget" question.** Size is asked, but "small sealed enclosure,
   must stay cool" was volunteered by the user and changes topology (switching vs linear charger, synchronous boosts,
   charge current limit). *Fix:* add "how hot may the board/box get, is there airflow?" to section 2 with a default.

## Battery / charging (pcb-battery-power)

5. **medium - PD sink coverage is one line, and misses the charger/PD interaction.** `charging.md:102` says "use a
   PD sink controller" and stops. Missing: (a) a charger's VINDPM (BQ25606: fixed 4.3 V / VBAT+200 mV) does nothing to
   protect a 9 V PD source, so the charger's input current limit must be at or below the negotiated PDO current
   (an 18 W charger gives 9 V / 2 A); (b) what the sink does when the requested voltage is not offered (CH224Q's
   datasheet does not say) and what input limit is safe then; (c) BC1.2-detecting chargers (BQ25606, BQ25895) only
   use the ILIM resistor when D+/D- detection returns "unknown" [BQ25606 s9.3.2.3], so whether D+/D- are wired to
   the connector changes the input limit. *Fix:* a "PD sink + charger" subsection covering these three.

6. **medium - Nothing on parallel cells (1SnP).** `chemistries.md` covers buying genuine 18650s but not paralleling
   them: same model/age, matched capacity, joined at the same voltage (or through a resistor) to avoid a large
   equalising current, one protector for the parallel group, per-cell current = pack current / n. *Fix:* a short
   section in `chemistries.md` or `protection-and-safety.md`.

7. **low - Protector trip current ignores gate drive.** `protection-and-safety.md:17` gives
   I_trip = V_OCD / (Rds,CHG + Rds,DSG), which is right, but the FETs in a DW01/HY2120 circuit are driven at roughly
   the cell voltage, so Rds(on) must be read at Vgs ~ 3 V (empty cell), not the 4.5 V headline figure - the trip
   current falls as the cell empties and the 8205A-class FETs trip around 3-5 A. *Fix:* add "read Rds(on) at
   Vgs = cell minimum" and a sizing example for a multi-amp load.

8. **low - Standalone vs I2C-default chargers not compared.** The battery skill names BQ2407x (linear), BQ25185 and
   BQ25895 (I2C) but not the standalone switching family (BQ25606/BQ25616: resistor-set ICHG/ILIM, no host). The
   power-supply skill's "startup independence" rule is the deciding argument and the battery skill should cross-link
   it: a charger that needs I2C cannot be configured by an MCU that it powers. *Fix:* add the standalone switching
   option to the charger-selection table in `charging.md`.

## Power design (pcb-power-supply)

9. **medium - WEBENCH is offered too late and too quietly.** The WEBENCH step is in `pcb-power-supply/SKILL.md` s3
   ("Choose the controller IC"), mid-paragraph. In practice the controller was chosen during kicad-new-board step 8
   (candidates) with pcb-part-selection, and the agent went straight to hand calculations from the datasheet; the user
   had to ask "do we have any tools for TI?" before WEBENCH was used. Neither kicad-new-board's component-selection
   step nor pcb-part-selection mentions it. *Fix:* in kicad-new-board step 8 and pcb-part-selection "Finding
   candidates", say: for any switching regulator, run WEBENCH (ask the user about the terms and a myTI login up front)
   *before* settling on a part and before hand sizing; make it a checklist item at the top of pcb-power-supply rather
   than a bullet inside s3. Also say plainly that WEBENCH does not cover battery chargers (BQ25xxx), so those stay
   datasheet-only.

10. **medium - WEBENCH results are not stock-filtered before use.** `webench.md` mentions "WEBENCH does not know what
    is in stock at JLC/LCSC" only in its last section, after the steps that pick and customize a design. On this
    board the 5 V run's top three (TPS61022, TPS61230A, TPS61236P) had 0 / 0 / 13 units in LCSC's global warehouse.
    Customizing any of them would have been wasted work. *Fix:* make the stock check step 2 of the WEBENCH flow: read
    the table view, pull every part number, run them through `jlcimport-cli search --region global` in one batch,
    and drop anything below the order quantity before opening Customize. A small script that takes the table text and
    prints stock per part would make this one command.

11. **low - WEBENCH can refuse a part the datasheet allows, without saying why.** Forcing TPS61178 at 3.0-4.35 V in,
    5 V / 2.5 A out returned "Design cannot be created! Your preferred device does not work with the inputs you
    selected" with no reason, although the datasheet allows 4.5-20 V out from 2.7 V in. `webench.md` does not say what
    to do then (vary Iout / Vin to find the limit, or fall back to the datasheet procedure). *Fix:* add a line on that.

12. **high (wrong statement) - "there is no KiCad/CAD export there" is false, and the PCB layout tab is not
    mentioned.** `webench.md` ("Export" paragraph) says the Export page has "no KiCad/CAD export". On 2026-10-24 the
    Export page offers **Altium Designer, Cadence OrCAD, TINA-TI, CadSoft EAGLE, Mentor Graphics and P-CAD** exports
    ("schematic, board, and simulation files"), and KiCad 10's `kicad-cli pcb import --format eagle|altium|pcad`
    reads three of those. Customize and Export also show a **PCB LAYOUT** tab with a per-layer reference layout
    (Top / Mid 1 / Mid 2 / Bottom). Following the skill, the agent skipped both and would have hand-placed every
    converter's hot loop instead of starting from TI's layout. *Fix:* replace the sentence; add a step: capture the
    PCB LAYOUT views for each chosen design and, with the user's permission to download, export EAGLE (or Altium),
    import with `kicad-cli pcb import`, and use the copper as the placement/routing reference for that converter
    (re-check against the datasheet layout guidelines; WEBENCH layouts use its own BOM footprints).

13. **medium - No "layout reference pack" step, and no stated order of authority between layout sources.**
    `pcb-power-supply` s6 says "copy the datasheet's layout example; then check against references/layout.md", and
    nothing else. Before placing any converter the skill should have the agent gather, per IC, into the project
    (e.g. `docs/layout-refs/<part>/`): (1) the datasheet's Layout Guidelines text and Layout Example figure (rendered
    with pdftoppm) - **primary, these win any conflict**; (2) the EVM user guide's layout if one exists; (3) the
    WEBENCH PCB LAYOUT views and imported EAGLE/Altium board - **reference only**, because they are drawn around
    WEBENCH's BOM (different inductor/capacitor sizes from the stocked LCSC substitutes) and a generic stackup.
    Then write down, per converter, the hot loop, the parts that must sit at the pins, the quiet-side parts, the
    feedback routing and the thermal-pad via count, and check the KiCad placement against that list. *Fix:* add
    this as a numbered step before s6 "Lay it out", and have kicad-pcb-workflow s1 ("Plan the change against real
    data") point to it for any switching converter.

## Part selection (pcb-part-selection)

14. **high - No lifecycle (NRND/EOL) check, and distributor stock hides discontinued parts.** kicad-new-board step 8
    says "avoid NRND/EOL parts" but neither it nor pcb-part-selection says how to check. On this board WEBENCH
    recommended the TPS61088 (5 V boost) and LCSC listed 7,130 in stock, but ti.com/product/TPS61088 and its
    datasheet symlink both return 404 and TI's site search does not find it; only the automotive TPS61088-Q1 is
    still listed (ACTIVE). Stock at a distributor is not evidence that a part is still made. WEBENCH's own tell was
    "IC Cost: N/A" for that part (every active part showed a price). *Fix:* add to pcb-part-selection "Reading the
    datasheet": open the manufacturer's product page and record the lifecycle status (ACTIVE / NRND / LAST TIME BUY
    / OBSOLETE); a 404 product page or a missing datasheet link means treat as obsolete; and in webench.md, treat
    "IC Cost: N/A" as a lifecycle warning.

## Tooling

15. **low - render.py cannot render a board without an Edge.Cuts outline, even with --window.** It exits with "no
    Edge.Cuts outline found", which blocks rendering imported reference boards (the WEBENCH EAGLE imports have no
    outline). *Fix:* when --window is given, use it and skip the outline lookup.

4. **low - `jlcimport-cli` install not documented.** README lists it as a requirement with only a repo link. The
   repo's pyproject needs a modern pip (system Python 3.9 / pip 21 cannot do `pip install -e` on it) and a stale
   PyInstaller build in `dist/` lacks `--region`, which the skill's commands use. *Fix:* give the install command
   (`pipx install git+https://github.com/jvanderberg/kicad_jlcimport` or a venv with Python >= 3.11) and the minimum
   version that has `--region`.

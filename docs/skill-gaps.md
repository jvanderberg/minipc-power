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

## Tooling

4. **low - `jlcimport-cli` install not documented.** README lists it as a requirement with only a repo link. The
   repo's pyproject needs a modern pip (system Python 3.9 / pip 21 cannot do `pip install -e` on it) and a stale
   PyInstaller build in `dist/` lacks `--region`, which the skill's commands use. *Fix:* give the install command
   (`pipx install git+https://github.com/jvanderberg/kicad_jlcimport` or a venv with Python >= 3.11) and the minimum
   version that has `--region`.

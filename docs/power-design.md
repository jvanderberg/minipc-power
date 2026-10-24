# minipc-power - power design

Revision 1 - 2026-10-24. Every value traces to a datasheet equation or a WEBENCH design (designs saved under the
owner's myTI account; numbers copied to `docs/webench/`). Datasheets read: BQ25606 (SLUSCK6C), TPS61178 (SLVSDA7E),
TPS61088-Q1 (SLVSE52A), TPS63802, CH224Q (WCH, Chinese), HY2113 (DS-HY2113-V16), CSD13202Q2, CSD25404Q3, FXL series
inductors. Stock checked with `jlcimport-cli --region global` on 2026-10-24; re-check before ordering.

Design corner: empty cell 3.0 V, ambient 50 C (closed box), each rail at its rated current. The combined output budget
is 15 W (requirements s4); the per-rail corners below do not all happen at once.

## 1. Input: USB-C + PD sink

| Item | Value | Basis |
|---|---|---|
| J1 | TYPE-C-31-M-12 (C165948, 325k stock) | 16-pin SMD receptacle, 5 A |
| U1 | CH224Q (C46061833) | PD 3.2 sink, also BC1.2/QC on D+/D- |
| Request | 9 V | R_CFG1 = **6.8 k** to GND (CH224Q table 5-1); CFG2/CFG3 floating |
| VHV / VBUS pins | tied together, 1 uF to GND (25 V) | CH224Q pin table: "VBUS needs to be shorted to VHV" |
| PG | not used (pad optional) | open drain, active low |
| D+/D- | **not connected** (connector and CH224Q) | PD negotiates on CC1/CC2. CH224Q's DP/DM only add BC1.2/QC requests; dropped because its 0.4 mm-pitch inner pins cannot be routed beside CC1/CC2 without crossings. Effect: a QC-only (non-PD) charger stays at 5 V. The charger's D+/D- stay open (s2) |
| TVS | SMF12A (C123800): 12 V standoff, 13.3-14.7 V breakdown, 19.9 V clamp | below BQ25606 VBUS/VAC abs max 22 V; CH224Q VBUS abs max 32 V |

If the charger has no 9 V PDO, the CH224Q stays at 5 V (behaviour not stated in its datasheet - bench-check).

## 2. Charger: BQ25606 (standalone, NVDC)

| Item | Value | Basis |
|---|---|---|
| U2 | BQ25606RGER (C374063, 8,201 stock) | 3.9-13.5 V in, 22 V abs max; ACOV 13.5/14.28/14.91 V |
| Charge voltage | VSET floating -> **4.208 V** | VSET table (RPD > 50 k = float) |
| Charge current | R_ICHG = **453 R** -> 1.41 / **1.49** / 1.58 A | ICHG = KICHG / R, KICHG 639/677/715 A.Ohm |
| Input current limit | R_ILIM = **249 R** -> 1.84 / **1.92** / 2.01 A | IINDPM = KILIM / R, KILIM 459/478/500; must stay <= the 9 V PDO current (2 A on an 18 W charger) because VINDPM (4.3 V / VBAT+200 mV) does not protect a 9 V source |
| D+ / D- | **floating** | ILIM applies only when detection returns "unknown adapter" (s9.3.2.3); a D+/D- short would read as DCP = 2.4 A |
| TS (NTC) | RT1 = **5.23 k** (REGN-TS), RT2 = **30.9 k** (TS-GND), 103AT 10 k B3435 on pads | datasheet s9.3.5.4, 0-60 C window; JEITA cuts current below 10 C / voltage above 45 C |
| Inductor | **2.2 uH**, FXL0630-2R2-M (C167218): 15 mOhm, I_sat 10.5 A (30 % drop) | ripple 0.66 A at 9 V, 0.29 A at 5 V (fs 1.5 MHz); I_sat > IHSFET_OCP max 8.0 A |
| PMID cap | 10 uF 25 V | datasheet; input hot loop is PMID-GND |
| VBUS cap | 1 uF 25 V at pin | |
| SYS cap | 10 uF (total effective on VSYS <= ~20 uF, see note) | internal compensation optimised for <= 20 uF |
| BAT cap | 10 uF 10 V | |
| REGN | 4.7 uF 10 V | |
| BTST | 47 nF | |
| STAT | red LED + 1 k to VSYS (on while charging), and a pad | sink 6 mA abs max |
| PG | pad (open drain, MCU pull-up) | |
| OTG | to GND (boost mode off) | "OTG cannot be floating" |
| CE | to GND (charge enabled) | |

VSYS capacitance note: the charger's loop is compensated for <= 20 uF of ceramic on SYS. VSYS also carries the three
converters' input capacitors; their *effective* capacitance at 4 V (10 V 0603/0805 parts lose about half) must be
counted. Plan: 10 uF at SYS + converter inputs as specified below; total effective about 25-30 uF. On the bench,
check VSYS for ringing at charge start and on a load step; if it rings, move part of the converter input capacitance
behind a 0.1 Ohm / ferrite.

Heat (9 V in, 1.5 A charge + ~1.5 A system): buck efficiency ~90 % -> about 1 W in the BQ25606; 110 C thermal
regulation folds the charge current back if the box gets hot.

## 3. Cell protection and reverse connection

Order from the battery pads: B- pad -> **Q1 reverse-block** -> CELL- (protector VSS) -> **Q2 discharge, Q3 charge**
(common source, back-to-back) -> GND. B+ pad -> **F1** -> BAT (charger BAT pin, protector VDD via R).

| Item | Value | Basis |
|---|---|---|
| U3 | HY2113-MB1A (C168772) | 1-cell: VCU 4.280 +/-0.025, VDL 2.80 +/-0.05, VDIP 250 +/-15 mV, VCIP -100 mV, short 0.85 V; TDIP 12 ms, TSIP 300 us |
| R (VDD) / C (VDD) | 330 R / 100 nF | HY2113 connection example (100-470 R, 0.01-1 uF) |
| R (CS) | 2 k | HY2113 connection example |
| Q1, Q2, Q3 | CSD13202Q2 (C187839, 2,233 stock): 12 V, +/-8 V Vgs, 8.4 / 10.4 mOhm at Vgs 3 V | one part for all three |
| Discharge trip | 250 mV / (Q2 + Q3) | at 25 C typ: ~15 A; at 3.0 V cell, max Rds, hot (x1.4): ~8 A. Above the ~5.6 A design peak |
| Q1 gate | 10 k from B+ pad, 1 M gate-source | reversed pack: Vgs < 0, body diode reverse-biased, nothing conducts; HY2113 never sees reverse voltage |
| F1 | Littelfuse 0451010.MRL, 10 A Nano2 2410 (C44479) | backup only if the protector fails short; protector trips first (12 ms) |

Note: an earlier candidate, HY2120, was a **2-cell** protector (caught from its datasheet title and VC pin) - not used.

Battery wiring: 18 AWG-20 AWG to the pads; cells bought as a matched pair, joined at the same voltage.

## 4. 12 V rail: TPS61178 (WEBENCH design 33)

| Item | Value | Basis |
|---|---|---|
| U4 | TPS61178RNWR (C127918, 6,745 stock) | 20 V sync boost, 16 mOhm FETs, DISDRV |
| fsw | R_FREQ = **169 k** -> 0.99 MHz | WEBENCH; eq. 2 |
| Current limit | R_ILIM = **162 k** -> 4.6 A (eq. 1, 745/R); datasheet table suggests the equation reads ~15 % high, so ~4.0 A typ, ~2.6 A min | needed peak 2.31 A (WEBENCH, 3.0 V / 0.5 A) |
| Inductor | **3.3 uH**, FXL0630-3R3-M (C167219): 22 mOhm, I_sat 8.7 A | WEBENCH 2.7 uH; 3.3 uH within the 0.47-3.3 uH range, ripple ~0.7 A; I_sat > ILIM max (~6.2 A) |
| Cin | 2 x 22 uF 10-16 V 0805/1206 (input <= 4.35 V) | WEBENCH 2 x 22 uF 1210 (36 uF derated); input ripple current only 0.12 A RMS |
| Cout1 (before FET) | 4.7 uF 25 V 1206 | WEBENCH; COUT2 <= 10 x COUT1 (inrush rule) |
| Cout2 (after FET) | 3 x 22 uF 25 V 1210 (31 uF effective at 12 V) | WEBENCH; COUT2 31 uF <= 10 x COUT1 (32 uF) |
| FB | R_top **732 k** / R_bot **80.6 k** -> 12.08 V | VFB 1.198 V |
| Compensation | Rc **44.2 k**, Cc **1.8 nF**, no Cp | WEBENCH: PM 54.9 deg, fc 13 kHz at 3 V |
| Disconnect FET | CSD25404Q3 (C2865523): -20 V, 10.1 mOhm at -2.5 V | WEBENCH M3 |
| Rgate / Cgate | **178 k / 22 nF** | Vgs = 178 k x 55 uA = 9.8 V (< 12 V abs); turn-on ~0.5 ms (< 3 ms) |
| VCC / BST | 4.7 uF / 100 nF | datasheet s9.2.4.4.4-5 |
| EN | from EN net | VEN_H 1.2 V max |

Output capacitor note: the WEBENCH compensation assumed 31 uF effective after the FET. If the final output capacitance
differs, recheck the loop with WEBENCH (Customize -> output cap) before ordering. The LCD board adds its own input
capacitance after the pads (unknown; typically 10-100 uF) - this is outside the 10 x COUT1 rule; the slow Cgate turn-on
limits that inrush.

Loss at corner: 0.33 W total (IC 0.25 W, L 0.08 W); Tj 57 C (WEBENCH, theta-JA 28.5 C/W).

## 5. 5 V rail: TPS61088-Q1 (WEBENCH design 37)

| Item | Value | Basis |
|---|---|---|
| U5 | TPS61088QRHLRQ1 (C1850341, 442 stock, ACTIVE) | commercial TPS61088 appears discontinued |
| fsw | R_FREQ = **267 k** (FSW to SW) -> 594 kHz | eq. 2 |
| Current limit | R_ILIM = **69.8 k** -> 7.9 A typ, ~6.9 A min, ~9.0 A max (MODE floating, PFM) | ILIM = 550000 / R; spread from the 49.9 k table row |
| Inductor | **1.0 uH**, FXL0630-1R0-M (C167216): 7.4 mOhm, I_sat 13.5 A | WEBENCH 1 uH / 11 mOhm; I_sat > 9.0 A |
| Cin | 3 x 10 uF 16 V 0805 + 100 nF | WEBENCH |
| Cout | 2 x 47 uF 16 V 1210 (63 uF effective) | WEBENCH |
| FB | **220 k / 69.8 k** -> 5.00 V | |
| Compensation | Rc **28.7 k**, Cc **680 pF**, Cp **33 pF** (0402) | WEBENCH: PM 55.1 deg, fc 34 kHz |
| SS | 8.2 nF -> 2.0 ms | t = 1.204 x C / 5 uA |
| VCC / BOOT | 2 x 1 uF / 100 nF | |
| MODE | floating (PFM at light load) | ILIM equation above assumes MODE floating |
| Disconnect | Q5 CSD25404Q3 P-FET (source = boost VOUT, drain = 5V pad); Q6 2N7002 pulls the gate low when EN is high; 100 k gate-source, 10 nF gate-source for soft turn-on | TPS61088 has no load-disconnect |

Loss at corner (3.0 V, 2.5 A): ~0.88 W total, IC Tj ~74-78 C. Typical (3.7 V, 1 A) is a fraction of that.

## 6. 3.3 V rail: TPS63802 (WEBENCH design 36)

| Item | Value | Basis |
|---|---|---|
| U6 | TPS63802DLAR (C2845237, 37,457 stock) | buck-boost, 1.3-5.5 V in, current limit 4.0-5.75 A (boost) |
| Inductor | **0.47 uH**, MWSA0402S-R47MT (C6331050): 14 mOhm, I_sat 7.5 A, 4.4 x 4.2 mm | datasheet 0.37-0.57 uH effective; I_sat > 5.75 A |
| Cin | 22 uF 6.3-10 V 0603/0805 (>= 4 uF effective) | |
| Cout | 22 uF 10 V 0805 (11 uF effective; >= 7 uF required) | |
| FB | **511 k / 91 k** -> 3.31 V | VFB 0.5 V |
| MODE | GND (power-save at light load) | |
| PG | 100 k pull-up to 3V3, to a pad | |

Loss at corner (3.0 V, 1.5 A): 0.48 W, Tj 66 C.

## 7. Enable, status, sense

| Item | Value |
|---|---|
| EN net | pads EN and VSYS for a SPST switch; 100 k EN-GND (off by default); 1 k series from the pad + 100 nF to GND (ESD/bounce). Drives U4 EN, U5 EN, U6 EN and Q6 gate. Thresholds: 1.2 V max high on all three; VSYS 3.0-4.35 V |
| VBAT sense | 470 k / 1 M from BAT -> VBAT_SENSE pad (2.96 V at 4.35 V), 100 nF; 3 uA drain |
| Status pads | CHG (STAT, LED pull-up to VSYS -> pad up to ~2.5 V), PG (open drain), 3V3_PG |
| Test points | VBUS, VSYS, BAT, 5V, 12V, 3V3, GND |

## 8. Totals at the corner (all rails at rated current, 3.0 V cell - not a real operating point)

| Rail | Pout | Loss |
|---|---|---|
| 12 V | 6 W | 0.33 W |
| 5 V | 12.5 W | 0.88 W |
| 3.3 V | 4.95 W | 0.48 W |
| Sum | 23.5 W (budget 15 W) | 1.7 W |

At the 15 W budget the converter losses are about 1.1 W; plus the charger (~1 W) only while charging from USB.

## 9. Bench verification required (not optional)

Charge profile with real cells (CC 1.5 A, CV 4.208 V, termination); TS cut-off with resistors in place of the NTC;
protector short-circuit response on a current-limited supply first; each rail's ripple, load step and start-up at 3.0
and 4.2 V; hot-plug of a 9 V PD charger and of a 5 V-only charger; VSYS stability at charge start; case temperatures at
full load in the enclosure.

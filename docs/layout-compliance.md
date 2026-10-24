# Layout compliance: each block checked against its datasheet layout rules

Every routed block is checked against `docs/layout-refs/<part>/` (datasheet section and figure first, WEBENCH board
as a secondary reference) in a net-coloured render (`view.py`) before the next block is started. DRC is not enough:
it was clean while two of the charger rules below were broken (skill-gaps.md, gap 21).

## BQ25606 charger (datasheet s12, fig. 12-2)

| Rule | Status |
|---|---|
| C_PMID (C3) at PMID with the shortest path to GND | ok: C3 on PMID pin 23, its GND pad has a via beside it |
| Inductor right at SW, SW copper small, no parallel SW layers | ok: SW is a single F.Cu pour from pins 19/20 to C4 and L1 (~4 mm, 1.6 mm longer than ideal because the FXL0630 courtyard forced L1 right to make room for C_SYS). In1 GND sits under it, nothing else on SW |
| C_SYS at SYS pins, ground tied short to IC ground | **fixed**: C5 now stands at pins 15/16 with its GND pad tied to GND pin 18 on F.Cu (was 4 mm away, returning through the plane) |
| C_BAT near BAT pins, ground short | ok: C6 under the BAT bar, GND via at its pad |
| REGN, BTST, VBUS caps at their pins | ok: C7, C4, C2 |
| Analog ground separate, joined to power ground at the thermal pad only | **fixed**: R2/R3/R5 grounds on their own track to GND pin 9, then into the EP; F.Cu pour keepout `AGND_CHG` around them; no plane vias (was stitched to the plane and flooded by the pour) |
| Thermal pad vias to the inner GND plane | ok: footprint's 9 thermal vias |
| Vias sized for charge + system current | ok: BAT 2 vias at the IC plus a 20 x 3.6 mm B.Cu pour, 6 vias at the fuse; VSYS on the In2 plane |

## CH224Q PD sink (no layout section)

| Rule | Status |
|---|---|
| CC1/CC2 short to the connector | ok: 2-3 mm, CC2 crosses CC1 on B.Cu |
| VHV/VBUS caps at the pins | ok: C1 on VHV pin 1 |
| ESD at the connector | ok: D1 SMF12A on the VBUS pour next to J1 |

## Protection (HY2113 datasheet application circuit; no layout section)

| Rule | Status |
|---|---|
| High-current path wide and short | ok: FETs alternate orientation so each link is a 1.4 mm pour gap (MID, CELLN, BATN). BAT goes through the fuse vias to the B.Cu pour |
| VDD RC filter at the IC | ok: R7/C8 next to U3 VDD/VSS |
| CS resistor at the CS pin | ok: R8 |

## TPS61178 12 V boost (datasheet s11, fig. 36)

Placement redone against fig. 36 before routing (C_OUT1 had been rotated GND-up, away from PGND).

| Rule | Status |
|---|---|
| 1. Smallest loop: switch FET, rectifier FET, output cap | ok: C14/C15 VOUT pads on the VOUT bar's pour, GND pads on the PGND bar's pour, both at the bar ends |
| 2. SW short and small, ground plane under the converter | ok: one F.Cu pour, bar to L2 (2 mm) plus the CBST finger; In1 solid GND underneath |
| 3. Small ceramics closest to the IC | ok: C14/C15 (4.7 uF) at the bars, C17-C19 (22 uF) after the P-FET |
| 4. Wide VOUT/SW/GND copper with vias | ok: pours on all three; PGND stitched to In1 at C14/C15/C19 and one extra via |
| 5. Input cap close to VIN and PGND | **deviation**: no room for a 22 uF 0805 at the 0.5 mm top-row escapes. VIN pin drops by via straight onto the In2 VSYS plane; C9/C10 sit at L2's input with GND vias into In1 directly below. VIN only supplies the controller (the power input is through L2) |
| 6. FB / COMP away from SW | ok: network under the bottom row, on the side away from SW; FB sense from +12V on B.Cu |
| 7. Separate ground trace for FB/COMP/FREQ/ILIM, single point to power ground | ok: AGND bus under R11/R12/C13/R14, joined to PGND only at the AGND pin; pour keepout `AGND_12V`; no plane vias |
| P-FET disconnect: gate network at DISDRV, R_UP from VOUT2 | ok: DISDRV -> C16/R16 -> gate along the top edge; R13 fed from +12V |

## TPS61088-Q1 5 V boost (datasheet s11, fig. 21)

Placement redone against fig. 21 before routing. Before that, the COMP parts sat between the VOUT pins and C_OUT,
C_OUT was GND-up, and the VIN cap was 4 mm from the pin.

| Rule | Status |
|---|---|
| SW traces short and small, ground plane under the regulator | ok: one F.Cu pour from L3 to SW pins 4-7, with R17 (FSW) and C24 (BOOT) standing on it as in the figure; In1 GND underneath |
| Input cap close to VIN and GND pins | ok: C23 directly under VIN pin 9 with its GND on PGND; C20-C22 at L3's input, C22's GND on the same PGND pour |
| Thermal pad soldered to a large ground plate with thermal vias | ok: EP to the PGND pour by its bottom tab, plus the footprint's thermal vias to In1 |
| (fig. 21) C_OUT right at the VOUT pins, GND on PGND | ok: C30/C31 VOUT pads on the VOUT pour beside pins 14-16, GND pads on PGND5 |
| (fig. 21) AGND parts top-right, grounds via to the bottom plane | ok: ILIM/COMP/FB column in pin order (no crossings), ground pads stitched to In1. This part's datasheet vias AGND to the plane, so no single-point bus here (unlike the TPS61178) |
| (fig. 21) VCC cap at VCC/AGND | ok: C25/C26 above the VCC and AGND pins |
| MODE floating = PFM (internal 800 k pull-up, datasheet pin table) | ok: left unconnected on purpose |
| Load switch (not in the datasheet) | Q5 source on the VOUT pour, drains straight up to the +5V pad (J7/J16 swapped so +5V is above Q5); gate network beside it, Q6 pull-down via B.Cu |

## TPS63802 3.3 V buck-boost (datasheet s12, fig. 12-1)

Placement redone against fig. 12-1 and WEBENCH d36 (same orientation as this board) before routing. Before that, L4
lay flat, which would have needed a 5 mm L2 trace around L4.1.

| Rule | Status |
|---|---|
| 1. Input and output caps as close as possible, short wide traces | ok: C33 VSYS pad 1.4 mm above VIN pin 10; C34 directly under VOUT pin 6; grounds via to In1 next to the pads |
| 2. Separate power and control ground nodes, joined close to an IC ground pin | ok: MODE (tied low), AGND pin and R25 form the control-ground node with pour keepout `AGND_3V3`; joined to PGND pin 8 and In1 by one via in the IC centre (as WEBENCH d36 does) |
| 3. Separate traces for power-stage and analog supply | n/a: the DLA package has a single VIN pin; EN comes on its own trace from the system EN net |
| 4. FB away from the L1 / L2 nodes | ok: FB divider on the left side; L1/L2 pours on the right. The TS B.Cu track was rerouted off U6's centre |
| (fig. 12-1) Inductor over the L1 / L2 pins | ok: L4 upright, pads level with L1 (upper) and L2 (lower); pours about 2 mm each, clear of PGND pin 8 |

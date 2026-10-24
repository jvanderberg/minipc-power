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

pending

## TPS61088-Q1 5 V boost (datasheet s11, fig. 21)

pending

## TPS63802 3.3 V buck-boost (datasheet s12, fig. 12-1)

pending

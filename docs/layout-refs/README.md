# Layout references

Order of authority when they disagree:

1. **Datasheet Layout Guidelines and Layout Example** (`<part>/datasheet-layout.txt`, `datasheet-p*.png`). These win.
2. EVM user guide layout (not collected yet; the BQ25606 datasheet points to the BQ25601 EVM guide, PWR877).
3. **WEBENCH layouts** (`<part>/webench-d*.kicad_pcb`, imported from WEBENCH's EAGLE export with
   `kicad-cli pcb import --format eagle`). **Reference only**: they are EVM-style test boards with large pours, drawn
   around WEBENCH's own BOM (different inductor and capacitor sizes from our LCSC parts) and a generic stackup.
   They are useful for the arrangement right around each IC. `webench-raw/` holds the original downloads.

`tps61088-5v-commercial-REJECTED/` is the WEBENCH design for the discontinued commercial TPS61088; kept for the record,
do not use.

## Per-converter checklist (from the datasheets)

### BQ25606 charger (datasheet s12)
- Input cap at **PMID** and GND, shortest path (the buck's hot loop is PMID - HSFET - LSFET - GND).
- Inductor right at SW; SW copper as small as the charge current allows; **no parallel layers on SW**; keep SW away
  from other traces and planes.
- SYS/BAT output caps near the inductor and IC, grounds tied short to IC ground.
- Analog ground routed separately, joined to power ground **at the thermal pad only** (single point).
- REGN, BTST, VBUS decoupling caps at the pins.
- Thermal pad soldered, thermal vias under the IC to the inner ground planes.
- Via count/size sized for charge + system current.

### TPS61178 12 V boost (datasheet s11)
- Smallest loop: low-side FET (SW-PGND), rectifier FET (SW-VOUT), output cap.
- SW traces minimal; ground plane directly under the converter.
- Small ceramics closest to the IC, bulk further out.
- Wide VOUT/SW/GND copper with vias for heat.
- Input cap at VIN and PGND.
- FB and COMP network away from SW.
- Separate quiet ground trace for FB, COMP, FREQ and ILIMIT resistors, joined to power ground at one point.

### TPS61088-Q1 5 V boost (datasheet s11)
- SW traces minimal; ground plane under the regulator.
- Input cap at VIN and GND.
- Thermal pad to a large ground area with thermal vias ("high power density device").
- Example: bottom layer is a solid ground plane connected to the top-layer PGND and AGND areas by vias; AGND island
  for VCC/FSW/ILIM/COMP/FB parts.

### TPS63802 3.3 V buck-boost (datasheet s12)
- Input and output caps as close as possible, short wide traces.
- Power ground and control ground as separate nodes, joined near one of the IC's ground pins.
- Separate traces for power-stage supply and analog supply.
- FB trace away from the L1 and L2 nodes.

### CH224Q PD sink
- 3-page datasheet with no layout section: keep CC1/CC2 short to the connector, VHV/VBUS caps at the pins, ESD
  diodes at the connector.

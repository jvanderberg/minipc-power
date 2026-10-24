# minipc-power - requirements and architecture

Revision: 1 - Date: 2026-10-24 - Status: draft

Scope: hobby/personal project. Not designed or reviewed for safety-critical, medical, automotive, on-board mains or
certified use. It charges bare lithium cells: first charges are supervised, on a non-flammable surface.

## 1. Purpose

- What it does: small power board for MCU-based emulator builds (Pico / ESP32 class) with a 12 V 5" LCD. Runs from
  USB-C (PD) or a 1S2P 18650 pack, charges the pack whenever USB-C is present, and supplies 5 V (MCU) and 12 V (LCD).
- Users: the owner, in their own enclosures.
- Quantity: 5 boards fabricated, 5 assembled (JLC minimum).
- Budget: not tight at prototype quantity.
- Timeline: weeks; no hard date.
- Project type: tool.
- Existing prototype / firmware: none for this board. The external MCU is not part of this board.

## 2. Usage and environment

| Item | Requirement |
|---|---|
| Location | indoor, handheld / desk |
| Ambient temperature | 0 to 40 C; charging only 0-45 C (cell limit, NTC) |
| Enclosure | small closed plastic enclosure, little or no airflow - **heat is a design constraint** |
| Mounting | 2 x M2 holes (assumed); may also be taped/glued |
| Vibration / moisture / dust | handheld use, occasional drops; no moisture |
| External connections | USB-C receptacle (charger, plugged daily); everything else is **solder pads**: battery, 5 V out, 12 V out, enable switch, status |
| User-touchable parts (ESD) | USB-C connector (shell and pins); the enable switch is wired through the enclosure |
| Long cables (> 1 m) | USB-C charging cable only |
| Mains proximity | none (external certified USB-C charger) |

## 3. Functional blocks

### Block diagram

```
USB-C --> [TVS] --> [PD sink: request 9 V, fall back to 5 V] --VBUS--> [switching charger, NVDC power path]
                                                                          |            |
                                                                    BAT <-'            '-> VSYS (3.5-4.35 V)
                                                                     |                       |
                    1S2P 18650 pack <-- [protector + dual FET] <-----'                       |
                    (solder pads, NTC)   [fuse]                                              |
                                                                  .--------------------------+
                                                                  |                          |
                                                    [5 V sync boost, true disconnect]  [12 V sync boost + disconnect FET]
                                                                  |                          |
                                                          5V OUT pads (MCU)          12V OUT pads (LCD)
                                                                  ^                          ^
                                          EN pads (mechanical switch) ---------------------'
                                          Status pads: CHG (STAT), PG, VBAT sense (divider)
```

### Blocks

| Block | Function | Key requirements |
|---|---|---|
| USB-C input | Power only (no data) | 16-pin or 6-pin power receptacle, mid-mount or SMD, top side |
| PD sink | Negotiate 9 V | Falls back to 5 V on non-PD chargers; no MCU needed |
| Charger | Charge 1S2P from VBUS, power the system | Switching (not linear: heat), NVDC power path, resistor-programmed (no I2C), NTC input, safety timer; runs the system with a dead or absent pack |
| Cell protection | Overcharge, over-discharge, overcurrent, short | On board (cells are bare, wired to pads); OC trip above the worst-case boost input current |
| 5 V rail | Power the MCU board | Synchronous boost, true output disconnect when off |
| 12 V rail | Power the 5" LCD | Synchronous boost, output disconnect when off (a plain boost leaks VSYS to the LCD) |
| User interface | On/off | Solder pads for a mechanical switch enabling both outputs; charging works with the switch off |
| Status | Optional monitoring by the external MCU | Pads for charge status, power-good and a switched-or-high-value VBAT divider (read-only - the MCU cannot configure its own supply) |
| Processor / connectivity / sensors / display / storage | - | None on this board |
| Debug / programming | - | Test points on VBUS, VSYS, BAT, 5V, 12V, GND |

### Interfaces

| From | To | Interface | Speed | Length / notes |
|---|---|---|---|---|
| Charger STAT | pad | open drain | static | external MCU pull-up to its 3V3 |
| Charger PG | pad | open drain | static | external MCU pull-up |
| VBAT divider | pad | analog | static | high-impedance divider, <= 3.3 V at 4.35 V, for an MCU ADC |
| EN pads | both boosts | switch to VSYS | static | microamp switch current |

## 4. Power

- Source(s): USB-C PD sink requesting 9 V (5 V fallback); 1S2P 18650 Li-ion (2 x ~3000-3500 mAh genuine cells,
  ~6-7 Ah, ~22-25 Wh).
- Charging: on board, switching, CC/CV to 4.20 V, charge current 1.5 A (resistor; 2 A footprint option), NTC.
- Protection: TVS on VBUS; PD sink and charger input OVP; protector IC + dual N-FET on the pack; fuse in the pack
  line; reverse-connection crowbar on the battery pads (diode + fuse) - see open questions.
- Battery life target: ~1.5 h at full load is fine (owner accepted); off-state drain should be < 50 uA so a pack
  survives months on a shelf.

### Rails

| Rail | Voltage | Tolerance | Source | Regulator type (tentative) | Noise-sensitive loads |
|---|---|---|---|---|---|
| VBUS | 9 V (5 V fallback) | PD spec | USB-C | PD sink | - |
| VSYS | 3.5-4.35 V (tracks battery on battery) | - | charger NVDC | charger buck | - |
| 5V | 5.0 V | +/-3 % | VSYS | sync boost, load disconnect | MCU, audio (possible) |
| 12V | 12.0 V | +/-5 % | VSYS | sync boost + external disconnect FET | LCD driver board |

### Power budget

| Rail | Load | Avg mA | Peak mA | Notes |
|---|---|---|---|---|
| 5V | Pico / ESP32 + small peripherals | 300 | 1000 | ESP32 Wi-Fi TX peaks ~500 mA; 1 A continuous rating, 1.5 A peak (assumed) |
| 12V | 5" LCD + driver board | 350 | 500 | **assumed - get the real panel's number** |
| | **Output power** | 5.7 W | 11 W | 5V 1.5 A peak case: 13.5 W |
| VSYS | boost inputs (eff ~90 %) | ~1.8 A @ 3.6 V | ~5.1 A @ 3.0 V | worst case: both peaks at the empty-cell voltage |
| VBUS | system + 1.5 A charge | | ~2 A @ 9 V | input limit 2.0 A (fits an 18 W 9 V/2 A PD charger) |

Peak battery current ~5 A (worst case): ~2.5 A per cell in a 1S2P pack - within typical 18650 continuous ratings, but
it sets the protector FET size and the charger's BATFET discharge limit (BQ25606: 6 A continuous [BQ25606 s7.3]).

Charge-while-running at 9 V / 2 A input (18 W): 1.5 A charge (~6.3 W at 4.2 V) + typical system (~6.3 W input) fits
with margin. On a 5 V-only charger the input limit is ~10 W, so a heavily loaded system charges slowly.

Heat estimate (plugged in at 9 V, charging 1.5 A, typical load): charger loss ~1.2 W + boosts ~0.6 W = ~1.8 W total.
That is warm in a closed box; hence 1.5 A default charge current, 4 layers for spreading, and the charger's own 110 C
thermal regulation as the backstop. Regulator design: see the pcb-power-supply notes when done.

## 5. Physical

| Item | Requirement |
|---|---|
| Board outline | target <= 40 x 25 mm rectangle (smaller if routing allows) |
| Connector positions | USB-C on a short edge; battery pads on the opposite edge; 5V/12V/GND output pads and EN/status pads along a long edge |
| Mounting holes | 2 x M2 (2.2 mm), diagonal corners (assumed) |
| Height limits | top <= 5 mm (inductors and USB-C); bottom: flat (no parts) |
| Assembly side | top only |
| Through-hole parts | none (USB-C SMD or hybrid with SMD signal pins) |

## 6. Manufacturing

| Item | Choice |
|---|---|
| Fab | JLCPCB |
| Assembly | JLC economic, top side only |
| Quantity | 5 / 5 |
| Surface finish, colour | ENIG (QFN pads, flat solder pads for wires), any colour |
| Smallest package | 0402 |
| Part policy | in stock at LCSC (global) for quantity + attrition; prefer Basic / Preferred Extended; power ICs will be Extended |

## 7. Stackup

| Item | Choice |
|---|---|
| Layers | 4 |
| Reason | three switching converters on a tiny board: solid ground plane under the hot loops, and inner copper spreads heat |
| JLC stackup | JLC04161H-7628 (JLC default) |
| Thickness | 1.6 mm |
| Copper | outer 1 oz, inner 0.5 oz (default; consider 1 oz inner for heat spreading - priced option) |
| Layer use | L1 parts + power / L2 GND / L3 GND + VSYS/BAT pours / L4 GND pour + short jumps |
| Controlled impedance | none (no data lines) |
| Design rules | 0.15/0.15 mm track/space, 0.3/0.6 mm vias, 0.3 mm copper to edge |

Values taken from the kicad-skills JLC reference (checked there October 2026); re-check on jlcpcb.com before ordering.

## 8. Component candidates

Stock from `jlcimport-cli search --region global` on 2026-10-24. Re-check before ordering.

| Block | Candidate (front-runner first) | LCSC | Stock | Class | Package | Why / concerns |
|---|---|---|---|---|---|---|
| PD sink | **CH224Q** | C46061833 | 11,344 | Ext | DFN-10 2x2 | One resistor on CFG1 picks voltage (6.8k = 9 V); PG output; 32 V abs max on VBUS. 5 V fallback behaviour not stated in the datasheet - bench-check |
| PD sink | CH224K | C970725 | 150 | Ext | ESSOP-10 | Low stock; VBUS abs max 13.5 V |
| Charger | **BQ25606RGER** | C374063 | 8,201 | Ext | VQFN-24 4x4 | Standalone NVDC, 3.9-13.5 V in, ICHG 0.3-3 A and ILIM 0.5-3.2 A by resistor, 6 A BATFET discharge, NTC, 1.5 MHz. ILIM applies only when D+/D- detection says "unknown" - D+/D- must not see a BC1.2 DCP |
| Charger | BQ25895RTWR | C80200 | 4,983 | Ext | QFN-24 4x4 | I2C; runs on register defaults without a host - rejected for no on-board MCU |
| Charger | BQ25792RQMR | C2862876 | 7,519 | Ext | QFN-29 4x4 | Buck-boost, I2C; overkill |
| 5 V boost | **TPS61023DRLR** | C919459 | 9,478 | Ext | SOT-563 | 3.7 A typ / 2.7 A min valley limit, true disconnect, ~$0.24. ~1.7 A out at 3.0 V worst case |
| 5 V boost | SY7088DGC | C178240 | 28,209 | Ext | DFN-8 2x3 | Check disconnect behaviour |
| 12 V boost | **TPS61178RNWR** | C127918 | 6,745 | Ext | VQFN-13 3x3.5 | 20 V, 16 mOhm FETs, resistor-set peak limit, DISDRV gate driver for an external disconnect FET |
| 12 V boost | TPS61089RNRR | C165129 | 10,355 | Ext | VQFN-11 2x2.5 | 12.6 V max output - too close to 12 V; no disconnect |
| Protector | **HY2120-CB** | C116509 | 17,071 | Ext | SOT-23-6 | 4.28 V OVC, 2.90 V ODC, 200 +/-30 mV OCD. Needs FETs with ~20-25 mOhm total at Vgs = 3 V for a >= 6.5 A trip |
| Protector | DW01A | C351410 | 104,610 | Ext | SOT-23-6 | Cheapest; check its OCD and 2.4 V ODC |
| Protector FET | AO8810 (x2 in parallel?) | C21426 | 12,191 | Ext | TSSOP-8 | 20 mOhm @ 4.5 V per FET; one part trips ~3.5-5.5 A - too low alone. Look for a low-Rds common-drain dual |

## 9. Decisions

| Decision | Choice | Reason |
|---|---|---|
| Input | USB-C PD sink, request 9 V | 5 V/3 A (15 W) cannot charge and run the 12 V LCD at once; 9 V gives lower charger loss than 12 V and margin under the BQ25606's 13.5 V max |
| Charger type | standalone switching NVDC | heat (a linear charger at 1.5 A from 9 V would burn ~7 W); the external MCU cannot configure its own supply |
| Power architecture | everything runs from VSYS via two boosts | one path for USB and battery; no source OR-ing |
| Output switching | mechanical switch to boost EN pins | user request; switch carries only microamps; charging continues when off |
| Output disconnect | required on both boosts | a disabled plain boost passes VSYS to its output |
| Layers | 4 | heat spreading and hot-loop ground on a small board |
| Connections | solder pads only (except USB-C) | user request: maximum flexibility |

## 10. Assumptions

- 5 V load: 1 A continuous, 1.5 A peak.
- 12 V LCD: 350 mA typical, 500 mA peak. **Needs the real number.**
- Charge current 1.5 A (heat), input limit 2.0 A.
- Genuine 3000-3500 mAh cells, bought as a matched pair, joined at the same voltage before connection.
- NTC: 10 k B=3435 thermistor on a pad pair, taped to the pack (charger TS input). If omitted, a fixed resistor
  footprint can stand in - but then charging is not temperature-limited.
- Hardware low-battery cutoff = protector over-discharge (2.90 V). No separate UVLO.
- Board <= 40 x 25 mm; 2 x M2 holes; ENIG.

## 11. Open questions

| Question | Who answers | Blocks |
|---|---|---|
| Real 12 V LCD current (typ and peak at power-on / backlight full) | owner | 12 V boost current limit, inductor |
| Will the 5 V rail also feed an audio amp or anything over 1 A? | owner | 5 V boost choice |
| Reverse-polarity on battery pads: crowbar diode + fuse, or silkscreen only? | owner (recommend crowbar) | battery input |
| On-board power-management MCU (soft button, gauge, shutdown signal) - rev 2? | owner | none now |
| CH224Q behaviour when the charger has no 9 V PDO | bench test | input current limit at 5 V |
| Mounting holes needed at all? | owner | outline |

## 12. Next steps

1. Create the KiCad project; set stackup and design rules to section 7; draw the outline and mounting holes.
2. Power design from section 4 (pcb-power-supply): BQ25606 resistors, both boosts, protector FET choice.
3. Stock and datasheet checks for each candidate in section 8 (pcb-part-selection).
4. Schematic capture and layout (kicad-pcb-workflow).
5. Design review before ordering (kicad-board-review).

| Pin | Part | Name | Type | State | Decision / datasheet note |
|---|---|---|---|---|---|
| J1.A6 | USB-C HRO TYPE-C-31-M-12 | D+ | bidirectional | unconnected | USB D+: not connected. PD negotiates on CC1/CC2; the BC1.2/QC path through CH224Q DP/DM was dropped (0.4 mm-pitch inner pins could not escape beside CC1/CC2). Effect: a QC-only charger stays at 5 V. docs/power-design.md s1 |
| J1.A7 | USB-C HRO TYPE-C-31-M-12 | D- | bidirectional | unconnected | USB D-: not connected, as J1.A6 |
| J1.A8 | USB-C HRO TYPE-C-31-M-12 | SBU1 | bidirectional | unconnected | SBU1: unused. Sideband use is for alternate modes; a power-only sink needs none |
| J1.B6 | USB-C HRO TYPE-C-31-M-12 | D+ | bidirectional | unconnected | USB D+ (second row): not connected, as J1.A6 |
| J1.B7 | USB-C HRO TYPE-C-31-M-12 | D- | bidirectional | unconnected | USB D- (second row): not connected, as J1.A6 |
| J1.B8 | USB-C HRO TYPE-C-31-M-12 | SBU2 | bidirectional | unconnected | SBU2: unused, as J1.A8 |
| U1.2 | CH224Q | CFG2 | input | unconnected | CH224Q CFG2: floating. Single-resistor configuration (R1 6.8k on CFG1 = 9 V); 'CFG2 and CFG3 may be left floating' (CH224 datasheet s5.2.1, table 5-1) |
| U1.3 | CH224Q | CFG3 | input | unconnected | CH224Q CFG3: floating, as U1.2 (CH224 datasheet s5.2.1) |
| U1.4 | CH224Q | DP | bidirectional | unconnected | CH224Q DP: not connected. BC1.2/QC requests dropped, see J1.A6; PD on CC1/CC2 only |
| U1.5 | CH224Q | DM | bidirectional | unconnected | CH224Q DM: not connected, as U1.4 |
| U1.10 | CH224Q | ~{PG} | open_collector | unconnected | CH224Q PG: unused. Open-drain active-low power-good indicator (pin table); nothing on this board needs it |
| U2.1 | BQ25606 | VAC | input | tied to VBUS | BQ25606 VAC: tied to VBUS. 'Input voltage sensing. This pin must be shorted to the VBUS pin.' (SLUSCK6C table 7-1) |
| U2.2 | BQ25606 | NC | no_connect | symbol NC |  |
| U2.3 | BQ25606 | D+ | bidirectional | unconnected | BQ25606 D+: floating on purpose. The DCD timer expires, nonstandard detection finds no divider, so the source is 'unknown' and the ILIM resistor (R2 249R, 1.92 A) sets the input limit (SLUSCK6C s9.3.2.3.1, ILIM row of table 7-1). This chain is inferred from the datasheet: confirm the input limit on the bench |
| U2.4 | BQ25606 | D- | bidirectional | unconnected | BQ25606 D-: floating on purpose, as U2.3 |
| U2.6 | BQ25606 | OTG | input | tied to GND | BQ25606 OTG: tied to GND. 'When this pin is pulled HIGH, OTG is enabled. OTG cannot be floating.' (table 7-1); boost-back mode not used |
| U2.9 | BQ25606 | ~{CE} | input | tied to GND | BQ25606 /CE: tied to GND. 'When this pin is driven low, battery charging is enabled.' (table 7-1); charging always enabled |
| U2.12 | BQ25606 | VSET | passive | unconnected | BQ25606 VSET: floating. RPD > 50 kohm (float pin) = 4.208 V charge voltage for Li-ion 18650 (table 7-1, VBATREG spec) |
| U3.4 | HY2113-MB1A | NC | no_connect | symbol NC |  |
| U5.11 | TPS61088-Q1 | NC | no_connect | symbol NC |  |
| U5.12 | TPS61088-Q1 | NC | no_connect | symbol NC |  |
| U5.13 | TPS61088-Q1 | MODE | input | unconnected | TPS61088-Q1 MODE: floating. Internal 800 kohm pull-up (RMODE); floating selects PFM at light load (SLVSE52A pin table); efficiency at light load preferred over forced PWM |
| U6.2 | TPS63802 | MODE | input | tied to GND | TPS63802 MODE: tied to GND. 'Set LOW for power save mode, set HIGH for forced PWM mode. It must not be left floating.' (SLVSEU9D pin table) |

23 pins listed, 0 without a decision

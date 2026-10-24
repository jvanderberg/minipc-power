# WEBENCH: 5 V rail (2026-10-24, logged in)

Inputs: Vin 3.0-4.35 V, Vout 5 V, Iout 2.5 A (corner: empty cell + amp peak), ambient 50 C, max height 5 mm, ceramic
caps, shielded inductors, Balanced.

## Candidate list vs LCSC global stock (jlcimport-cli, same day)

| Part | WEBENCH eff. | LCSC global stock | Verdict |
|---|---|---|---|
| TPS61022 | 93.8 % | 0 (2,500 in CN only) | no stock |
| TPS61230A | 89.5 % | 0 | no stock |
| TPS61236P | 95 % | 13 | no stock |
| TPS61088 | 93.4 % | 7,130 | **chosen** |
| TPS61089 | 93.5 % | 10,355 | IC peak 7.24 A vs ~7 A limit, Tj 80 C - rejected |
| TPS61178 | - | 6,745 | WEBENCH: "Design cannot be created" at 5 V (datasheet allows 4.5-20 V out); not used for 5 V |

## TPS61089RNRR (design 34) - rejected
490 kHz (WEBENCH allowed 200-490 kHz here), L 470 nH 3.9 mOhm (Coilcraft XGL4030-471), Cin 3 x 47 uF 1210, Cout 2 x
47 uF 1210, Rlim 124 k, Rt 316 k, Rfbt/Rfbb 240 k / 76.8 k, Rcomp 32.4 k, Ccomp 560 pF, Ccomp2 27 pF.
At 3.0 V / 2.5 A: eff 93.5 %, PM 56.9 deg, fc 38.5 kHz, L ripple 5.58 App, **IC peak 7.24 A**, IC Pd 764 mW, IC Tj
79.9 C (theta-JA 39.2 C/W), total Pd 864 mW.

## TPS61088RHLR (design 35) - chosen
| Ref | Value | WEBENCH MPN |
|---|---|---|
| L1 | 1.0 uH, 11 mOhm | TDK VLP8040T-1R0N (IDC 9.4 A) - substitute |
| Cin | 3 x 10 uF 16 V 0805 (16 uF derated) + 100 nF | Taiyo MSASE21GAB5106KTNA01 |
| Cout | 2 x 47 uF 16 V 1210 (63 uF derated) | Murata GRM32ER61C476KE15L |
| Cvcc | 2 x 1 uF 0603 | |
| Cbst | 100 nF | |
| Css | 8.2 nF | |
| Rt | 267 k | 594 kHz |
| Rlim | 154 k | |
| Rfbt / Rfbb | 220 k / 69.8 k | 5.00 V |
| Rcomp / Ccomp / Ccomp2 | 26.7 k / 750 pF / 39 pF | |

At 3.0 V / 2.5 A: eff 93.4 %, PM 56.0 deg, fc 31.9 kHz, duty 42.4 %, L ripple 2.14 App, IC peak 5.45 A, Iin 4.46 A,
Cout RMS 2.2 A, Cin RMS 0.62 A, IC Pd 655 mW, L Pd 215 mW, total Pd 878 mW, IC Tj 75.4 C (theta-JA 38.8 C/W),
Vout ripple 31 mVpp, tolerance 4.19 %. No load disconnect: add an external P-FET switch.

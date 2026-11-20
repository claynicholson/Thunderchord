# Musical DRSSTC — driver board rev A and coil numbers

Status: schematic complete and ERC-clean. PCB is routed (90 x 65 mm, 4 layers, 0 DRC errors
under JLC standard no-surcharge rules). It is NOT ready to order — see "Before ordering".
Nothing here has been simulated or built. No firmware exists yet.

## 1. What the board is

One board replaces the usual driver + interrupter + fibre receiver + wireless bridge:

| Block | Parts | What it does |
|---|---|---|
| Resonance tracking | U4a TLV3502 (4.5 ns), 4 x 10R 1206 burden (2.5 ohm), R1/C15 phase lead | Squares up the primary-current CT signal. The bridge is switched by the tank's own current, so it always runs at the tank's resonant frequency, whatever the streamer loading does. R1 advances switching 0-45 deg at 65 kHz to cancel IGBT turn-off delay. |
| Zero-current switching | U6a 74HCT74, U5 74AHCT00 | Bursts start immediately and stop only on a current zero crossing. Outputs are both low when disabled (GDT primary shorted). |
| Over-current trip | U4b, D7-D10 bridge, R2 trimmer, U6b latch | Second CT. Trips for the rest of the burst, re-arms on the next burst. Burden is 4 x 10R 1206 = 2.5 ohm; R2 sets 0-1320 A (with a 1000:1 CT). Red LED D13 + flag to the ESP32. |
| Hardware on-time limit | U7 74LVC1G123 (R14 39k, C23 10n) | No burst can exceed ~390 us, whatever the firmware does. |
| Safety chain | U8 voltage detector, J7 E-stop loop | Bursts are blocked if the 24 V rail is under ~18 V or the E-stop loop on J7 is open. Fit a link or a NC switch on J7. |
| Gate drive | U2/U3 IXDI614CI (14 A, 35 V, TO-220-5 standing on the left edge for an external heatsink), C35-C38 DC block (4 x 10 uF 50 V 0805), J4 | 24 V full bridge into an external gate drive transformer. |
| Controller | U1 ESP32-S3-WROOM-1U (external antenna) | Bluetooth-LE MIDI and Wi-Fi (wireless), USB-C MIDI, 3.5 mm TRS MIDI (opto-isolated, U11) and a Toslink fibre input FC1 (wired). Measures 24 V rail, heatsink NTC (J8), resonant frequency (FB_MON) and drives a 24 V fan (J9). |
| Power | J3 24 V in, D1 reverse protection, D2 TVS, U13 TPS5430 buck to 5.3 V (5.0 V after the OR diode), U14 AMS1117-3.3 | USB alone powers the logic for flashing. |

ESP32 pins: IO4 interrupter out, IO5 fibre in, IO6 MIDI RX, IO7 OCD flag, IO10 limited-burst readback,
IO11 feedback frequency, IO1 24 V sense (x0.091), IO2 NTC, IO8 fan PWM, IO9 status LED, IO19/20 USB.

Connectors: J10 24 V DC barrel jack (5.5 x 2.1 mm, centre positive, top edge; in parallel with J3, use one or the other) · J3 24 V in · J4 GDT primary · J5 feedback CT · J6 over-current CT · J7 E-stop loop ·
J8 NTC · J9 fan · J2 USB-C · J1 TRS MIDI · FC1 fibre.

## 2. Coil numbers (ASSUMED secondary: 6 in diameter x 24 in winding)

You told me the secondary is 24 in long and probably 28 AWG, so use the 28 AWG column (~84 kHz).
The diameter is still an assumption (6 in form). Measure and re-run.

| Item | 28 AWG (~1740 turns) | 30 AWG (~2180 turns) |
|---|---|---|
| Secondary inductance (Wheeler) | ~102 mH | ~160 mH |
| Self capacitance (Medhurst) | ~11 pF | ~11 pF |
| Toroid 6 x 24 in | ~26 pF | ~26 pF |
| Unloaded resonance | ~84 kHz | ~67 kHz |

Starting point for the rest (28 AWG case):
- Primary: tune 5-10 % below the secondary, ~75 kHz. 0.3 uF MMC + ~15 uH (about 6-7 turns of 3/8 in
  copper tube, 9 in inner diameter, tapped). Tank impedance ~7 ohm.
- MMC: 50 x 0.15 uF 2 kV polypropylene pulse caps, 5 in series x 10 in parallel = 0.3 uF, 10 kV.
  At 1000 A peak the cap sees ~7 kV.
- Bridge: full bridge of two half-bridge IGBT bricks, 1200 V, 300-600 A class, on a laminated bus.
- Bus: 340 V (120 V doubled) to 680 V (240 V doubled), several mF of electrolytics plus snubbers.
- CTs: two, each 1000:1 overall (e.g. two cascaded 1:33 stages), on the primary lead.
- GDT: 1:1 (x4 secondaries) on a high-permeability ferrite toroid, gate resistors and +/- clamp zeners at each gate.
- Spark length: coils of this size are reported at roughly 8-10 ft. That is an estimate, not a calculation.

## 3. Before ordering — must do

1. Layout: see item 9 for the current state. Gate-drive tracks would be better as poured copper.
2. Check J1 tip/ring. I mapped ring->pad 4, tip->pad 5 from the footprint geometry, not a datasheet.
   Wrong polarity is harmless (D11 protects) but MIDI will not work.
3. Check D6 (BAT54S) pinout against its datasheet: wired pad 1 GND, pad 2 +5 V, pad 3 signal.
4. FC1 (PLR135/T10) shows zero JLC assembly stock — hand-solder it or pick a stocked Toslink receiver.
5. Done: U1 uses a project copy of the footprint with 0.3 mm vias (copper-lcsc:ESP32-S3-WROOM-1U_via0p3).
6. KiCad 10.0.6 has a zone-fill bug that can short pours to pads; update to 10.0.7 and re-run DRC.
7. Cost-down pass: every part with a JLC Basic equivalent is now Basic. 11 Extended parts remain for JLC to
   place (about $33 in feeder fees): U1 ESP32, U2/U3 drivers, U4 comparator, U5, U6, U7 logic, U8 detector,
   U11 opto, U12 USB ESD, J2 USB-C, L2 inductor. None has a Basic equivalent that does the job.
8. Hand-solder parts (field Assembly=hand-solder; leave them out of the JLC assembly order and buy from LCSC):
   J1, J3-J10, R1, R2, FC1, C1, C2, U2, U3 (TO-220 gate drivers). Remove these lines from the BOM/CPL files before uploading.
9. Layout: see section 8.

## 4. Operating rules built into the design

- Power the 24 V logic before the HV bus, and remove the bus first. With 24 V present and 5 V absent
  the two driver outputs are not guaranteed to match.
- CT phasing: if the coil does not oscillate, flip the feedback CT leads on J5.
- Start with R2 turned to minimum (trips at once), low bus voltage, short bursts.
- Keep the board in a grounded metal box, antenna outside. Prefer fibre or Bluetooth over copper MIDI
  cables for anything longer than a patch lead.

## 5. Firmware (not written)

Needs: BLE-MIDI + USB-MIDI + UART MIDI in, polyphonic voice mixer producing one burst train on IO4,
per-note on-time table, total duty cap (5-10 %), minimum off-time, refuse to run on low 24 V / high
NTC, back off on repeated OCD flags.

A DRSSTC plays notes (MIDI), not arbitrary audio. "Clean" means a well-behaved interrupter: limited
voices, duty and on-time. It will be very loud (well over 110 dB close up).

## 6. Safety

Lethal bus voltage, 8-10 ft arcs, strong RF, ozone and hearing-damage sound levels. For an audience:
RF ground separate from mains earth, a strike rail or cage, at least twice the spark length of clear
distance, no one with a pacemaker nearby, hearing protection, an operator with the E-stop in hand.

## 7. Power input

The on-board mains supply was removed again at the user's request. Power is 24 V DC, 2 A or more, through
barrel jack J10 (5.5 x 2.1 mm, centre positive, 2 A / 30 V rated) or screw terminal J3. Never both.
J10 pin 1 (rear pad) is wired as centre/+, pins 2 and 3 as sleeve/GND, read from the footprint geometry,
not a datasheet: check with a meter before first power-up. D1 blocks a reversed adapter.

## 8. Layout (fourth pass)

Major parts placed by hand, small parts auto-placed, all tracks auto-routed then corner-checked.
- Gate drivers U2/U3 are now TO-220-5 (IXDI614CI), standing upright with their metal tabs flush with the
  left board edge, mirrored about the board centreline, so both bolt to one external heatsink bar.
  Check the datasheet for whether the tab is tied to GND; use an insulating pad unless the heatsink is
  at board ground. These are the gate drivers. The IGBT power transistors are not on this board; they
  bolt to their own heatsink and connect through the gate drive transformer on J4.
- Bulk caps C1/C2 sit beside the drivers. J4 (GDT) is on the bottom edge: GDT_A 57 mm, GDT_B 22 mm.
- ESP32 centred on the right half; USB-C centred on the right edge with the MIDI jack above and the
  fibre receiver below; reset/boot buttons mirrored either side of the USB.
- Top edge: J3, J10 barrel jack, J7 (E-stop), J8 (NTC), J9 (fan). Bottom edge: J4, J5, J6 with both
  trimmers and the comparator between them.
- Corners: no trace bends of 90 degrees or sharper, and no mid-trace tee junctions at 90 degrees or sharper
  (checked by script after routing). Four tees were reworked by hand: +3V3 near R2 and BUCK_FB now join
  at a pad; BUCK_SW and OCD_SENSE use a shallow 10-degree peak in the main track so all three angles
  are 100/100/160 degrees. Joints at pads can still be 90 degrees where two tracks leave one pad;
  one of these is at the tip of USB-C pad B7 (USB_DM), 0.03 mm outside the pad.
- Screw-terminal wire-entry direction was inferred from the 3D model, not a datasheet: check in KiCad's
  3D viewer that every terminal opens toward the board edge before ordering.
- Not fully symmetric: the small passives are where the auto-placer put them.

## 9. Fifth pass: widths, USB pair, ground fills, artwork

- Track widths are now three deliberate sizes: 0.2 mm signals, 0.8 mm power, 1.0 mm gate drive, CT and
  24 V input. Anything else is a short neck where a wide track enters a narrow pad (0.3-0.6 mm).
- USB: nets renamed USB_D_P / USB_D_N. Hand-routed as a 0.2 mm / 0.2 mm gap pair from the ESD part to
  the ESP32, matched to about 1 mm. Both pad pairs of the USB-C connector are joined (one link on the
  bottom layer through two vias). U12 moved 1.5 mm west and rotated to make room.
  The ESP32-S3's USB is full speed (12 Mbit/s); impedance was not calculated for the JLC stack-up.
- Ground: GND fills on both outer layers with 29 stitching vias, on top of the inner GND plane.
- D3 (buck catch diode) changed SS14 -> SS34: the TPS5430 can deliver 3 A into a fault.
- Back silkscreen: Tesla coil, lightning and note artwork generated by a script (uuid prefix a57a57);
  it avoids through-hole pads. drsstc-driver.kicad_pcb.pre-art.bak is the board before the artwork.
- Nine dangling router stubs were deleted.

### Things only a bench test can settle (the design is NOT guaranteed to work)
1. TPS5430 loop stability with all-ceramic output capacitors (2 x 22 uF). The datasheet's reference
   design uses a capacitor with some ESR; if the 5 V rail rings, fit a 100-220 uF electrolytic across C5.
2. ESP32 staying alive next to a running coil (brown-outs, resets, radio drop-outs).
3. Feedback lock at start-up and the phase-lead trimmer range with the real tank.
4. Gate waveforms into the real gate drive transformer and IGBTs.
5. MIDI jack tip/ring and barrel-jack polarity (both read from footprints, not datasheets).
6. PLR135 supply range at 3.3 V and screw-terminal wire-entry direction.

## 10. Looks (sixth pass)

- Solder mask set to black, silkscreen white and finish ENIG in the board stackup. These only drive
  KiCad's 3D view: on the JLCPCB order form you must pick "Black" solder mask yourself, and ENIG
  (gold) if you want it. ENIG costs extra; HASL works electrically.
- Back artwork v2 (script-generated, uuid prefix a57a57, all on B.SilkS): Tesla coil with shaded
  toroid and breakout point, nine tapered branching bolts, a halftone corona of 459 dots, the
  burst waveform the coil makes for each note with its interrupter pulse, title block, spec lines,
  edge rulers, mounting-hole rings and a legend next to every connector, trimmer and driver.
- Artwork keeps 0.45 mm off every through-hole pad, uses lines of 0.15 mm or wider and text of
  1.0 mm / 0.15 mm or larger (JLC's printable minimums).
- copper-out/render/black-back.png and black-front.png are the black-mask renders.

## 11. Name and branding

- Board name: THUNDERCHORD. Printed on both sides, with CHORD as negative (knockout) text.
- CLAYNICHOLSON.COM printed as a knockout banner on the back (bottom centre) and on the front
  (below C2). SOLID STATE on the back is also knockout.
- The KiCad project and file names are still drsstc-driver.

## 12. Silkscreen clean-up

- Removed from the back: "DUAL RESONANT / SOLID STATE" (duplicates "DRSSTC" in the subtitle) and the
  three spec lines (they repeated what the connector legends already say).
- The artwork generator now lives in tools/silkscreen_art.py. Run it from this folder with the board
  closed in KiCad; it replaces its own earlier output (uuid prefix a57a57) and leaves everything else.

## 13. Back artwork v3

The coil drawing, waveform, notes, rulers and "REV A" are gone. The whole back is now one discharge:
17 bolts from a single point to every edge with three levels of branching, four loose arcs, and a
halftone field of 1138 dots over the entire board that swell near a spark and shrink away from it.
Kept: the THUNDERCHORD banner, CLAYNICHOLSON.COM and the connector legends.

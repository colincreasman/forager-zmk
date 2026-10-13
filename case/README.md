# Cases: Forager

Two cases for the Forager, each in its own folder. Both use the same base, PCB, nuts and screws.

| | [Enclosed (stock)](enclosed/README.md) | [Sandwich](sandwich/README.md) |
|---|---|---|
| What | carrefinho's original Forager case, the one PandaKB ships | A new top shell for the stock base, in the style of ErgoMech's Totemist (and GEIST's TOTEM) |
| Style | A flat 2.2 mm top plate, switches and keycaps stand on top | Keycaps sit in wells, the rim comes up to just under their tops |
| Parts | Top plate + base per half, optional magnetic tenting legs | A top shell per half; the base, legs, screws and nuts are the stock ones |
| Desk to plate / rim / keycap tops | 8.4 / – / 16.7 mm | 8.4 / 15.3 / 16.7 mm |
| Footprint per half | 117.2 × 98.9 mm | The same |

![sandwich vs stock](sandwich/stl/forager_preview.png)

Side by side, cut through the middle-finger column and a thumb key:

![stock vs sandwich profile](sandwich/stl/forager_profile.png)

**Which one?** If you already have a Forager, the sandwich case is just two new top shells: unscrew
the stock top plates and screw these on. It looks and feels like the Totemist: the switches are
hidden and the rim guards the keycaps from the side. The stock plate makes the keycaps easier to
reach, and its flat surface lets sweat run off the edge, where the sandwich case's wells hold it on
the plate.

## Layout

```
case/
├── pcb/forager-pcb.kicad_pcb   the Forager PCB, from carrefinho/forager (CERN-OHL-P-2.0)
├── enclosed/                   the stock case: STLs, STEP, license, source
└── sandwich/                   README, generate_case.py, sandwich.py, stl/
```

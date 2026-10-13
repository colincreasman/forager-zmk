# Enclosed case (stock): Forager

The Forager's original case by carrefinho, copied unmodified from
[carrefinho/forager](https://github.com/carrefinho/forager) at the commit in
[SOURCE.txt](SOURCE.txt), under [CERN-OHL-P-2.0](LICENSE). It's the case PandaKB ships, printed in
PLA. One of the two designs in [`case/`](../README.md); the other is the
[sandwich case](../sandwich/README.md), which reuses this base.

- **Top plate:** a 2.2 mm plate that lies on the PCB. The Choc clips catch under it, and it has
  switch-puller grooves and countersinks for 4 top screws.
- **Base:** a 6.2 mm tray whose walls come up to the PCB's top face. It has the XIAO's USB-C slot,
  a filament light pipe for its LED, and a print-in-place lever that presses the XIAO's reset button.
- **Screws:** each half has 5 SMD M2 nuts soldered to the PCB, 4 countersunk screws from the top and
  5 from the bottom.

| File | What it is |
|---|---|
| `LTop.stl`, `RTop.stl` | Top plates: 117.2 × 98.9 × 2.2 mm |
| `LBase.stl`, `RBase.stl` | Bases: 117.2 × 98.9 × 6.2 mm |
| `legs.stl` | Magnetic tenting legs (see the build guide) |
| `Forager Case.step` | The editable CAD model |

The STLs are in the assembly's coordinates (z = 0 is the PCB's bottom face), so a top and base loaded
together line up.

Parts list, printing and assembly: carrefinho's
[build guide](https://github.com/carrefinho/forager/blob/main/docs/build-guide.md). In short:
18 countersunk M2 screws 4–5 mm long, 10 SMD M2 nuts (SMTSO2020MTJ), rubber bumpers, and magnets,
pins and bumpers for the legs. carrefinho designed the case for FDM printing: "some walls may be too
thin for certain technologies".

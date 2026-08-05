# Forager ZMK Config (urob's config, QWERTY base)

This repo pairs the Forager keyboard hardware definition (shield in `boards/`)
with a near-verbatim copy of [urob's ZMK
config](https://github.com/urob/zmk-config). The only layout change is the
alphanumeric base: instead of urob's Colemak-DH, the base layer uses **QWERTY**.
Every other feature (timeless homerow mods, combos, leader key, smart layers,
magic-shift, nav cluster, mouse emulation, etc.) is identical to upstream. The
keymap lives in `config/forager.keymap` (which includes `config/base.keymap`).

The original Forager module readme follows.

---

This is the ZMK module for [the Forager keyboard](https://github.com/carrefinho/forager).

[ZMK Studio](https://zmk.dev/docs/features/studio) is supported and enabled by default.

Featuring the awesome [zmk-rgbled-widget by caksoylar](https://github.com/caksoylar/zmk-rgbled-widget).

# Usage

Add these lines to `config/west.yml` in your `zmk-config` repository:

```yaml
manifest:
  remotes:
    - name: zmkfirmware
      url-base: https://github.com/zmkfirmware
    - name: carrefinho                            # <---
      url-base: https://github.com/carrefinho     # <---
    - name: caksoylar                             # <---
      url-base: https://github.com/caksoylar      # <---
  projects:
    - name: zmk
      remote: zmkfirmware
      revision: main
      import: app/west.yml
    - name: forager-zmk-module                    # <---
      remote: carrefinho                          # <---
      revision: main                              # <---
    - name: zmk-rgbled-widget                     # <---
      remote: caksoylar                           # <---
      revision: main                              # <---
  self:
    path: config
```

Then add `forager_left` and `forager_right` shields to your `build.yaml`:

```yaml
---
include:
  - board: seeeduino_xiao_ble
    shield: forager_left rgbled_adapter
    snippet: studio-rpc-usb-uart
  - board: seeeduino_xiao_ble
    shield: forager_right rgbled_adapter
```

For more information on ZMK Modules and building locally, see [the ZMK docs page on modules.](https://zmk.dev/docs/features/modules)

To customize behavior of the RGB LED, see [rgbled-widget documentation.](https://github.com/caksoylar/zmk-rgbled-widget)
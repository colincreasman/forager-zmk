# Forager ZMK Module

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
# Dongle mode (PandaKB USB dongle)

The keyboard can also run through [PandaKB's ZMK dongle](https://pandakb.com/shop/keyboard-kit/pandakb-zmk-split-keyboard-dongle/)
(a nice!nano v2 with a 1.3" OLED). The dongle becomes the split **central** and both halves become its
**peripherals**: plug it into a computer and the keyboard just works as a USB keyboard, with no Bluetooth pairing
on that computer. ZMK fixes each part's role at build time, so in dongle mode the halves cannot connect to a
computer without the dongle, and switching modes means reflashing. Both sets of firmware are built.

| Artifact | Flash to | Mode |
|---|---|---|
| `forager_dongle` | dongle | dongle |
| `forager_left_dongle_mode` | left half | dongle |
| `forager_right rgbled_adapter-seeeduino_xiao_ble-zmk` | right half | **both** (the right half is a peripheral either way) |
| `forager_left rgbled_adapter-seeeduino_xiao_ble-zmk` | left half | standalone |
| `settings_reset_dongle` | dongle | reset (nice!nano board) |
| `settings_reset-seeeduino_xiao_ble-zmk` | either half | reset (XIAO board) |

**One-time setup:** turn off other ZMK keyboards nearby, flash the matching settings reset to all three devices
(standalone-mode bonds must be cleared first), then flash the dongle-mode firmware, plug in the dongle, and power
on both halves. To go back, reset the halves and flash the standalone left firmware.

- Keymap changes then only need the **dongle** reflashed. To reach its bootloader without opening its case, hold
  both far outer thumbs (maintenance layer) and hold `T` for 2 seconds. `Q`/`P` still bootloader each half.
- The dongle keeps all five Bluetooth profiles (its connection limits are raised to fit both halves too), so it
  can also pair to computers wirelessly on its own battery. ZMK Studio is enabled on the dongle.
- Layers are named so the dongle's OLED can show them. The dongle never deep-sleeps: deep sleep is only woken by
  a key press, and it has no keys.
- The `pandakb_dongle` shield holds the OLED wiring, copied from PandaKB's own dongle firmware;
  `forager_dongle` is the board-agnostic dongle itself.

# Timeless Homerow Mods

This document describes the change that made the forager's homerow mods (`HRML`
and `HRMR`) "timeless", mirroring the approach used in
[urob's zmk-config](https://github.com/urob/zmk-config).

Only the homerow mods were changed. Layers, combos, the `&ht LSHIFT TAB` thumb
key, and the physical layout are all untouched.

> **Update:** the `&ht` thumb behavior *was* subsequently changed — see
> [Thumb keys must not use prior-idle gating](#thumb-keys-must-not-use-prior-idle-gating)
> at the end of this document.

## What "timeless" means

Naive homerow mods (HRMs) depend on precise timing: hold longer than
`tapping-term-ms` for a modifier, release faster than it for a tap. That
requires very consistent typing speed and leads to misfires. A "timeless" setup
removes the dependence on precise timing by combining four ZMK features:

1. **`balanced` flavor + a large `tapping-term-ms` (280ms)** — the behavior
   becomes insensitive to exact timing. `balanced` resolves a *hold* as soon as
   another key is both pressed and released within the tapping term, which is
   exactly what you do when using a modifier.
2. **`require-prior-idle-ms` (150ms)** — if the HRM key is pressed shortly after
   another key (i.e. mid-typing), it resolves immediately as a *tap*. This
   eliminates the delay between pressing an alpha and seeing it on screen.
3. **`hold-trigger-key-positions` (cross-hand + thumbs)** — "positional
   hold-tap". A modifier is only produced when the *next* key is on the opposite
   hand (or a thumb). Same-hand rolls therefore resolve as taps, preventing
   false modifiers.
4. **`hold-trigger-on-release`** — delays the positional decision until the next
   key is *released* rather than pressed, so multiple modifiers on the same hand
   can still be combined.

## Implementation

Because each hand needs a different set of cross-hand trigger positions, the
single shared `&ht` behavior was replaced (for the homerow only) with two
dedicated behaviors: `hml` (left hand) and `hmr` (right hand). The `HRML` /
`HRMR` macros now point at these instead of `&ht`, so the per-layer bindings did
not need to change.

The `&ht` behavior itself was left unchanged at the time and still powers the
`&ht LSHIFT TAB` thumb key — this later turned out to be a bug, see below.

### Behavior settings

| Property                     | Old (`ht`)                | New (`hml` / `hmr`)          | Why |
| ---------------------------- | ------------------------- | ---------------------------- | --- |
| `flavor`                     | `balanced`                | `balanced`                   | Resolve hold on cross-key press+release |
| `tapping-term-ms`            | 220                       | **280**                      | Large term → insensitive to precise timing |
| `quick-tap-ms`               | 150                       | **175**                      | Matches urob's value |
| `require-prior-idle-ms`      | — (used `global-quick-tap`) | **150**                    | Instant tap when typing fast → removes delay |
| `hold-trigger-key-positions` | —                         | **cross-hand keys + thumbs** | Positional hold-tap → no false mods on same-hand rolls |
| `hold-trigger-on-release`    | —                         | **enabled**                  | Lets same-hand mods still be combined |

### Key-position map

The trigger positions were derived from the matrix transform in
`boards/shields/forager/forager.dtsi`:

```
Row 0:  0  1  2  3  4  |  5  6  7  8  9
Row 1: 10 11 12 13 14  | 15 16 17 18 19
Row 2: 20 21 22 23 24  | 25 26 27 28 29
Thumbs:        30 31   | 32 33
```

Which gives the macros:

```c
#define KEYS_L 0 1 2 3 4 10 11 12 13 14 20 21 22 23 24   // left-hand keys
#define KEYS_R 5 6 7 8 9 15 16 17 18 19 25 26 27 28 29   // right-hand keys
#define THUMBS 30 31 32 33                               // thumb keys
```

- `hml` uses `hold-trigger-key-positions = <KEYS_R THUMBS>` — a left-hand HRM
  only produces a modifier when the next key is on the right hand or a thumb.
- `hmr` uses `hold-trigger-key-positions = <KEYS_L THUMBS>` — the mirror image.

## Net effect

Fast same-hand rolls resolve as taps (no accidental modifiers), while genuine
cross-hand chords still produce modifiers — with virtually no typing delay and
no reliance on precise hold/tap timing.

## Reference

- urob's writeup on timeless homerow mods: <https://github.com/urob/zmk-config>
- ZMK hold-tap docs: <https://zmk.dev/docs/keymaps/behaviors/hold-tap>

## Thumb keys must not use prior-idle gating

### Symptom

Holding the thumb `&ht LSHIFT TAB` key emitted **TAB instead of SHIFT** most of
the time while typing, regardless of how long the key was held. Every other
hold-tap on the board behaved correctly, and swapping the physical switch made
no difference.

### Cause

The `&ht` behavior carried `global-quick-tap` together with
`quick-tap-ms = <150>`. In ZMK, `global-quick-tap` is a deprecated alias that
simply sets `require-prior-idle-ms` to the value of `quick-tap-ms`
(`app/src/behaviors/behavior_hold_tap.c`, `KP_INST`):

```c
.require_prior_idle_ms = DT_INST_PROP(n, global_quick_tap)
                             ? DT_INST_PROP(n, quick_tap_ms)
                             : DT_INST_PROP(n, require_prior_idle_ms),
```

On key-down, `is_quick_tap()` then short-circuits the whole decision:

```c
static bool is_quick_tap(struct active_hold_tap *hold_tap) {
    if ((last_tapped.timestamp + hold_tap->config->require_prior_idle_ms) > hold_tap->timestamp) {
        return true;   // -> decide_hold_tap(hold_tap, HT_QUICK_TAP) -> TAP
    }
    ...
}
```

`last_tapped` is refreshed by **every non-modifier keycode press anywhere on the
keyboard**. So if any letter was pressed within the previous 150 ms, the thumb
key resolved to a tap *immediately* on press — the hold branch was never even
considered, which is why holding harder or longer could not help. Because Shift
is almost always pressed right after typing a character, the failure rate was
very high.

Only this one key was affected because `&ht` had exactly one binding in the
keymap. The homerow mods use `hml`/`hmr`, and `&lt L1 SPACE` uses ZMK's stock
`&lt`, neither of which has global prior-idle gating on a thumb.

### Fix

Drop `global-quick-tap` from `ht`. Prior-idle gating exists to hide typing
latency on *alpha* keys that double as mods; thumb keys are never pressed
accidentally mid-word, so they should not use it. This matches urob's config,
where `require-prior-idle-ms` appears only in the homerow-mod macro and never on
the thumb hold-taps.

| Property                | Before  | After   | Why |
| ----------------------- | ------- | ------- | --- |
| `global-quick-tap`      | enabled | **removed** | Was forcing an instant tap whenever a key was pressed in the previous 150ms |
| `tapping-term-ms`       | 220     | 200     | Matches urob's thumb hold-taps |
| `quick-tap-ms`          | 150     | 175     | Matches urob's `QUICK_TAP_MS`; still allows fast TAB-TAB repeats |
| `flavor`                | balanced | balanced | Unchanged — resolves the hold as soon as another key is pressed and released |

`quick-tap-ms` is retained: without `global-quick-tap` it only applies to the
*same* key position, so tapping TAB and immediately pressing again still repeats
TAB rather than turning into Shift.

### Note on ZMK Studio

This shield builds with `CONFIG_ZMK_STUDIO=y`. Studio can only remap *bindings*,
not behavior properties, so this fix takes effect as soon as the new firmware is
flashed. If the thumb key has ever been remapped in Studio, however, the stored
keymap in flash wins over the compiled one — flash `settings_reset` first in
that case.

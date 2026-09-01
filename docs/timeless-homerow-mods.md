# Timeless Homerow Mods

This document describes the change that made the forager's homerow mods (`HRML`
and `HRMR`) "timeless", mirroring the approach used in
[urob's zmk-config](https://github.com/urob/zmk-config).

Only the homerow mods were changed. Layers, combos, the `&ht LSHIFT TAB` thumb
key, and the physical layout are all untouched.

> **Update:** the `&ht` thumb behavior *was* subsequently changed — see
> [Thumb keys must not use prior-idle gating](#thumb-keys-must-not-use-prior-idle-gating).
>
> **Update 2:** items 3 and 4 below (`hold-trigger-key-positions` and
> `hold-trigger-on-release`) have since been **removed** from all boards
> because they made same-hand shortcuts impossible — see
> [Cross-hand gating was removed](#cross-hand-gating-was-removed) at the end of
> this document. The rest of the setup (items 1 and 2) is unchanged.

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

## The other outer thumb: layer-taps must not be `tap-preferred`

### Symptom

The same class of failure on the **other** thumb: holding `&lt L1 SPACE` to
reach layer 1 would intermittently emit a literal **SPACE** (plus whatever key
was chorded with it) instead of activating the layer. Like the Shift/Tab bug it
was timing-dependent and happened many times a minute.

### Cause

This one is *not* prior-idle gating — it is the flavor. ZMK's stock `&lt`
(`app/dts/behaviors/layer_tap.dtsi`) is:

```dts
lt: layer_tap {
    compatible = "zmk,behavior-hold-tap";
    flavor = "tap-preferred";
    tapping-term-ms = <200>;
    bindings = <&mo>, <&kp>;
};
```

`tap-preferred` only ever resolves a hold from two events — the key's own
release, or the tapping-term timer firing:

```c
static void decide_tap_preferred(struct active_hold_tap *hold_tap, enum decision_moment event) {
    case HT_KEY_UP:      hold_tap->status = STATUS_TAP;         return;
    case HT_TIMER_EVENT: hold_tap->status = STATUS_HOLD_TIMER;  return;
    case HT_QUICK_TAP:   hold_tap->status = STATUS_TAP;         return;
}
```

Note the absence of `HT_OTHER_KEY_UP`. Pressing *and releasing* another key
while the layer-tap is held does **not** trigger the hold. So any layer chord
completed faster than the 200 ms tapping term resolves as a tap, emitting
`SPACE` followed by the other key. `balanced` handles exactly that case:

```c
case HT_OTHER_KEY_UP: hold_tap->status = STATUS_HOLD_INTERRUPT; return;
```

### Fix

Override `&lt` globally, matching urob's config:

```dts
&lt {
    flavor = "balanced";
    tapping-term-ms = <200>;
    quick-tap-ms = <175>;
};
```

Now a layer chord resolves as a hold the moment the chorded key is released,
with no dependence on beating a 200 ms timer.

### Scope

Both thumb defects are the same underlying mistake — a hold-tap configured so
that it resolves to a *tap* without ever considering the hold — and they were
applied across all the boards in this collection:

| Repo | Left outer thumb | Right outer thumb | Homerow |
| ---- | ---------------- | ----------------- | ------- |
| `forager`    | `ht` — dropped `global-quick-tap` | `lt` — now `balanced` | already timeless |
| `sweep`      | `ht` — dropped `global-quick-tap` | `lt` — now `balanced` | split out to `hml`/`hmr`, now timeless |
| `totemist`   | `ht` — dropped `global-quick-tap` | `lt` — now `balanced` | split out to `hml`/`hmr`, now timeless |
| `hillside52` | `ht` — already correct | `lt` — now `balanced` | already timeless |

`sweep` and `totemist` were the worst offenders because a single `ht` behavior
was shared by *both* the thumbs and every homerow mod, so the one bad
`global-quick-tap` broke ten keys per board rather than one.

## Reference

- urob's writeup on timeless homerow mods: <https://github.com/urob/zmk-config>
- ZMK hold-tap docs: <https://zmk.dev/docs/keymaps/behaviors/hold-tap>

## Cross-hand gating was removed

### Symptom

On the totemist, left-hand homerow mods emitted their **tap** keycode instead of
the modifier, no matter how long the key was held. `CMD+C` typed `fc`, `CMD+Q`
typed `fq`, and capitalising a left-hand letter produced a two-letter roll. The
right hand was affected too, but much less noticeably.

### Cause

Items 3 and 4 above — `hold-trigger-key-positions` and `hold-trigger-on-release`.

The positional gate is **absolute**: there is no timeout escape hatch. If the
next key pressed is on the same half, the hold-tap can *never* resolve as a
hold, however long you hold it. On these layouts every common shortcut is
same-hand:

- `LGUI` is on `F`, so `CMD` + `Q W A S Z X C V` are all left-hand
- `LSHIFT` is on `A`, so every capital of a left-hand letter is left-hand
- `LCTRL` on `S` and `LALT` on `D` have the same problem

urob's config gets away with this because it defines same-hand shortcuts as
combos instead. These configs do not, so the gate simply removed the ability to
use those shortcuts.

### Fix

Dropped both properties from `hml` / `hmr` on every board, and reduced the
tapping term from 280ms back to 220ms. That last part matters: with the
positional gate gone, the tapping term becomes the window in which a same-hand
roll could still resolve as a hold (`balanced` resolves on the other key's
release), so a shorter term narrows the exposure. `require-prior-idle-ms` is
retained and is now the main guard against false mods while typing.

Final homerow settings, identical on all four boards:

| Property                     | Value      |
| ---------------------------- | ---------- |
| `flavor`                     | `balanced` |
| `tapping-term-ms`            | 220        |
| `quick-tap-ms`               | 150        |
| `require-prior-idle-ms`      | 150        |
| `hold-trigger-key-positions` | *(none)*   |
| `hold-trigger-on-release`    | *(none)*   |

### Trade-off

A fast same-hand roll that *starts* on the homerow after more than 150ms of idle
time (`as`, `sad`, `fad`) can now register a modifier. This is the failure mode
the positional gate was there to prevent. If it turns out to be more annoying
than losing same-hand shortcuts, the `KEYS_L` / `KEYS_R` / `THUMBS` defines are
still present in every keymap, so re-adding the two properties is a two-line
change — but pair it with combos for the same-hand shortcuts.

### Scope

| Repo | Homerow gating | Notes |
| ---- | -------------- | ----- |
| `totemist`   | removed | where the problem was reported |
| `forager`    | removed | same layout, same latent problem |
| `sweep`      | removed | same layout, same latent problem |
| `hillside52` | removed | lower impact — it also has dedicated modifier keys |


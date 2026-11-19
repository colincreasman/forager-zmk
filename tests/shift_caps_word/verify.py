#!/usr/bin/env python3
"""Verify the Shift thumb and Caps Word/maintenance combo, then run the native test."""

import os
from pathlib import Path
import re
import subprocess
import sys

test_dir = Path(__file__).resolve().parent
repo = test_dir.parents[1]
fixture = (test_dir / "native_posix_64.keymap").read_text()


def node(text, name):
    match = re.search(rf"(?m)^\s*(?:\w+:\s*)?{re.escape(name)}\s*\{{", text)
    if not match:
        return None
    end = text.index("{", match.start()) + 1
    depth = 1
    while depth:
        depth += (text[end] == "{") - (text[end] == "}")
        end += 1
    return re.sub(r"\s+", "", re.sub(r"//.*", "", text[match.start() : end]))


for keymap in (repo / "boards/shields/forager/forager.keymap",):
    source = keymap.read_text()
    if node(source, "shift_tab") != node(fixture, "shift_tab"):
        sys.exit(f"shift_tab in {keymap} differs from the native test")
    for binding in ("&hml LSHFT A", "&hmr RSHFT BSLH", "&shift_tab LSHFT TAB"):
        if binding not in source:
            sys.exit(f"{binding} missing from {keymap}")
    if "caps_dance" in source or "a_shift" in source or "bslash_shift" in source:
        sys.exit(f"Double-tap Caps Word remains in {keymap}")
    if node(source, "caps_sys") != node(fixture, "caps_sys"):
        sys.exit(f"caps_sys in {keymap} differs from the native test")
    combo = node(source, "combo_caps_word_maintenance")
    if combo is None or "key-positions=<3033>" not in combo:
        sys.exit(f"Caps Word combo must use Enter (30) and Backspace (33) in {keymap}")
    translated = (
        combo.replace("<3033>", "<67>")
        .replace("&caps_sysL30", "&caps_sys20")
        .replace("<L0L1L2>", "<01>")
    )
    if translated != node(fixture, "combo_caps_word_maintenance"):
        sys.exit(f"Caps Word combo in {keymap} differs from the native test")

zmk = os.environ.get("ZMK_SRC_DIR")
if not zmk:
    sys.exit("Set ZMK_SRC_DIR to the ZMK app directory")
subprocess.run([str(Path(zmk) / "run-test.sh"), str(test_dir)], check=True)

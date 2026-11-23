"""Subset the two fonts to the glyphs the hero uses, into hero/fonts/.

usage: HERO_FONTS=<folder with clash-display-600.woff2 and martian-mono-var-latin.woff2> python3 hero/subset.py
Needs fonttools and brotli (pip install fonttools brotli). Re-run it whenever a
label below changes, and keep LABELS in step with the labels in gen.py.
"""
import os
from fontTools.ttLib import TTFont
from fontTools import subset
from fontTools.varLib import instancer
F = os.path.join(os.environ["HERO_FONTS"], "")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
os.makedirs(OUT, exist_ok=True)
LABELS = ["SOFTWARE ENGINEER", "PARIS", "SYSTEMS THAT SHOW THEIR WORK", "ROMAINCOUPEY.COM"]

def run(src, dst, text, features, pin=None):
    f = TTFont(F + src)
    if pin and "fvar" in f:
        print(src, "axes", [(a.axisTag, a.minValue, a.defaultValue, a.maxValue) for a in f["fvar"].axes])
        f = instancer.instantiateVariableFont(f, pin)
    o = subset.Options()
    o.layout_features = features
    o.name_IDs = []
    o.notdef_outline = False
    o.hinting = False
    o.desubroutinize = True
    o.flavor = "woff2"
    s = subset.Subsetter(o)
    s.populate(text=text)
    s.subset(f)
    f.flavor = "woff2"
    dst = os.path.join(OUT, dst)
    f.save(dst)
    print(dst, os.path.getsize(dst), "bytes", "glyphs", len(f.getGlyphOrder()))

run("clash-display-600.woff2", "clash.woff2", "ROMAINCOUPEY", ["kern"])
run("martian-mono-var-latin.woff2", "martian.woff2", "".join(LABELS), [], pin={"wght": 400})

#!/usr/bin/env python3
"""README hero, direction C "optics bench": one self-contained animated SVG.

usage: python3 hero/gen.py images/hero.svg [--static] [--no-grain]

Fonts: reads the subset files hero/fonts/clash.woff2 and hero/fonts/martian.woff2
(not committed; build them with hero/subset.py). Without them it falls back to
the whole font files in the folder named by HERO_FONTS, which makes a larger SVG.

Animation rules: CSS keyframes on transform and opacity only. Every animated
group is pivoted by nesting translate() groups, so no transform-origin is used.
All periods divide LOOP, and every keyframe set starts and ends on the resting
pose, so time zero, the loop point and the un-animated state are the same frame.
"""
import base64, math, os, sys

OUT = sys.argv[1]
STATIC = "--static" in sys.argv
GRAIN = "--no-grain" not in sys.argv
HERE = os.path.dirname(os.path.abspath(__file__))
SITE_FONTS = os.path.join(os.environ.get("HERO_FONTS", ""), "")  # folder holding the site's woff2 files

def font(sub, whole):
    p = os.path.join(HERE, "fonts", sub)
    if not os.path.exists(p):
        p = SITE_FONTS + whole
    return base64.b64encode(open(p, "rb").read()).decode()

CD = font("clash.woff2", "clash-display-600.woff2")
MM = font("martian.woff2", "martian-mono-var-latin.woff2")

LOOP = 14                    # seconds
W, H = 846, 470
MX = 42                      # side margin
TW = W - 2 * MX              # text block width (762)
FS = 178                     # cap height = 0.67em = 119
B1, B2 = 183, 320            # baselines; 18px gap between the lines
CX, CY, R = 378, 268, 92     # sphere, centred on the U of COUPEY
RAY_Y = (B1 + (B2 - 0.67 * FS)) / 2   # the ray threads the gap between the two lines
word = (f'<text x="{MX}" y="{B1}" textLength="{TW}" lengthAdjust="spacing">ROMAIN</text>'
        f'<text x="{MX}" y="{B2}" textLength="{TW}" lengthAdjust="spacing">COUPEY</text>')

# --- optics geometry -------------------------------------------------------
dy = CY - RAY_Y
ex, ey = CX - math.sqrt(R * R - dy * dy), RAY_Y      # where the ray enters the glass
a_out = math.radians(36)                             # exit point, 36 deg below the horizontal
ox, oy = CX + R * math.cos(a_out), CY + R * math.sin(a_out)
red, vio = (786, 374), (694, 410)                    # where the fan lands (red bends least)
SPEC = ["#ff5b6a", "#ffa04a", "#ffe36a", "#63f09a", "#4fd6ff", "#6583ff", "#b56cff"]

def ang(p):  return math.atan2(p[1] - oy, p[0] - ox)
def dist(p): return math.hypot(p[0] - ox, p[1] - oy)
AXIS = (ang(red) + ang(vio)) / 2                     # fan axis; the fan is drawn in a frame with
def local(p):                                        # the apex at 0,0 and the axis along +x
    a, d = ang(p) - AXIS, dist(p)
    return (d * math.cos(a), d * math.sin(a))
LR, LV = local(red), local(vio)

def lerp(p, q, t): return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)
def hexrgb(h): return [int(h[i:i + 2], 16) for i in (1, 3, 5)]
def spec_at(t):
    x = t * (len(SPEC) - 1); i = min(int(x), len(SPEC) - 2); f = x - i
    a, b = hexrgb(SPEC[i]), hexrgb(SPEC[i + 1])
    return "#%02x%02x%02x" % tuple(round(a[k] + (b[k] - a[k]) * f) for k in range(3))

NW, OVER = 26, 1.07          # wedges; each runs a little past the floor line, the mask fades it
wedges = []
for i in range(NW):
    p, q = lerp(LR, LV, i / NW), lerp(LR, LV, (i + 1.4) / NW)
    wedges.append(f'<path d="M0 0L{p[0]*OVER:.1f} {p[1]*OVER:.1f}L{q[0]*OVER:.1f} {q[1]*OVER:.1f}Z" fill="{spec_at((i + .5) / NW)}"/>')
wedges = "".join(wedges)
# floor line in the fan frame, and the normal pointing away from the glass
fdx, fdy = LV[0] - LR[0], LV[1] - LR[1]
fl = math.hypot(fdx, fdy)
nx, ny = -fdy / fl, fdx / fl
mid = lerp(LR, LV, .5)
if nx * mid[0] + ny * mid[1] < 0: nx, ny = -nx, -ny
g0 = (mid[0] - nx * 16, mid[1] - ny * 16)
g1 = (mid[0] + nx * 12, mid[1] + ny * 12)
smear = []
for i, c in enumerate(SPEC):
    p = lerp(LR, LV, i / (len(SPEC) - 1))
    smear.append(f'<ellipse cx="{p[0]+7:.1f}" cy="{p[1]+1:.1f}" rx="24" ry="3.4" fill="{c}" transform="rotate({-math.degrees(AXIS)-7:.1f} {p[0]:.1f} {p[1]:.1f})"/>')
smear = "".join(smear)

# --- floor grid ------------------------------------------------------------
HZ = 236
grid = []
for i in range(-16, 17):
    grid.append(f'M{W/2:.0f} {HZ}L{W/2 + i*96:.0f} {H}')
k = 0
while True:
    y = HZ + (H - HZ) / (1 + k * 0.42)
    if y < HZ + 34: break
    grid.append(f'M0 {y:.1f}H{W}')
    k += 1
grid_d = "".join(grid)

lab = lambda x, y, t, anchor="start": f'<text class="l" x="{x}" y="{y}" text-anchor="{anchor}">{t}</text>'

# --- motion ----------------------------------------------------------------
SINE_OUT, SINE_IO, SINE_IN = "cubic-bezier(.61,1,.88,1)", "cubic-bezier(.37,0,.63,1)", "cubic-bezier(.12,0,.39,0)"
def swing(name, a, b):
    """rest -> a -> b -> rest as one sine period; a and b are CSS declarations."""
    return (f'@keyframes {name}{{0%{{{REST[name]};animation-timing-function:{SINE_OUT}}}'
            f'25%{{{a};animation-timing-function:{SINE_IO}}}75%{{{b};animation-timing-function:{SINE_IN}}}100%{{{REST[name]}}}}}')
REST = {"sw": "transform:rotate(0deg)", "si": "transform:rotate(0deg)", "sf": "transform:rotate(0deg)",
        "fw": "transform:scaleY(1)", "hl": "transform:translate(0px,0px)", "cs": "transform:translate(0px,0px)"}
CF = 5.5                     # caustic layers drift this far either side while they fade through
css_anim = "" if STATIC else f'''
.a{{animation-duration:{LOOP}s;animation-iteration-count:infinite;animation-timing-function:linear}}
{swing("sw", "transform:rotate(-.9deg)", "transform:rotate(.9deg)")}
{swing("si", "transform:rotate(-1.25deg)", "transform:rotate(1.25deg)")}
{swing("sf", "transform:rotate(-2.5deg)", "transform:rotate(2.5deg)")}
{swing("fw", "transform:scaleY(1.16)", "transform:scaleY(.84)")}
{swing("hl", "transform:translate(2.6px,-1.2px)", "transform:translate(-2.2px,1.6px)")}
{swing("cs", "transform:translate(-5px,0px)", "transform:translate(5px,0px)")}
@keyframes br{{0%,100%{{opacity:1}}50%{{opacity:.52}}}}
@keyframes cf{{0%{{opacity:0;transform:translate({-CF}px,1.4px);animation-timing-function:{SINE_OUT}}}33.333%{{opacity:1;transform:translate(0px,0px);animation-timing-function:{SINE_IN}}}66.667%,100%{{opacity:0;transform:translate({CF}px,-1.4px)}}}}
.sw{{animation-name:sw}}.si{{animation-name:si}}.sf{{animation-name:sf}}.fw{{animation-name:fw}}.hl{{animation-name:hl}}.cs{{animation-name:cs}}
.br{{animation-name:br;animation-duration:{LOOP/2:g}s;animation-timing-function:{SINE_IO}}}
.c0,.c1,.c2{{animation-name:cf}}.c0{{animation-delay:0s}}.c1{{animation-delay:-{LOOP/3:.4f}s}}.c2{{animation-delay:-{2*LOOP/3:.4f}s}}
@media (prefers-reduced-motion:reduce){{.a{{animation:none!important}}}}'''

CA = (CX - 172, 340, 384, 116)                       # caustic patch (filter region)
caustic_filters = "".join(f'''<filter id="ca{i}" filterUnits="userSpaceOnUse" x="{CA[0]}" y="{CA[1]}" width="{CA[2]}" height="{CA[3]}" color-interpolation-filters="sRGB">
<feTurbulence type="turbulence" baseFrequency=".015 .055" numOctaves="2" seed="{seed}" result="n"/>
<feColorMatrix in="n" type="matrix" values="0 0 0 0 .86  0 0 0 0 .83  0 0 0 0 1  -8.5 -3.2 0 0 1.62" result="f"/>
<feGaussianBlur in="f" stdDeviation=".55" result="f1"/><feGaussianBlur in="f" stdDeviation="5" result="f2"/>
<feMerge><feMergeNode in="f2"/><feMergeNode in="f1"/><feMergeNode in="f1"/></feMerge></filter>''' for i, seed in enumerate((3, 7, 12)))
# layer 1 is the resting layer: at time zero it sits at the 33% keyframe, fully opaque
caustic_layers = "".join(
    f'<g class="a c{i}" opacity="{1 if i == 1 else 0}"><rect x="{CA[0]}" y="{CA[1]}" width="{CA[2]}" height="{CA[3]}" filter="url(#ca{i})"/></g>'
    for i in range(3))

grain_defs = f'''<filter id="gr" x="0" y="0" width="100%" height="100%" color-interpolation-filters="sRGB"><feTurbulence type="fractalNoise" baseFrequency="1.2" numOctaves="1" seed="5" stitchTiles="stitch"/><feColorMatrix type="matrix" values="0 0 0 0 .82  0 0 0 0 .8  0 0 0 0 1  .8 0 0 0 -.4"/></filter>
<pattern id="gp" patternUnits="userSpaceOnUse" width="128" height="128"><rect width="128" height="128" filter="url(#gr)"/></pattern>''' if GRAIN else ""
grain_use = f'<rect width="{W}" height="{H}" fill="url(#gp)" opacity=".42"/>' if GRAIN else ""

dxi, dyi = (ox - ex) * 1.35, (oy - ey) * 1.35        # inner ray, drawn long and clipped by the glass
AX = math.degrees(AXIS)

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">
<title id="t">Romain Coupey</title>
<desc id="d">A ray of light enters a glass sphere set in front of the name Romain Coupey, bends, and leaves as a soft fan of spectral colour that pools on the floor.</desc>
<style>
@font-face{{font-family:CD;font-weight:600;src:url(data:font/woff2;base64,{CD}) format("woff2")}}
@font-face{{font-family:MM;font-weight:400;src:url(data:font/woff2;base64,{MM}) format("woff2")}}
.w text{{font-family:CD,"Arial Black",Impact,sans-serif;font-weight:600;font-size:{FS}px}}
.l{{font-family:MM,ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:8.6px;font-weight:400;letter-spacing:1.7px;fill:#b3afdc;fill-opacity:.78}}
.s{{mix-blend-mode:screen}}{css_anim}
</style>
<defs>
<clipPath id="rc"><rect width="{W}" height="{H}" rx="12"/></clipPath>
<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#08071c"/><stop offset=".5" stop-color="#0d0c2a"/><stop offset="1" stop-color="#15133d"/></linearGradient>
<radialGradient id="haze" gradientUnits="userSpaceOnUse" cx="700" cy="-10" r="560"><stop offset="0" stop-color="#8d86ea" stop-opacity=".62"/><stop offset=".42" stop-color="#4a4499" stop-opacity=".3"/><stop offset="1" stop-color="#211e5a" stop-opacity="0"/></radialGradient>
<radialGradient id="floorglow" gradientUnits="userSpaceOnUse" cx="{CX+90}" cy="402" r="330" gradientTransform="translate(0 402) scale(1 .42) translate(0 -402)"><stop offset="0" stop-color="#6f68d8" stop-opacity=".55"/><stop offset=".5" stop-color="#3b3690" stop-opacity=".22"/><stop offset="1" stop-color="#1b1850" stop-opacity="0"/></radialGradient>
<radialGradient id="vig" gradientUnits="userSpaceOnUse" cx="{W/2}" cy="{H/2}" r="520"><stop offset=".55" stop-color="#04030f" stop-opacity="0"/><stop offset="1" stop-color="#04030f" stop-opacity=".66"/></radialGradient>
<linearGradient id="gridfade" x1="0" y1="{HZ}" x2="0" y2="{H}" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#8a83e6" stop-opacity="0"/><stop offset=".35" stop-color="#8a83e6" stop-opacity=".09"/><stop offset="1" stop-color="#8a83e6" stop-opacity=".32"/></linearGradient>
<linearGradient id="ink" gradientUnits="userSpaceOnUse" x1="{W-MX}" y1="50" x2="{MX}" y2="330"><stop offset="0" stop-color="#f3eddd"/><stop offset=".5" stop-color="#e0dac9"/><stop offset="1" stop-color="#c6c0b0"/></linearGradient>
<g id="word" class="w">{word}</g>
<linearGradient id="rfade" gradientUnits="userSpaceOnUse" x1="0" y1="{B2}" x2="0" y2="{B2-64}"><stop offset="0" stop-color="#cfc8ee" stop-opacity=".2"/><stop offset=".5" stop-color="#cfc8ee" stop-opacity=".07"/><stop offset="1" stop-color="#cfc8ee" stop-opacity="0"/></linearGradient>
<clipPath id="rcl"><rect x="0" y="{B2+3}" width="{W}" height="66"/></clipPath>
{grain_defs}
<clipPath id="sc"><circle cx="{CX}" cy="{CY}" r="{R}"/></clipPath>
<radialGradient id="glassback" gradientUnits="userSpaceOnUse" cx="{CX-34}" cy="{CY+44}" r="{R*1.5:.0f}"><stop offset="0" stop-color="#5a54c2"/><stop offset=".45" stop-color="#26225f"/><stop offset="1" stop-color="#0d0b28"/></radialGradient>
<radialGradient id="glassshade" gradientUnits="userSpaceOnUse" cx="{CX}" cy="{CY}" r="{R}"><stop offset="0" stop-color="#b9b2ff" stop-opacity="0"/><stop offset=".55" stop-color="#8f88ee" stop-opacity=".04"/><stop offset=".78" stop-color="#0c0a2c" stop-opacity=".46"/><stop offset=".915" stop-color="#070519" stop-opacity=".78"/><stop offset=".965" stop-color="#8d86ee" stop-opacity=".55"/><stop offset="1" stop-color="#ebe8ff" stop-opacity=".95"/></radialGradient>
<radialGradient id="gather" gradientUnits="userSpaceOnUse" cx="{ox-16:.0f}" cy="{oy-12:.0f}" r="{R*.72:.0f}"><stop offset="0" stop-color="#fff" stop-opacity=".9"/><stop offset=".25" stop-color="#c9c2ff" stop-opacity=".55"/><stop offset="1" stop-color="#7d76e6" stop-opacity="0"/></radialGradient>
<linearGradient id="rim" gradientUnits="userSpaceOnUse" x1="{CX+R*.7:.0f}" y1="{CY-R*.7:.0f}" x2="{CX-R*.7:.0f}" y2="{CY+R*.7:.0f}"><stop offset="0" stop-color="#fff" stop-opacity=".95"/><stop offset=".5" stop-color="#a59fff" stop-opacity=".35"/><stop offset="1" stop-color="#cfcaff" stop-opacity=".75"/></linearGradient>
<filter id="sb" filterUnits="userSpaceOnUse" x="{CX-R-40}" y="{CY-R-40}" width="{2*R+80}" height="{2*R+80}"><feGaussianBlur stdDeviation="9"/></filter>
<filter id="hb" filterUnits="userSpaceOnUse" x="{CX-22}" y="{CY-100}" width="116" height="100"><feGaussianBlur stdDeviation="7"/></filter>
<filter id="hc" filterUnits="userSpaceOnUse" x="{CX-94}" y="{CY+14}" width="84" height="72"><feGaussianBlur stdDeviation="7"/></filter>
<filter id="gb" filterUnits="userSpaceOnUse" x="{CX+26}" y="{CY-74}" width="40" height="36"><feGaussianBlur stdDeviation="1.3"/></filter>
<filter id="lens" filterUnits="userSpaceOnUse" x="{CX-R}" y="{CY-R}" width="{2*R}" height="{2*R}"><feGaussianBlur stdDeviation=".7"/></filter>
<filter id="shb" filterUnits="userSpaceOnUse" x="{CX-150}" y="350" width="320" height="80"><feGaussianBlur stdDeviation="9 4"/></filter>
<filter id="b1" filterUnits="userSpaceOnUse" x="{CX-60}" y="375" width="180" height="40"><feGaussianBlur stdDeviation="1"/></filter>
<radialGradient id="cmask" gradientUnits="userSpaceOnUse" cx="{CX+34}" cy="398" r="170" gradientTransform="translate(0 398) scale(1 .27) translate(0 -398)"><stop offset="0" stop-color="#fff" stop-opacity="1"/><stop offset=".45" stop-color="#fff" stop-opacity=".7"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>
<mask id="cm" maskUnits="userSpaceOnUse" x="{CX-160}" y="346" width="360" height="104"><rect x="{CX-160}" y="346" width="360" height="104" fill="url(#cmask)"/></mask>
{caustic_filters}
<!-- incoming ray, in a frame whose origin is the entry point -->
<linearGradient id="rayin" gradientUnits="userSpaceOnUse" x1="{-ex:.0f}" y1="0" x2="0" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".12" stop-color="#fff" stop-opacity=".85"/><stop offset="1" stop-color="#fff" stop-opacity="1"/></linearGradient>
<filter id="r3" filterUnits="userSpaceOnUse" x="{-ex-90:.0f}" y="-24" width="{ex+120:.0f}" height="48"><feGaussianBlur stdDeviation="3.2"/></filter>
<filter id="r9" filterUnits="userSpaceOnUse" x="{-ex-90:.0f}" y="-44" width="{ex+130:.0f}" height="88"><feGaussianBlur stdDeviation="9"/></filter>
<filter id="ib" filterUnits="userSpaceOnUse" x="-24" y="-24" width="{dxi+48:.0f}" height="{dyi+48:.0f}"><feGaussianBlur stdDeviation="5"/></filter>
<filter id="pt" filterUnits="userSpaceOnUse" x="-40" y="-40" width="80" height="80"><feGaussianBlur stdDeviation="4.2"/></filter>
<!-- spectral fan, in a frame whose origin is the exit point and whose x axis is the fan axis -->
<linearGradient id="la" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{LR[0]:.0f}" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".12" stop-color="#fff" stop-opacity=".2"/><stop offset=".36" stop-color="#fff" stop-opacity=".82"/><stop offset=".7" stop-color="#fff" stop-opacity=".5"/><stop offset="1" stop-color="#fff" stop-opacity=".3"/></linearGradient>
<linearGradient id="lb" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{LR[0]:.0f}" y2="0"><stop offset=".08" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".62"/><stop offset="1" stop-color="#fff" stop-opacity=".66"/></linearGradient>
<linearGradient id="lw" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{LR[0]*.5:.0f}" y2="0"><stop offset="0" stop-color="#fff" stop-opacity=".95"/><stop offset=".45" stop-color="#e9e4ff" stop-opacity=".5"/><stop offset="1" stop-color="#cfc8ff" stop-opacity="0"/></linearGradient>
<linearGradient id="le" gradientUnits="userSpaceOnUse" x1="{g0[0]:.1f}" y1="{g0[1]:.1f}" x2="{g1[0]:.1f}" y2="{g1[1]:.1f}"><stop offset="0" stop-color="#fff" stop-opacity="1"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<mask id="ma" maskUnits="userSpaceOnUse" x="-16" y="-62" width="400" height="124"><rect x="-16" y="-62" width="400" height="124" fill="url(#la)"/></mask>
<mask id="mb" maskUnits="userSpaceOnUse" x="-16" y="-62" width="400" height="124"><rect x="-16" y="-62" width="400" height="124" fill="url(#lb)"/></mask>
<mask id="me" maskUnits="userSpaceOnUse" x="-16" y="-62" width="400" height="124"><rect x="-16" y="-62" width="400" height="124" fill="url(#le)"/></mask>
<filter id="f1" filterUnits="userSpaceOnUse" x="-16" y="-62" width="400" height="124"><feGaussianBlur stdDeviation="1.5"/></filter>
<filter id="f6" filterUnits="userSpaceOnUse" x="-24" y="-70" width="420" height="140"><feGaussianBlur stdDeviation="7"/></filter>
<filter id="f3" filterUnits="userSpaceOnUse" x="210" y="-62" width="180" height="124"><feGaussianBlur stdDeviation="3.6"/></filter>
<g id="fan">{wedges}</g>
</defs>

<g clip-path="url(#rc)">
<!-- field -->
<rect width="{W}" height="{H}" fill="url(#bg)"/>
<rect width="{W}" height="{H}" fill="url(#haze)"/>
<rect x="{CX+90-332}" y="262" width="664" height="{H-262}" fill="url(#floorglow)"/>
{grain_use}
<path d="{grid_d}" fill="none" stroke="url(#gridfade)" stroke-width=".8"/>

<!-- the name, and its faint mirror on the floor -->
<use xlink:href="#word" href="#word" fill="url(#ink)"/>
<g clip-path="url(#rcl)"><use xlink:href="#word" href="#word" fill="url(#rfade)" transform="translate(0 {2*B2+3}) scale(1 -1)"/></g>
<rect width="{W}" height="{H}" fill="url(#vig)"/>

{lab(MX, 30, "SOFTWARE ENGINEER")}
{lab(W-MX, 30, "PARIS", "end")}
{lab(MX, H-18, "SYSTEMS THAT SHOW THEIR WORK")}
{lab(W-MX, H-18, "ROMAINCOUPEY.COM", "end")}

<!-- contact shadow, then the caustic pool: three pre-filtered layers that drift and cross-fade -->
<ellipse cx="{CX+4}" cy="388" rx="74" ry="11" fill="#04030f" fill-opacity=".7" filter="url(#shb)"/>
<g class="s">
<g mask="url(#cm)">{caustic_layers}</g>
<g class="a cs">
<ellipse cx="{CX+16}" cy="394" rx="70" ry="8" fill="#cfc8ff" fill-opacity=".7" filter="url(#shb)"/>
<ellipse cx="{CX+24}" cy="395" rx="20" ry="2.4" fill="#fff" fill-opacity=".8" filter="url(#b1)"/>
</g>
</g>

<!-- spectral fan: rotates about the sphere centre with the exit point, and breathes across its axis -->
<g class="s"><g transform="translate({CX} {CY})"><g class="a sf"><g transform="translate({ox-CX:.2f} {oy-CY:.2f}) rotate({AX:.2f})">
<g class="a fw">
<g mask="url(#me)">
<g mask="url(#mb)"><use xlink:href="#fan" href="#fan" opacity=".8" filter="url(#f6)"/></g>
<g mask="url(#ma)"><use xlink:href="#fan" href="#fan" opacity=".9" filter="url(#f1)"/></g>
</g>
<path d="M0 0L{LR[0]*.5:.1f} {-2.6:.1f}L{LR[0]*.5:.1f} {2.6:.1f}Z" fill="url(#lw)" filter="url(#f1)"/>
<g opacity=".42" filter="url(#f3)">{smear}</g>
</g>
<circle class="a br" r="12" fill="#fff" fill-opacity=".85" filter="url(#pt)"/>
<circle r="2.2" fill="#fff"/>
</g></g></g></g>

<!-- the glass -->
<circle class="s" cx="{CX}" cy="{CY}" r="{R+10}" fill="#7f78ea" fill-opacity=".2" filter="url(#sb)"/>
<g clip-path="url(#sc)">
<circle cx="{CX}" cy="{CY}" r="{R}" fill="url(#glassback)"/>
<g transform="translate({CX} {CY}) scale(1.1) translate({-CX} {-CY})" filter="url(#lens)">
<use class="s" xlink:href="#word" href="#word" fill="#ff5a6e" fill-opacity=".7" transform="translate(-2.6 -.6)"/>
<use class="s" xlink:href="#word" href="#word" fill="#4f8dff" fill-opacity=".75" transform="translate(2.6 .6)"/>
<use xlink:href="#word" href="#word" fill="#d9d3ea"/>
</g>
<circle class="s" cx="{CX}" cy="{CY}" r="{R}" fill="url(#gather)"/>
<g class="s" transform="translate({ex:.2f} {ey:.2f})"><g class="a si" stroke-linecap="round" fill="none">
<path d="M0 0L{dxi:.1f} {dyi:.1f}" stroke="#d9d2ff" stroke-width="7" stroke-opacity=".5" filter="url(#ib)"/>
<path d="M0 0L{dxi:.1f} {dyi:.1f}" stroke="#fff" stroke-width="1.1" stroke-opacity=".72"/>
</g></g>
<circle cx="{CX}" cy="{CY}" r="{R}" fill="url(#glassshade)"/>
<g class="a hl">
<ellipse class="s" cx="{CX+34}" cy="{CY-50}" rx="36" ry="17" fill="#fff" fill-opacity=".5" transform="rotate(32 {CX+34} {CY-50})" filter="url(#hb)"/>
<ellipse class="s" cx="{CX+46}" cy="{CY-56}" rx="11" ry="4.5" fill="#fff" fill-opacity=".95" transform="rotate(34 {CX+46} {CY-56})" filter="url(#gb)"/>
</g>
<ellipse class="s" cx="{CX-52}" cy="{CY+50}" rx="20" ry="6" fill="#bdb6ff" fill-opacity=".45" transform="rotate(38 {CX-52} {CY+50})" filter="url(#hc)"/>
</g>
<circle cx="{CX}" cy="{CY}" r="{R-.5}" fill="none" stroke="url(#rim)" stroke-width="1.1"/>

<!-- the incoming ray: sweeps a degree or so about the point where it meets the glass -->
<g class="s" transform="translate({ex:.2f} {ey:.2f})">
<g class="a sw" fill="none" stroke-linecap="round">
<path d="M{-ex-60:.0f} 0H0" stroke="#8f88ff" stroke-width="16" stroke-opacity=".34" filter="url(#r9)"/>
<path d="M{-ex-60:.0f} 0H0" stroke="#cfc9ff" stroke-width="5" stroke-opacity=".8" filter="url(#r3)"/>
<path d="M{-ex-60:.0f} 0H0" stroke="url(#rayin)" stroke-width="1.5"/>
</g>
<circle class="a br" r="10" fill="#e6e1ff" fill-opacity=".9" filter="url(#pt)"/>
<circle r="2.2" fill="#fff"/>
</g>
</g>
</svg>
'''
open(OUT, "w").write(svg)
print(OUT, len(svg), "bytes | entry", round(ex, 1), round(ey, 1), "| exit", round(ox, 1), round(oy, 1), "| axis", round(AX, 2), "| fan ends", [round(v, 1) for v in LR + LV])

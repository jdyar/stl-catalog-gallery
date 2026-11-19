#!/usr/bin/env python3
"""Create a self-made dummy catalog (simple OpenSCAD shapes) to test the gallery generator."""
import json, os, shutil, subprocess, sys, pathlib
def find_openscad():
    for c in (os.environ.get("OPENSCAD"), shutil.which("openscad"), shutil.which("openscad-nightly")):
        if c:
            return c
    sys.exit("OpenSCAD not found. Install it and put 'openscad' on your PATH, or set the OPENSCAD environment variable.")

OS = find_openscad()
ROOT = pathlib.Path(__file__).parent/"sample_catalog"
MODELS = [
 ("2026-01", "Stone Well", ["terrain","dungeon"], "Basic", "difference(){cylinder(r=20,h=18,$fn=48);translate([0,0,2])cylinder(r=16,h=20,$fn=48);}"),
 ("2026-01", "Supply Crate Set", ["terrain","props"], "Basic", "for(i=[0:2])translate([i*24,0,0])cube([20,20,20-i*4]);"),
 ("2026-02", "Rune Pillar", ["terrain","magic"], "Basic", "cylinder(r1=8,r2=6,h=40,$fn=6);"),
 ("2026-02", "Goblin Banner Pole", ["miniature","goblin"], "Merchant", "union(){cylinder(r=1.5,h=45,$fn=16);translate([0,0,30])cube([14,1,12]);cylinder(r=10,h=3,$fn=40);}"),
 ("2026-03", "Arch Gate", ["terrain","dungeon"], "Basic", "difference(){cube([40,8,36]);translate([10,-1,0])cube([20,10,24]);translate([20,-1,24])rotate([-90,0,0])cylinder(r=10,h=10,$fn=40);}"),
 ("2026-03", "Treasure Chest", ["props","loot"], "Merchant", "union(){cube([24,14,10]);translate([0,7,10])rotate([0,90,0])cylinder(r=7,h=24,$fn=32);}"),
 ("2026-04", "Hex Base 25mm (10 pack)", ["bases"], "Basic", "for(i=[0:4],j=[0:1])translate([i*28,j*28,0])cylinder(r=12.5,h=3,$fn=6);"),
 ("2026-04", "Crystal Cluster", ["terrain","magic"], "Merchant", "for(a=[0:60:300])rotate([20,0,a])cylinder(r1=4,r2=0,h=26,$fn=6);"),
]
for month, title, tags, tier, scad in MODELS:
    slug = title.lower().replace(" ", "-").replace("(", "").replace(")", "")
    d = ROOT/month/slug; d.mkdir(parents=True, exist_ok=True)
    (d/"model.scad").write_text(scad + "\n")
    env = os.environ.copy(); env.setdefault("QT_QPA_PLATFORM", "offscreen")
    subprocess.run([OS, "-o", str(d/f"{slug}.stl"), str(d/"model.scad")], capture_output=True, env=env)
    (d/"model.scad").unlink()
    json.dump({"title": title, "tags": tags, "tier": tier, "release": month,
               "patreon_url": f"https://www.patreon.com/posts/example-{slug}",
               "notes": "Synthetic sample model for testing."}, open(d/"meta.json", "w"), indent=1)
print("sample models:", len(MODELS))

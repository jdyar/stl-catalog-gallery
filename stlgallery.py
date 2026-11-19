#!/usr/bin/env python3
"""stlgallery: turn a folder of 3D-print models into a static, searchable gallery.

Usage:  python stlgallery.py <catalog_dir> <output_dir> [--title "Creator Name Archive"] [--link-files]

Catalog layout (flexible): any folder that contains .stl/.3mf/.obj files is one model.
Optional meta.json per model: {"title", "tags", "tier", "release" (YYYY-MM), "patreon_url", "notes"}.
Missing fields are inferred: title from the folder name, release from a YYYY-MM parent folder,
tags from parent folder names. Existing images (jpg/png/webp) are used as previews; otherwise
a preview PNG is rendered from the first STL with OpenSCAD (headless).

SAFETY: model files are NEVER copied to the output unless --link-files is passed (for creators
who want public free files). By default each card links to the creator's own post (patreon_url).
"""
import argparse, html, json, os, re, shutil, subprocess, sys, pathlib

def find_openscad():
    for c in (os.environ.get("OPENSCAD"), shutil.which("openscad"), shutil.which("openscad-nightly")):
        if c:
            return c
    return None

MODEL_EXT = {".stl", ".3mf", ".obj"}
IMG_EXT = {".jpg", ".jpeg", ".png", ".webp"}

def find_models(root):
    dirs = sorted({p.parent for p in root.rglob("*") if p.suffix.lower() in MODEL_EXT})
    for d in dirs:
        meta = {}
        if (d/"meta.json").exists():
            meta = json.load(open(d/"meta.json"))
        rel = d.relative_to(root)
        parts = list(rel.parts)
        month = next((p for p in parts if re.fullmatch(r"\d{4}-\d{2}", p)), None)
        files = sorted(p for p in d.iterdir() if p.suffix.lower() in MODEL_EXT)
        imgs = sorted(p for p in d.iterdir() if p.suffix.lower() in IMG_EXT)
        yield {
            "id": re.sub(r"[^a-z0-9]+", "-", str(rel).lower()).strip("-"),
            "title": meta.get("title") or d.name.replace("-", " ").replace("_", " ").title(),
            "tags": meta.get("tags") or [p for p in parts[:-1] if p != month],
            "tier": meta.get("tier", ""),
            "release": meta.get("release") or month or "",
            "url": meta.get("patreon_url", ""),
            "notes": meta.get("notes", ""),
            "files": [f.name for f in files],
            "_dir": d, "_files": files, "_imgs": imgs,
        }

def render_preview(stl, png):
    cmd = find_openscad()
    if not cmd:
        return False
    scad = png.with_suffix(".scad")
    scad.write_text(f'color("SteelBlue") import("{stl.resolve()}");\n')
    env = os.environ.copy()
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    r = subprocess.run([cmd, "-o", str(png), "--imgsize=600,600", "--viewall", "--autocenter",
                        "--colorscheme=Tomorrow", "--camera=0,0,0,60,0,30,0", str(scad)],
                       capture_output=True, text=True, env=env)
    scad.unlink(missing_ok=True)
    return r.returncode == 0 and png.exists()

PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title><style>
:root{--bg:#f6f6f4;--card:#fff;--ink:#1d1d1f;--mute:#6b6b70;--acc:#2f6fdb}
@media(prefers-color-scheme:dark){:root{--bg:#141416;--card:#1f1f23;--ink:#ececf0;--mute:#9a9aa3;--acc:#7aa7ff}}
body{margin:0;font:15px/1.4 system-ui,-apple-system,Segoe UI,sans-serif;background:var(--bg);color:var(--ink)}
header{padding:20px 24px 8px}h1{margin:0 0 4px;font-size:22px}.sub{color:var(--mute)}
.bar{display:flex;flex-wrap:wrap;gap:8px;padding:8px 24px 16px;position:sticky;top:0;background:var(--bg)}
input,select{font:inherit;padding:8px 10px;border-radius:8px;border:1px solid #8884;background:var(--card);color:var(--ink)}
input{flex:1;min-width:200px}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:14px;padding:0 24px 40px}
.card{background:var(--card);border-radius:12px;overflow:hidden;box-shadow:0 1px 3px #0002;display:flex;flex-direction:column}
.card img{width:100%;aspect-ratio:1;object-fit:cover;background:#ddd}.body{padding:10px 12px 12px;display:flex;flex-direction:column;gap:4px;flex:1}
.t{font-weight:600}.meta{color:var(--mute);font-size:13px}.tags{display:flex;flex-wrap:wrap;gap:4px}
.tag{font-size:12px;padding:2px 7px;border-radius:99px;background:#8882;cursor:pointer}
a.btn{margin-top:auto;text-align:center;padding:7px;border-radius:8px;background:var(--acc);color:#fff;text-decoration:none;font-size:14px}
.count{padding:0 24px 8px;color:var(--mute)}footer{padding:20px 24px;color:var(--mute);font-size:12px}
</style></head><body>
<header><h1>__TITLE__</h1><div class="sub">Search every release. Downloads stay on the creator's page.</div></header>
<div class="bar"><input id="q" placeholder="Search titles, tags, notes..." autofocus>
<select id="tier"><option value="">All tiers</option></select><select id="month"><option value="">All months</option></select>
<select id="sort"><option value="new">Newest first</option><option value="old">Oldest first</option><option value="az">A to Z</option></select></div>
<div class="count" id="count"></div><div class="grid" id="grid"></div>
<footer>Generated __DATE__ by stlgallery. __NFILES__</footer>
<script>
const DATA=__DATA__;
const $=s=>document.querySelector(s), esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const uniq=a=>[...new Set(a)].filter(Boolean).sort();
uniq(DATA.map(d=>d.tier)).forEach(t=>$('#tier').add(new Option(t,t)));
uniq(DATA.map(d=>d.release)).reverse().forEach(m=>$('#month').add(new Option(m,m)));
function render(){const q=$('#q').value.toLowerCase().trim().split(/\\s+/).filter(Boolean),t=$('#tier').value,m=$('#month').value,s=$('#sort').value;
let r=DATA.filter(d=>(!t||d.tier===t)&&(!m||d.release===m)&&q.every(w=>(d.title+' '+d.tags.join(' ')+' '+d.notes+' '+d.files.join(' ')).toLowerCase().includes(w)));
r.sort((a,b)=>s==='az'?a.title.localeCompare(b.title):s==='old'?a.release.localeCompare(b.release):b.release.localeCompare(a.release));
$('#count').textContent=r.length+' of '+DATA.length+' models';
$('#grid').innerHTML=r.map(d=>`<div class="card"><img loading="lazy" src="${esc(d.img)}" alt="${esc(d.title)} preview"><div class="body">
<div class="t">${esc(d.title)}</div><div class="meta">${esc(d.release)}${d.tier?' · '+esc(d.tier):''} · ${d.files.length} file${d.files.length==1?'':'s'}</div>
<div class="tags">${d.tags.map(x=>`<span class="tag" data-t="${esc(x)}">${esc(x)}</span>`).join('')}</div>
${d.url?`<a class="btn" href="${esc(d.url)}" target="_blank" rel="noopener">Get it on the creator's page</a>`:''}
${d.dl?d.dl.map(f=>`<a class="btn" href="${esc(f)}" download>Download ${esc(f.split('/').pop())}</a>`).join(''):''}</div></div>`).join('');
document.querySelectorAll('.tag').forEach(e=>e.onclick=()=>{$('#q').value=e.dataset.t;render()});}
['#q','#tier','#month','#sort'].forEach(s=>$(s).addEventListener('input',render));render();
</script></body></html>"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("catalog"); ap.add_argument("out")
    ap.add_argument("--title", default="Model Archive")
    ap.add_argument("--link-files", action="store_true", help="copy model files into the site (only for files the creator gives away)")
    a = ap.parse_args()
    root, out = pathlib.Path(a.catalog), pathlib.Path(a.out)
    (out/"previews").mkdir(parents=True, exist_ok=True)
    items, problems = [], []
    for m in find_models(root):
        img = out/"previews"/f'{m["id"]}.png'
        if m["_imgs"]:
            src = m["_imgs"][0]; img = img.with_suffix(src.suffix.lower()); shutil.copy(src, img)
        elif not img.exists():
            stl = next((f for f in m["_files"] if f.suffix.lower() == ".stl"), None)
            if not (stl and render_preview(stl, img)): problems.append(f'no preview for {m["title"]}')
        m["img"] = f"previews/{img.name}"
        if a.link_files:
            (out/"files"/m["id"]).mkdir(parents=True, exist_ok=True)
            m["dl"] = []
            for f in m["_files"]:
                shutil.copy(f, out/"files"/m["id"]/f.name); m["dl"].append(f'files/{m["id"]}/{f.name}')
        items.append({k: v for k, v in m.items() if not k.startswith("_")})
    import datetime
    page = (PAGE.replace("__TITLE__", html.escape(a.title)).replace("__DATA__", json.dumps(items))
            .replace("__DATE__", datetime.date.today().isoformat())
            .replace("__NFILES__", "Model files included." if a.link_files else "No model files are hosted here."))
    (out/"index.html").write_text(page)
    json.dump(items, open(out/"catalog.json", "w"), indent=1)
    print(f"{len(items)} models -> {out/'index.html'}")
    for p in problems: print("WARN:", p)

if __name__ == "__main__":
    main()

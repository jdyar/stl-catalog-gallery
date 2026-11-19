# stlgallery

`stlgallery.py` turns a folder of 3D-print models into a static, searchable gallery. The output is one self-contained `index.html` plus `previews/` and `catalog.json`. You can host it on GitHub Pages, Cloudflare Pages, or Netlify, or zip it and give it to the creator.

Model files are not copied into the site unless you pass `--link-files`, which is meant only for files the creator already gives away. By default, each card links to the creator's own post.

## Install

Python 3.10+. To auto-render preview images from STL files, install [OpenSCAD](https://openscad.org/) and make sure `openscad` is on your `PATH`. You can also point to a binary with the `OPENSCAD` environment variable.

## Usage

```bash
python make_sample_data.py          # optional: rebuild the synthetic sample catalog (needs OpenSCAD)
python stlgallery.py sample_catalog demo_site --title "Example Creator Archive"
# open demo_site/index.html in a browser
```

Catalog layout: any folder that contains `.stl`, `.3mf`, or `.obj` files is one model. An optional `meta.json` can set `title`, `tags`, `tier`, `release` (YYYY-MM), `patreon_url`, and `notes`. Missing fields are inferred from folder names. If a folder already has a jpg, png, or webp, that image is used as the preview; otherwise a preview is rendered from the first STL with OpenSCAD.

`demo_screenshot.png` shows the sample gallery: search, tier and month filters, sort, clickable tags, and auto-rendered previews.

## Sample data

`sample_catalog/` and `demo_site/` are synthetic. The eight models are simple OpenSCAD shapes made only for this demo. They are not anyone's real catalog.

## Notes

- Only run this on files a creator sends or explicitly authorizes.
- For a public gallery, get the creator's OK that preview images and titles may be public, or keep the gallery private.
- The generated page loads every model at once, so a very large archive may need pagination, which is not implemented yet.

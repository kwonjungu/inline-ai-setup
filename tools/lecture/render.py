import os
import subprocess, pathlib, sys, os, fitz, time
REPO = pathlib.Path(r"C:\Users\권준구\Desktop\inline-ai-setup")
HERE = pathlib.Path(__file__).parent
raw = HERE / (("raw_" + os.environ["LANGX"]) if os.environ.get("LANGX") else "raw").__add__(".pdf") if False else HERE / ((os.environ.get("LANGX") and "raw_" + os.environ["LANGX"] + ".pdf") or "raw.pdf")
url = (REPO / "lecture.html").as_uri() + "?print=1&code=1111" + (("&lang=" + os.environ["LANGX"]) if os.environ.get("LANGX") else "")
edge = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if raw.exists(): raw.unlink()
t = time.time()
subprocess.run([edge, "--headless=new", "--disable-gpu", "--no-first-run", "--user-data-dir=" + str(HERE / "edgeprof"),
                "--run-all-compositor-stages-before-draw", "--virtual-time-budget=30000",
                "--no-pdf-header-footer", "--print-to-pdf=" + str(raw), url], timeout=240)
print("render", round(time.time() - t, 1), "s", raw.exists())
d = fitz.open(raw); print("pages", d.page_count, "size", d[0].rect)
out = HERE / "png"; out.mkdir(exist_ok=True)
for f in out.glob("*.png"): f.unlink()
pages = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else range(1, d.page_count + 1)
for n in pages:
    d[n - 1].get_pixmap(dpi=72).save(out / ("p%03d.png" % n))

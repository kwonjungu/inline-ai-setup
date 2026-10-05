# -*- coding: utf-8 -*-
"""실습 파일·정답 예시의 미리보기 PNG를 assets/files/ 에 만든다.
   - hwp/hwpx: 한글 COM → PDF → PyMuPDF  (파일마다 별도 프로세스, 시간 제한)
   - xlsx: Excel COM → PDF → PyMuPDF (여백 자르기)
   - pptx: PowerPoint COM → PDF → PyMuPDF
   - pdf: PyMuPDF / txt·md: 글자를 그림으로 / png: 줄여서 / mp4: ffmpeg 첫 장면
   원본(materials)은 읽기만 하고, 사본을 임시 폴더에 복사해서 작업한다.
   사용: python tools/render_previews.py [키 ...]   (키를 주면 그것만 다시 만든다)"""
import os, sys, shutil, subprocess, tempfile, time, glob, textwrap
sys.stdout.reconfigure(encoding="utf-8")
import fitz
from PIL import Image, ImageDraw, ImageFont, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from site_manifest import FOLDERS, FILES

M = os.path.join(ROOT, "materials")
OUT = os.path.join(ROOT, "assets", "files")
os.makedirs(OUT, exist_ok=True)
TMP = os.path.join(tempfile.gettempdir(), "inline_site_render")
os.makedirs(TMP, exist_ok=True)
WIDTH = 1000
FONT = r"C:\Windows\Fonts\malgun.ttf"
FONTB = r"C:\Windows\Fonts\malgunbd.ttf"
ONLY = set(sys.argv[1:])


def procs(name):
    try:
        out = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {name}", "/FO", "CSV", "/NH"],
                             capture_output=True, text=True, encoding="cp949", errors="ignore").stdout
    except Exception:
        return set()
    return {int(l.split('","')[1]) for l in out.splitlines() if l.startswith('"') and '","' in l}


APP = {"hwp": "Hwp.exe", "hwpx": "Hwp.exe", "xlsx": "EXCEL.EXE", "pptx": "POWERPNT.EXE"}


def to_pdf(kind, src, timeout=150):
    """사본을 만들어 COM으로 PDF 저장. 새로 뜬 프로그램만 시간 초과 시 끈다."""
    ext = os.path.splitext(src)[1]
    work = os.path.join(TMP, f"src_{abs(hash(src)) % 10**8}{ext}")
    shutil.copy2(src, work)
    pdf = work[: -len(ext)] + ".pdf"
    if os.path.exists(pdf):
        os.remove(pdf)
    before = procs(APP[kind])
    try:
        r = subprocess.run([sys.executable, os.path.join(HERE, "render_child.py"), kind, work, pdf],
                           capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="ignore")
        if r.returncode != 0:
            print("   child err:", r.stderr.strip()[-300:])
    except subprocess.TimeoutExpired:
        print("   시간 초과 →", APP[kind], "새 프로세스 정리")
        for pid in procs(APP[kind]) - before:
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
    return pdf if os.path.exists(pdf) else None


def autocrop(img, pad=24):
    bg = Image.new(img.mode, img.size, (255, 255, 255))
    box = ImageChops.difference(img, bg).convert("L").point(lambda v: 255 if v > 12 else 0).getbbox()
    if not box:
        return img
    l, t, r, b = box
    return img.crop((max(0, l - pad), max(0, t - pad), min(img.width, r + pad), min(img.height, b + pad)))


def pdf_pages(pdf, key, pages, crop=False):
    doc = fitz.open(pdf)
    outs = []
    for i in range(min(pages, doc.page_count)):
        pg = doc[i]
        zoom = WIDTH / pg.rect.width
        pix = pg.get_pixmap(matrix=fitz.Matrix(zoom * (1.6 if crop else 1), zoom * (1.6 if crop else 1)), alpha=False)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        if crop:
            img = autocrop(img)
            if img.width > WIDTH:
                img = img.resize((WIDTH, round(img.height * WIDTH / img.width)), Image.LANCZOS)
        name = f"{key}.png" if i == 0 else f"{key}_{i+1}.png"
        img.save(os.path.join(OUT, name), optimize=True)
        outs.append(name)
    return outs


def text_png(path, key, max_lines=46, title=None):
    txt = open(path, encoding="utf-8-sig").read().replace("\r\n", "\n").replace("\t", "    ")
    f = ImageFont.truetype(FONT, 19)
    fb = ImageFont.truetype(FONTB, 21)
    lines = []
    for raw in txt.split("\n"):
        if not raw.strip():
            lines.append(""); continue
        cur = ""
        for ch in raw:
            if f.getlength(cur + ch) > WIDTH - 80:
                lines.append(cur); cur = "  " + ch
            else:
                cur += ch
        lines.append(cur)
    more = len(lines) > max_lines
    lines = lines[:max_lines]
    head = 56
    H = head + 30 * len(lines) + (50 if more else 30)
    img = Image.new("RGB", (WIDTH, H), "white")
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, WIDTH, head - 12), fill=(245, 245, 245))
    d.text((40, 10), title or os.path.basename(path), font=fb, fill=(17, 17, 17))
    y = head
    for l in lines:
        d.text((40, y), l, font=f, fill=(57, 57, 59)); y += 30
    if more:
        d.text((40, y + 6), "… (이어지는 내용은 파일에서)", font=f, fill=(112, 112, 114))
    img.save(os.path.join(OUT, f"{key}.png"), optimize=True)
    return [f"{key}.png"]


def photos_grid(folder, key):
    exts = (".jpg", ".jpeg", ".png")
    files = sorted(p for p in os.listdir(folder) if p.lower().endswith(exts))
    cols, cell, cap = 6, 156, 34
    rows = (len(files) + cols - 1) // cols
    W = cols * (cell + 10) + 10
    img = Image.new("RGB", (W, rows * (cell + cap + 10) + 10), (245, 245, 245))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(FONT, 13)
    for i, name in enumerate(files):
        x = 10 + (i % cols) * (cell + 10); y = 10 + (i // cols) * (cell + cap + 10)
        p = os.path.join(folder, name)
        d.rectangle((x, y, x + cell, y + cell), fill="white", outline=(202, 202, 203))
        try:
            if os.path.getsize(p) == 0:
                raise ValueError
            im = Image.open(p).convert("RGB"); im.thumbnail((cell - 8, cell - 8))
            img.paste(im, (x + (cell - im.width) // 2, y + (cell - im.height) // 2))
        except Exception:
            d.text((x + cell // 2, y + cell // 2), "열리지 않음\n(0바이트)", font=f, fill=(158, 158, 160), anchor="mm", align="center")
        label = name if f.getlength(name) <= cell else name[:14] + "…"
        d.text((x + cell // 2, y + cell + 6), label, font=f, fill=(57, 57, 59), anchor="ma")
    img.save(os.path.join(OUT, f"{key}.png"), optimize=True)
    return [f"{key}.png"]


def folder_list(folder, key):
    files = sorted(os.listdir(folder))
    f = ImageFont.truetype(FONT, 15)
    fb = ImageFont.truetype(FONTB, 18)
    half = (len(files) + 1) // 2
    colw = WIDTH // 2
    H = 60 + half * 24 + 20
    img = Image.new("RGB", (WIDTH, H), "white")
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, WIDTH, 44), fill=(245, 245, 245))
    d.text((20, 10), f"다운로드_흉내  ·  파일 {len(files)}개", font=fb, fill=(17, 17, 17))
    for i, name in enumerate(files):
        x = 20 + (i // half) * colw; y = 58 + (i % half) * 24
        ext = os.path.splitext(name)[1].lower().strip(".")[:4] or "?"
        d.rounded_rectangle((x, y + 2, x + 40, y + 20), 6, fill=(17, 17, 17))
        d.text((x + 20, y + 11), ext, font=ImageFont.truetype(FONT, 11), fill="white", anchor="mm")
        label = name
        while f.getlength(label) > colw - 70 and len(label) > 4:
            label = label[:-2]
        if label != name:
            label += "…"
        d.text((x + 50, y + 1), label, font=f, fill=(57, 57, 59))
    img.save(os.path.join(OUT, f"{key}.png"), optimize=True)
    return [f"{key}.png"]


def main():
    done = {}
    for no, items in FILES.items():
        base = os.path.join(M, FOLDERS[no])
        for role, rel, key, pages, label in items:
            if not key or key in done or (ONLY and key not in ONLY):
                continue
            src = os.path.join(base, rel.replace("/", os.sep))
            ext = os.path.splitext(src)[1].lower()
            t0 = time.time()
            outs = []
            try:
                if key == "01_folder":
                    outs = folder_list(src, key)
                elif key == "01_photos":
                    outs = photos_grid(src, key)
                elif ext in (".txt", ".md"):
                    outs = text_png(src, key, title=os.path.basename(src).replace("(권준구 강의안 스타일)", "(강의안 스타일)"))
                elif ext == ".png":
                    im = Image.open(src).convert("RGB")
                    im.thumbnail((WIDTH, WIDTH))
                    im.save(os.path.join(OUT, f"{key}.png"), optimize=True); outs = [f"{key}.png"]
                elif ext == ".mp4":
                    o = os.path.join(OUT, f"{key}.png")
                    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "1", "-i", src, "-frames:v", "1",
                                    "-vf", f"scale={WIDTH}:-2", o], check=True)
                    outs = [f"{key}.png"]
                elif ext == ".pdf":
                    outs = pdf_pages(src, key, pages)
                else:
                    kind = ext.strip(".")
                    pdf = to_pdf(kind, src)
                    if pdf:
                        outs = pdf_pages(pdf, key, pages, crop=(kind == "xlsx"))
            except Exception as e:
                print("   오류:", e)
            done[key] = outs
            print(f"{key:18s} {('OK ' + ','.join(outs)) if outs else '실패'}  ({time.time()-t0:.0f}s)  {label}")
    bad = [k for k, v in done.items() if not v]
    print("실패:", bad if bad else "없음")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""사이트 점검: (1) index.html 의 모든 로컬 링크·이미지 파일이 있는지 (2) Edge 헤드리스 캡처.
   사용: python tools/site_check.py [캡처폴더]"""
import os, re, sys, subprocess
from urllib.parse import unquote, urlsplit
sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "..", "site_check")
os.makedirs(OUT, exist_ok=True)

html = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
refs = re.findall(r'(?:href|src|data-src)="([^"]+)"', html)
bad, n = [], 0
for r in refs:
    if r.startswith(("http", "#", "mailto:", "data:")):
        continue
    p = unquote(urlsplit(r).path)
    n += 1
    if not os.path.exists(os.path.join(ROOT, p)):
        bad.append(r)
ids = set(re.findall(r'id="([^"]+)"', html))
anchors = [a for a in re.findall(r'href="#([^"]+)"', html) if a not in ids]
print(f"로컬 링크·이미지 {n}개 확인 · 없는 파일 {len(bad)}개 · 깨진 #앵커 {len(anchors)}개")
for b in bad + anchors:
    print("  ✗", b)

# Edge(헤드리스)를 Playwright로 띄워 캡처 — 창 너비 390px도 정확히 맞추려고 Playwright 사용
from playwright.sync_api import sync_playwright
base = "file:///" + os.path.join(ROOT, "index.html").replace("\\", "/")
shots = [("home_1280.png", "", 1280, False), ("solo02_1280.png", "?solo=02", 1280, True),
         ("solo00_1280.png", "?solo=00", 1280, True), ("solo09_1280.png", "?solo=09", 1280, True),
         ("home_390.png", "", 390, True), ("solo05_390.png", "?solo=05", 390, True)]
with sync_playwright() as pw:
    br = pw.chromium.launch(channel="msedge", headless=True)
    for name, q, w, full in shots:
        pg = br.new_page(viewport={"width": w, "height": 900})
        pg.goto(base + q, wait_until="domcontentloaded"); pg.wait_for_timeout(1500)
        pg.evaluate("document.querySelectorAll('img[loading=lazy]').forEach(i=>i.loading='eager')"); pg.wait_for_timeout(1500)
        sw = pg.evaluate("document.documentElement.scrollWidth")
        pg.screenshot(path=os.path.join(OUT, name), full_page=full)
        print(name, "OK", "가로 넘침!" if sw > w else "", sw)
    # 복사 버튼: 클릭 → 버튼 글자가 '복사됨'으로 바뀌는지
    ctx = br.new_context(permissions=["clipboard-read", "clipboard-write"])
    pg = ctx.new_page(); pg.goto(base + "?solo=02", wait_until="domcontentloaded"); pg.wait_for_timeout(800)
    b = pg.locator(".solo-keep .prompt-row .prompt-copy").first; b.click(); pg.wait_for_timeout(200)
    print("복사 버튼:", b.inner_text(), "/ 이미지 깨짐:",
          pg.evaluate("[...document.images].filter(i=>i.complete&&i.naturalWidth===0&&!i.src.startsWith('https')).length"))
    br.close()

import re, json, pathlib, sys, importlib.util
from bs4 import BeautifulSoup
REPO = pathlib.Path(r"C:\Users\권준구\Desktop\inline-ai-setup"); HERE = pathlib.Path(__file__).parent
txt = (REPO / "deck" / "원고.md").read_text(encoding="utf-8")
S = {}
for sid, body in re.findall(r"^### (S\d{3}) (.*?)(?=^### S|\Z)", txt, re.S | re.M):
    scr = re.search(r"^- 화면 글자: (.*)$", body, re.M).group(1)
    vis = (re.search(r"^- 시각 자료: (.*)$", body, re.M) or [None, ""])[1] if re.search(r"^- 시각 자료: (.*)$", body, re.M) else ""
    S[sid] = (scr, vis)
norm = lambda t: re.sub(r"[\s/]", "", t)
soup = BeautifulSoup((REPO / "lecture.html").read_text(encoding="utf-8"), "html.parser")
frames = soup.select("div.frame")
bad_ms, bad_vs, partial, chars, cross = [], [], [], [], []
ALLSCR = "|".join(norm(v[0]) for v in S.values())
allsrc = []
for fr in frames:
    i = int(fr["data-i"]); src = fr["data-src"].split(","); allsrc += src
    scr = "".join(norm(S[s][0]) for s in src); vis = norm(" ".join(S[s][1] for s in src))
    sl = fr.select_one("section.slide")
    shown = ""
    for el in sl.select(".ms"):
        t = norm(el.get_text())
        shown += t
        if t not in scr:
            if t in ALLSCR: cross.append((i, el.get_text()))
            else: bad_ms.append((i, el.get_text()))
    for el in sl.select(".vs"):
        if norm(el.get_text()) not in vis and norm(el.get_text()) not in norm(txt): bad_vs.append((i, el.get_text()))
    # 원고 화면 글자 조각 중 강의안에 안 보이는 것
    for s in src:
        for seg in [x.strip() for x in S[s][0].split(" / ")]:
            for piece in re.split(r" · |[①②③④⑤⑥⑦⑧⑨⑩]", seg):
                if norm(piece) and norm(piece) not in norm(sl.get_text()):
                    partial.append((i, s, piece))
    chars.append((i, len(norm(sl.get_text()))))
print("강의안 장 수:", len(frames), "| 원고 장 수:", len(S), "| 원고 장 모두 대응:", sorted(allsrc) == sorted(S) and len(allsrc) == len(S))
print("(a) 원고 화면 글자 표시 요소(.ms):", len(soup.select(".ms")), "개 / 원고와 다른 것:", len(bad_ms))
for b in bad_ms: print("   MS-DIFF", b)
print("    다른 원고 장의 화면 글자를 요약 표에 인용:", len(cross), "개 (예:", cross[:3], ")")
print("    시각 자료 낱말(.vs) 원고에 없는 것:", len(bad_vs))
for b in bad_vs: print("   VS-DIFF", b)
print("    합친 장에서 낱말로 줄인 원고 조각(화면에 안 보임):", len(partial))
for p in partial: print("   OMIT", p)
# (b) 이미지
imgs = [im["src"] for im in soup.select("section.slide img")]
local = [s for s in imgs if not s.startswith("http")]
missing = [s for s in local if not (REPO / s).exists()]
print("(b) 이미지 참조:", len(imgs), "(로컬", len(local), ") / 없는 파일:", len(missing), missing)
if len(sys.argv) > 1:
    import fitz
    d = fitz.open(sys.argv[1]); print("(c) PDF 쪽수:", d.page_count, "= HTML 장 수", len(frames), "->", d.page_count == len(frames))

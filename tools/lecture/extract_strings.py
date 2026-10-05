import json, re, pathlib
from bs4 import BeautifulSoup, NavigableString, Comment
REPO = pathlib.Path(r"C:\Users\권준구\Desktop\inline-ai-setup"); HERE = pathlib.Path(__file__).parent
soup = BeautifulSoup((REPO / "lecture.html").read_text(encoding="utf-8"), "html.parser")
seen = {}
def add(t):
    t = re.sub(r"\s+", " ", t).strip()
    if not t or not re.search(r"[가-힣]", t): return
    seen.setdefault(t, None)
for fr in soup.select("div.frame"):
    add(fr["data-title"]); add(fr["data-sec"])
    for s in fr.select("section.slide")[0].descendants:
        if isinstance(s, NavigableString) and not isinstance(s, Comment):
            add(str(s))
    for el in fr.select("section.slide [alt]"): add(el["alt"])
keys = list(seen)
(HERE / "strings.json").write_text(json.dumps(keys, ensure_ascii=False, indent=0), encoding="utf-8")
print(len(keys))

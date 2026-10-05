# -*- coding: utf-8 -*-
"""deck/원고.md 의 '화면 글자' 글자 수 검사 (공백·/ 제외). 60자 초과 장을 원고_글자수검사.txt 로 저장."""
import os, re
HERE = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(HERE, "원고.md")
out = os.path.join(HERE, "원고_글자수검사.txt")
LIMIT, TARGET = 60, 40
rows, cur = [], None
for line in open(src, encoding="utf-8"):
    m = re.match(r"### (S\d{3}) \[(.+?)\] (.+?) · (\d+)", line)
    if m:
        cur = m.group(1); continue
    if cur and line.startswith("- 화면 글자:"):
        text = line.split(":", 1)[1].strip()
        rows.append((cur, len(re.sub(r"[\s/]", "", text)), text)); cur = None
over = [r for r in rows if r[1] > LIMIT]
mid = [r for r in rows if TARGET + 5 < r[1] <= LIMIT]
lines = ["원고 화면 글자 수 검사 (공백·/ 제외, 최대 %d자, 권장 %d자 안팎)" % (LIMIT, TARGET),
         "검사한 장: %d / 60자 초과: %d건 / 평균: %.1f자 / 최대: %d자" % (len(rows), len(over), sum(r[1] for r in rows) / len(rows), max(r[1] for r in rows)),
         "", "[60자 초과]"] + (["%s  %d자  %s" % r for r in over] or ["없음 (0건)"]) + \
        ["", "[46~60자 — 허용 범위지만 긴 장]"] + (["%s  %d자  %s" % r for r in mid] or ["없음"]) + \
        ["", "[전체]"] + ["%s  %d자  %s" % r for r in rows]
open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("\n".join(lines[:2])); print("over:", [r[0] for r in over])

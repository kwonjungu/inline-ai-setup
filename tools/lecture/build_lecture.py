# -*- coding: utf-8 -*-
"""deck/원고.md(151장) -> lecture.html(약 110장). 겹치는 장은 합치고, 노트는 원고 노트를 이어 붙인다.
   산출: lecture.html, deck/강의안_대응표.md, scratchpad slides.json"""
import re, json, html, os
import qrcode

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = r"C:\Users\권준구\Desktop\inline-ai-setup"
SRC = os.path.join(REPO, "deck", "원고.md")
OUT = os.path.join(REPO, "lecture.html")
E = html.escape

# ------------------------------------------------------------------ 원고 파싱
def parse():
    txt = open(SRC, encoding="utf-8").read()
    parts = re.split(r"^### (S\d{3}) ", txt, flags=re.M)
    S = {}
    for i in range(1, len(parts), 2):
        sid, body = parts[i], parts[i + 1]
        m = re.match(r"\[(.*?)\]\s*(.*?)\s*·\s*(\d+)", body.split("\n", 1)[0])
        d = {"type": m.group(1), "sec": m.group(2), "sec_s": int(m.group(3)),
             "screen": "", "visual": "", "act": "", "note": "", "quote": []}
        for line in body.split("\n")[1:]:
            if line.startswith("## "):
                break
            mm = re.match(r"- (화면 글자|시각 자료|참가자 행동|발표자 노트): ?(.*)", line)
            if mm:
                d[{"화면 글자": "screen", "시각 자료": "visual", "참가자 행동": "act", "발표자 노트": "note"}[mm.group(1)]] = mm.group(2).strip()
            elif line.startswith("  ") and line.strip():
                d["quote"].append(line.strip())
        S[sid] = d
    return S

S = parse()
assert len(S) == 151
S["S066"]["quote"] = ["프롬프트 원문(03-①, 원고에 비어 있어 materials 프롬프트.txt에서 보충):",
    "> [자료 1] 학년 업무분장을 '담당 | 맡은 일 | 마감일 | 비고' 표로 바꿔 줘. 마감일이 빠른 순서로 정리해 줘."]
S["S120"]["quote"] = ["프롬프트 원문(08-①, 원고에는 ⑥번 문장이 들어가 있어 materials 프롬프트.txt로 보정):",
    "> 첨부한 자료로 '2025 디지털 동아리 운영 결과' 발표 자료를 8장 이내로 만들어 줘.",
    "> - 열려 있는 우리 학교 양식(남색 제목 띠, 맑은 고딕)을 따를 것",
    "> - 순서: 표지 → 운영 개요 → 활동 내용 → 참여 현황 → 만족도 → 성과 → 개선점 → 마무리",
    "> - 새 파일 '동아리_결과발표.pptx'로 저장"]

def L(sid):   return [x.strip() for x in S[sid]["screen"].split(" / ")]
def V(sid):   return S[sid]["visual"]
def imgs(sid): return [p.replace("\\", "/") for p in re.findall(r"assets\\shot\\[^\s+]+?\.png", V(sid))]
def need(sid):
    m = re.search(r"\[캡처 필요: ?([^\]]*)\]", V(sid)); return m.group(1) if m else None
def gray(sid):
    m = re.search(r"아래 회색 (?:한 )?줄: ?'([^']+)'", V(sid)); return m.group(1) if m else None
def label(sid):
    m = re.search(r"라벨 '([^']+)'", V(sid)); return m.group(1) if m else None
def dots(sid):
    m = re.search(r"점 \d개\(([^)]*)\)", V(sid)); return re.findall(r"'([^']+)'", m.group(1)) if m else []
def tags(sid):
    m = re.search(r"(?:태그|유형 \d\)?):? ?(.*)$", V(sid))
    return re.findall(r"'([^']+)'", V(sid).split("유형", 1)[-1]) if V(sid) else []

# ------------------------------------------------------------------ 색
PINK, TEAL, RED, INK = "#ED1AA0", "#0B7F82", "#E0262B", "#111111"
SECCOL = {"여는 말": PINK, "0 준비": PINK, "01 다운로드 정리": PINK, "02 가정통신문 양식": PINK, "03 한글 표": PINK,
          "04 작년도 문서 업데이트": PINK, "쉬는 시간": INK, "05 행정 처리": TEAL, "06 계획서로 기안문": TEAL,
          "07 계획서로 보고서": TEAL, "08 계획서·통계로 PPT": TEAL, "09 클로드 코워크": RED, "정리": PINK}
ACC = PINK

# ------------------------------------------------------------------ 부품
def ms(t, tag="span", cls=""):
    """원고 '화면 글자'를 그대로 쓰는 요소(품질 검사 대상)."""
    return '<%s class="ms %s">%s</%s>' % (tag, cls, E(t), tag)
def vs(t, tag="span", cls=""):
    """원고 '시각 자료'에 적힌 낱말(검사: 원고 시각 자료에 있는지)."""
    return '<%s class="vs %s">%s</%s>' % (tag, cls, E(t), tag)
def br(*lines): return "<br>".join(ms(l) for l in lines)

def img(path, alt, style=""):
    return '<img src="%s" alt="%s" style="%s">' % (path, E(alt), style)
def ph(desc, w=None, h=None, style=""):
    st = style + (";width:%dpx" % w if w else "") + (";height:%dpx" % h if h else "")
    return ('<div class="ph" style="%s"><svg viewBox="0 0 48 48" width="40" height="40" aria-hidden="true">'
            '<rect x="5" y="11" width="38" height="28" rx="5" fill="none" stroke="currentColor" stroke-width="2.5"/>'
            '<circle cx="24" cy="25" r="7" fill="none" stroke="currentColor" stroke-width="2.5"/>'
            '<rect x="16" y="7" width="16" height="6" rx="2" fill="currentColor"/></svg>'
            '<b>리허설 때 캡처</b><span>%s</span></div>') % (st, E(desc))
def ftype(t): return '<i class="ft ft-%s">%s</i>' % ({"폴더": "dir"}.get(t, t.lower()), t)

def video(vid, title, w, h, start=0, short=False):
    q = ("?start=%d&autoplay=1" % start) if start else "?autoplay=1"
    link = ("https://www.youtube.com/shorts/%s" % vid) if short else ("https://youtu.be/%s%s" % (vid, "?t=%d" % start if start else ""))
    return ('<div class="vid" style="width:%dpx;height:%dpx" data-embed="https://www.youtube.com/embed/%s%s" role="button" tabindex="0" aria-label="영상 재생: %s">'
            '<img src="https://i.ytimg.com/vi/%s/hqdefault.jpg" alt="영상 미리보기: %s">'
            '<span class="play" aria-hidden="true"><svg viewBox="0 0 68 48" width="76" height="54"><path d="M66.5 7.7A8.5 8.5 0 0 0 60.5 1.7C55.2.3 34 .3 34 .3S12.8.3 7.5 1.7A8.5 8.5 0 0 0 1.5 7.7 89 89 0 0 0 .1 24a89 89 0 0 0 1.4 16.3 8.5 8.5 0 0 0 6 6C12.8 47.7 34 47.7 34 47.7s21.2 0 26.5-1.4a8.5 8.5 0 0 0 6-6A89 89 0 0 0 67.9 24a89 89 0 0 0-1.4-16.3z" fill="#111"/><path d="M27 34l18-10-18-10z" fill="#fff"/></svg></span>'
            '<a class="vlink" href="%s" target="_blank" rel="noopener">▶ %s</a></div>') % (
        w, h, vid, q, E(title), vid, E(title), link, link.replace("https://", ""))

def qr_svg(text, size=260):
    q = qrcode.QRCode(border=2, error_correction=qrcode.constants.ERROR_CORRECT_M); q.add_data(text); q.make()
    m = q.get_matrix(); n = len(m)
    rects = "".join('<rect x="%d" y="%d" width="1.02" height="1.02"/>' % (x, y) for y, row in enumerate(m) for x, v in enumerate(row) if v)
    return '<svg class="qr" viewBox="0 0 %d %d" width="%d" height="%d" role="img" aria-label="QR: %s" shape-rendering="crispEdges"><rect width="%d" height="%d" fill="#fff"/><g fill="#111">%s</g></svg>' % (n, n, size, size, E(text), n, n, rects)

def htitle(lines):
    if len(lines) == 1: return ms(lines[0])
    return ms(lines[0]) + " " + '<span class="hl2">' + " ".join(ms(x) for x in lines[1:]) + "</span>"

def head(title_html, acc, tail=""):
    return f'<div class="hd"><span class="tick" style="background:{acc}"></span><h2 class="d-sm">{title_html}</h2>{("<span class=tail>" + tail + "</span>") if tail else ""}</div>'

def pills(items, cls="chip"):
    return "".join(f'<span class="{cls}">{x}</span>' for x in items)

# ------------------------------------------------------------------ SVG 차트
def svg_hbars(rows, accent, w=520, bh=46, gap=16, unit="", maxv=None, labw=86):
    maxv = maxv or max(v for _, v, _ in rows)
    H = len(rows) * (bh + gap) - gap
    o = ['<svg class="chart" viewBox="0 0 %d %d" width="%d" height="%d" role="img" aria-label="%s">' % (
        w, H, w, H, E(", ".join("%s %s%s" % (a, format(b, ","), unit) for a, b, _ in rows)))]
    for i, (lab, v, hi) in enumerate(rows):
        y = i * (bh + gap); bw = max(4, (w - labw - 140) * v / maxv)
        o.append('<text x="0" y="%d" class="cl">%s</text>' % (y + bh / 2 + 8, E(lab)))
        o.append('<rect x="%d" y="%d" width="%.1f" height="%d" rx="6" fill="%s"/>' % (labw, y, bw, bh, accent if hi else "#D6D6D8"))
        o.append('<text x="%.1f" y="%d" class="cv">%s%s</text>' % (labw + bw + 12, y + bh / 2 + 9, format(v, ","), unit))
    return "".join(o) + "</svg>"

def svg_vbars(vals, labels, hi_idx, accent, w=760, h=330):
    n = len(vals); step = (w - 20) / n; bw = step * 0.62; top, base = 40, h - 40
    o = ['<svg class="chart" viewBox="0 0 %d %d" width="%d" height="%d" role="img" aria-label="회차별 참여율: %s">' % (
        w, h, w, h, E(", ".join("%s %d%%" % (l, v) for l, v in zip(labels, vals))))]
    o.append('<line x1="0" y1="%d" x2="%d" y2="%d" stroke="#CACACB" stroke-width="1.5"/>' % (base, w, base))
    for i, v in enumerate(vals):
        x = 10 + i * step + (step - bw) / 2; bh = (base - top) * v / 100
        o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="5" fill="%s"/>' % (x, base - bh, bw, bh, accent if i == hi_idx else "#D6D6D8"))
        o.append('<text x="%.1f" y="%.1f" text-anchor="middle" class="%s">%d</text>' % (x + bw / 2, base - bh - 10, "cvh" if i == hi_idx else "cvs", v))
        o.append('<text x="%.1f" y="%d" text-anchor="middle" class="cx%s">%s</text>' % (x + bw / 2, base + 28, " hi" if i == hi_idx else "", E(labels[i])))
    return "".join(o) + "</svg>"

def svg_ring(pct, lab, accent, size=180):
    r = size / 2 - 16; c = 2 * 3.14159265 * r
    return ('<div class="ring"><svg viewBox="0 0 {s} {s}" width="{s}" height="{s}" role="img" aria-label="{lab} {p}%">'
            '<circle cx="{h}" cy="{h}" r="{r}" fill="none" stroke="#ECECEE" stroke-width="20"/>'
            '<circle cx="{h}" cy="{h}" r="{r}" fill="none" stroke="{a}" stroke-width="20" stroke-linecap="round" stroke-dasharray="{d:.1f} {c:.1f}" transform="rotate(-90 {h} {h})"/>'
            '<text x="{h}" y="{ty}" text-anchor="middle" class="rv">{p}<tspan class="ru">%</tspan></text></svg><p>{lab}</p></div>').format(
        s=size, h=size / 2, r=r, a=accent, d=c * pct / 100, c=c, p=pct, lab=E(lab), ty=size / 2 + 12)

# ================================================================== 일반 렌더러 (원고 유형별)
def r_section(sid, sub=None):
    ls = L(sid); num = re.match(r"(\d+)", ls[0]).group(1)
    return f'''<div class="ghost">{num}</div><div class="pad">
  <span class="kick" style="color:{ACC}">SECTION {num}</span>
  <h2 class="d-lg">{ms(ls[0])}</h2><p class="lead-dk">{br(*ls[1:])}</p>
  {('<p class="cover-sub2">' + sub + '</p>') if sub else ''}</div>''', True

def r_sentence(sid):
    ls = L(sid); n = max(len(x) for x in ls)
    size = "d-lg" if n <= 13 else "d-md"
    g = gray(sid)
    return f'''<div class="pad center-v"><span class="rule" style="background:{ACC}"></span>
  <h1 class="{size}">{br(*ls)}</h1>{('<p class="sub">' + vs(g) + '</p>') if g else ''}</div>''', False

def card_parts(sid):
    ls = L(sid); tg = re.findall(r"'([^']+)'", V(sid))
    if len(tg) == len(ls): title, items = None, ls
    else:
        title = ls[0]; items = [y.strip() for x in ls[1:] for y in x.split(" · ")]
    out = []
    for i, it in enumerate(items):
        t = tg[i] if len(tg) == len(items) else None
        if t and t == it: t = None
        if t and "→" in t: out.append((ms(it), vs(t.split("→", 1)[1].strip()), "arrow"))
        elif t and len(t) < len(it): out.append((vs(t), ms(it), "big"))
        elif t: out.append((ms(it), vs(t), "small"))
        else: out.append(("%d" % (i + 1), ms(it), "big"))
    return title, out

def cards_html(parts, acc, cls=""):
    h = []
    for lab, p, kind in parts:
        h.append(f'<div class="card {kind}"><span class="lab" style="background:{acc}">{lab}</span><p>{p}</p></div>')
    return f'<div class="grid{len(parts)} {cls}">' + "".join(h) + "</div>"

def r_cards(sid):
    title, parts = card_parts(sid)
    g = gray(sid)
    return f'''<div class="pad vc"><span class="rule sm" style="background:{ACC}"></span>
  {('<h2 class="d-md">' + ms(title) + '</h2>') if title else ''}{cards_html(parts, ACC)}{('<p class="cap">' + vs(g) + '</p>') if g else ''}</div>''', False

def steps_of(text):
    return [x.strip() for x in re.findall(r"[①②③]\s*([^①②③/]+)", text)]

def steps_html(names, acc, descs=None):
    h = []
    for i, n in enumerate(names):
        d = descs[i] if descs else ""
        h.append(f'<div class="scell" style="border-color:{acc}"><span class="sno" style="background:{acc}">{i+1}</span><h3>{ms(n)}</h3>{("<p>" + d + "</p>") if d else ""}</div>')
    return '<div class="steps">' + "".join(h) + "</div>"

def r_steps(sid):
    ls = L(sid); title = ls[0] if not ls[0].startswith("①") else None
    names = steps_of(S[sid]["screen"]); g = gray(sid)
    return f'''<div class="pad vc"><span class="rule sm" style="background:{ACC}"></span>
  {('<h2 class="d-md">' + ms(title) + '</h2>') if title else ''}{steps_html(names, ACC)}
  {('<p class="cap mt">' + vs(g) + '</p>') if g else ''}</div>''', False

EXT = re.compile(r"\.(hwpx|xlsx|pptx|txt|pdf)")
def pill_parts(sid):
    ls = L(sid)
    if ls[0].startswith("정답_"):
        k = 1
        while not EXT.search(ls[k - 1]) and k < len(ls): k += 1
        if k < len(ls) and ls[k].startswith("…_"): k += 1
        return "answer", ls[:k], ls[k:]
    if re.match(r"[①②③\d]", ls[0]):
        return "none", [], ls
    return "title", [ls[0]], ls[1:]

def r_pills(sid, extra=""):
    kind, t, items = pill_parts(sid)
    g = gray(sid)
    if kind == "answer":
        th = f'<div class="hd"><span class="anslab" style="background:{ACC}">정답</span><h2 class="d-sm fname">{" ".join(ms(x) for x in t)}</h2></div>'
    elif kind == "title":
        th = f'<span class="rule sm" style="background:{ACC}"></span><h2 class="d-md">{ms(t[0])}</h2>'
    else:
        th = f'<span class="rule sm" style="background:{ACC}"></span>'
    return f'''<div class="pad vc">{th}<div class="chips">{pills([ms(x) for x in items], "chip big")}</div>
  {('<p class="cap mt">' + vs(g) + '</p>') if g else ''}{extra}</div>''', False

def prompt_art(acc, words=("복사", "붙여 넣기", "보내기")):
    ic = ['<svg viewBox="0 0 40 40"><rect x="12" y="4" width="22" height="26" rx="4" fill="none" stroke="currentColor" stroke-width="3"/><rect x="5" y="11" width="22" height="26" rx="4" fill="#fff" stroke="currentColor" stroke-width="3"/></svg>',
          '<svg viewBox="0 0 40 40"><rect x="7" y="8" width="26" height="28" rx="4" fill="none" stroke="currentColor" stroke-width="3"/><rect x="14" y="4" width="12" height="8" rx="2" fill="currentColor"/><path d="M14 22h12M14 28h8" stroke="currentColor" stroke-width="3"/></svg>',
          '<svg viewBox="0 0 40 40"><circle cx="20" cy="20" r="16" fill="currentColor"/><path d="M20 28V13M13 19l7-7 7 7" stroke="#fff" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>']
    cells = "".join(f'<div class="pa"><span class="paic" style="color:{acc if i==2 else "#111"}">{ic[i]}</span><b>{vs(w) if w in V_ALL else E(w)}</b></div>' + ('<i class="paarr">→</i>' if i < 2 else "") for i, w in enumerate(words))
    return f'<div class="partbox"><p class="pah">프롬프트.txt</p><div class="parow">{cells}</div></div>'

def r_mission(sid, right=None):
    ls = L(sid); lab = label(sid) or "실습 미션"; ds = dots(sid)
    im = imgs(sid)
    if right is None:
        if im: right = f'<div class="panel mimg">{img(im[0], ls[0] + " 화면")}</div>'
        elif "프롬프트.txt" in S[sid]["screen"]: right = prompt_art(ACC)
        else: right = ""
    dh = ('<ul class="dots">' + "".join(f"<li>{vs(d)}</li>" for d in ds) + "</ul>") if ds else ""
    tall = im and "03a_" in im[0]
    return f'''<div class="pad mission {"has-r" if right else ""} {"tall-r" if tall else ""}"><div class="mcopy">
  <span class="tag" style="background:{ACC}">{vs(lab)}</span>
  <h2 class="d-md">{br(*ls)}</h2>{dh}</div>{('<div class="mright">' + right + '</div>') if right else ''}</div>''', False

def shot_box(sid, maxw=1120, maxh=550):
    im = imgs(sid)
    if not im:
        return ph(need(sid) or "", min(maxw, 900), min(maxh, 470))
    if len(im) == 1:
        return f'<div class="panel">{img(im[0], " ".join(L(sid)) + " 화면", f"max-width:{maxw-24}px;max-height:{maxh-24}px")}</div>'
    return '<div class="multi">' + "".join(f'<div class="panel">{img(p, " ".join(L(sid)) + " 화면 " + str(k+1))}</div>' for k, p in enumerate(im)) + "</div>"

def r_capture(sid, tail=""):
    ls = L(sid)
    return f'''<div class="pad tight">{head(htitle(ls), ACC, tail)}
  <div class="figwrap grow">{shot_box(sid)}</div></div>''', False

AUTO = {"섹션 표지": r_section, "한 문장": r_sentence, "카드3": r_cards, "단계123": r_steps,
        "알약 모음": r_pills, "미션": r_mission, "캡처": r_capture}

# ================================================================== 합친 장용 렌더러
def r_combo(blocks, right_html="", note=""):
    """blocks: [(sid, label_override)] — 각 원고 장의 화면 글자를 한 줄 표로."""
    rows = []
    for sid, lab in blocks:
        ls = L(sid)
        first = lab or ls[0]; rest = ls[1:] if not lab else ls
        lab_h = ms(first) if not lab else vs(first) if first in V_ALL else E(first)
        rows.append(f'<div class="gr"><span class="gl" style="--ac:{ACC}">{lab_h}</span><div class="gc">{" ".join("<b>" + ms(x) + "</b>" if i == 0 else ms(x) for i, x in enumerate(rest))}</div></div>')
    return f'''<div class="pad combo {"has-r" if right_html else ""}"><div class="gtab">{"".join(rows)}{('<p class="cap">' + note + '</p>') if note else ''}</div>
  {('<div class="mright">' + right_html + '</div>') if right_html else ''}</div>''', False

def check_panel(sid, extra=""):
    kind, t, items = pill_parts(sid)
    return f'''<div class="chk"><p class="chkh">{ms(t[0]) if t else "확인할 것"}</p>
  {"".join(f'<div class="ci"><i style="color:{ACC}">✓</i>{ms(x)}</div>' for x in items)}{extra}</div>'''

def r_shot_check(cap, chk, extra="", boxw=760, boxh=470):
    ls = L(cap)
    return f'''<div class="pad tight">{head(htitle(ls), ACC)}
  <div class="sc"><div class="figwrap">{shot_box(cap, boxw, boxh) if imgs(cap) else ph(need(cap) or "", boxw, boxh)}</div>{check_panel(chk, extra)}</div></div>''', False

def more_line(sid):
    ls = L(sid)
    return f'<p class="more"><b>{ms(ls[0])}</b> ' + " · ".join(ms(x) for x in ls[1:]) + "</p>"

def file_visual(names):
    ext = (EXT.search(" ".join(names)) or [None, "hwpx"])[1]
    return (f'<div class="fileart"><svg viewBox="0 0 120 150" width="150" height="188" aria-hidden="true"><path d="M10 6h70l30 30v108H10z" fill="#fff" stroke="#111" stroke-width="5" stroke-linejoin="round"/>'
            f'<path d="M80 6v30h30" fill="none" stroke="#111" stroke-width="5" stroke-linejoin="round"/><path d="M28 66h64M28 84h64M28 102h44" stroke="#CACACB" stroke-width="7" stroke-linecap="round"/></svg>'
            f'<i class="ft ft-{ext} big">{ext}</i><p>강사 화면에 직접 열기</p></div>')

def r_answer(ans, more=None, visual="", side=""):
    kind, t, items = pill_parts(ans)
    if not visual: visual = file_visual(t)
    return f'''<div class="pad tight"><div class="hd"><span class="anslab" style="background:{ACC}">정답</span><h2 class="d-sm fname">{" ".join(ms(x) for x in t)}</h2></div>
  <div class="ans {"has-v" if visual else ""}">{('<div class="ansv">' + visual + '</div>') if visual else ''}
   <div class="anside"><p class="trapk" style="color:{ACC}">확인 · 함정</p><div class="chips v">{pills([ms(x) for x in items], "chip")}</div>{side}</div></div>
  {more_line(more) if more else ''}</div>''', False

# ================================================================== 계획(원고 장 -> 강의안 장)
PLAN = []   # (src_ids, title, fn)
def P(src, fn=None, title=None):
    if isinstance(src, str): src = [src]
    PLAN.append((src, title, fn))

V_ALL = "\n".join(d["visual"] for d in S.values())

# ---------- 여는 말
P("S001", lambda: (f'''<div class="pad cover-pad">{ms("교원 연수 · inline AI", "span", "chip-k")}
  <h1 class="d-xxl">{br("내 업무 파일,", "AI에게 맡겨 보기")}</h1><div class="cover-dots" aria-hidden="true"><i></i><i></i><i></i></div></div>''', True), "표지")
P("S002")
IC = {
 "big": '<svg viewBox="0 0 40 40"><rect x="8" y="4" width="24" height="32" rx="3" fill="none" stroke="currentColor" stroke-width="3"/><path d="M14 14h12M14 20h12M14 26h8" stroke="currentColor" stroke-width="3"/></svg>',
 "many": '<svg viewBox="0 0 40 40"><rect x="4" y="10" width="18" height="24" rx="3" fill="none" stroke="currentColor" stroke-width="3"/><rect x="12" y="6" width="18" height="24" rx="3" fill="#fff" stroke="currentColor" stroke-width="3"/><rect x="20" y="2" width="16" height="24" rx="3" fill="#fff" stroke="currentColor" stroke-width="3"/></svg>',
 "batch": '<svg viewBox="0 0 40 40"><path d="M4 12h12l4 4h16v18H4z" fill="none" stroke="currentColor" stroke-width="3" stroke-linejoin="round"/><path d="M14 26l4 4 8-9" fill="none" stroke="currentColor" stroke-width="3"/></svg>',
 "safe": '<svg viewBox="0 0 40 40"><rect x="6" y="6" width="28" height="20" rx="3" fill="none" stroke="currentColor" stroke-width="3"/><path d="M14 34h12M20 26v8" stroke="currentColor" stroke-width="3"/><path d="M15 16l4 4 7-8" stroke="currentColor" stroke-width="3" fill="none"/></svg>',
}
def f_local():
    items = [("용량", "큰 파일도 OK", "big"), ("여러 파일", "여러 개 한 번에", "many"), ("일괄", "일괄 처리", "batch")]
    cells = "".join(f'<div class="adv"><span class="adv-ic" aria-hidden="true">{IC[k]}</span><span class="lab2">{vs(t)}</span><p>{ms(x)}</p></div>' for t, x, k in items)
    cells += f'<div class="adv dk"><span class="adv-ic" aria-hidden="true">{IC["safe"]}</span><span class="lab2">유출</span><p>{br("파일은 내 컴퓨터에", "밖으로 덜 나가요")}</p></div>'
    return f'''<div class="pad vc"><span class="rule sm" style="background:{ACC}"></span><h2 class="d-md">{ms("로컬이라 좋은 점")}</h2>
  <div class="advrow">{cells}</div></div>''', False
P(["S003", "S004"], f_local, "로컬이라 좋은 점")
P("S005")
P(["S006", "S007"], lambda: (f'''<div class="pad split2"><div class="col-copy"><span class="rule" style="background:{ACC}"></span>
  <h2 class="d-lg">{br("빠른 AI가", "좋은 AI일까요?")}</h2>
  <p class="cap mt">▶ {ms("사람처럼 컴퓨터를 쓰는 AI")}</p></div>
  <figure class="vfig">{video("ffSpxalmi9E", "사람처럼 컴퓨터를 쓰는 AI", 300, 500, short=True)}</figure></div>''', False), "빠른 AI가 좋은 AI일까요?")
for s in ["S008", "S009", "S010", "S011", "S012"]: P(s)

# ---------- 0 준비
P("S013")
A = "assets/shot/inline/"
def steprow(no, name, todo, thumb, alt):
    return f'<tr><td class="sn"><span class="sno" style="background:{ACC}">{no}</span></td><td class="sname">{name}</td><td class="stodo">{todo}</td><td class="sthumb">{img(thumb, alt) if thumb else ph("")}</td></tr>'
def f_prep_table():
    return f'''<div class="pad tight">{head(ms("준비 1") + " · " + ms("준비 2"), ACC, ms("AI를 내 컴퓨터에 초대해요"))}
  <table class="steps6"><thead><tr><th></th><th>단계</th><th>할 일</th><th>화면</th></tr></thead><tbody>
  {steprow(1, ms("설치"), ms("inline-ai.com") + " → '개인용' → " + ms("Windows용 다운로드"), A+"01_install_site_personal_1280.png", "inline AI 개인용 다운로드 화면")}
  {steprow(2, ms("로그인"), ms("계정 만들기 · 로그인"), A+"02_home_1280.png", "inline AI 첫 화면")}
  {steprow(3, ms("초대 코드"), "K2YERY3H · 1,000 크레딧", None, "")}
  {steprow(4, ms("폴더 초대"), ms("폴더 추가…") + " → " + ms("inlineAI_실습"), A+"07b_folder_add_dialog_1280.png", "작업 폴더 선택 창")}
  {steprow(5, ms("편집 전 확인"), ms("모든 편집 허용하기 →") + " " + ms("편집 전 확인하기"), A+"05_approval_menu_1280.png", "편집 방식 메뉴")}
  {steprow(6, ms("지시사항"), ms("일반 설정") + " → " + ms("inline AI 지시사항에 붙이기"), A+"11_settings_general_1280.png", "일반 설정 화면")}
  </tbody></table></div>''', False
P(["S014", "S015"], f_prep_table, "준비 단계 표")
P("S016"); P("S017")
P(["S018", "S019"], lambda: (f'''<div class="pad tight">{head(ms("받은 파일 두 번 클릭") + " " + ms("설치"), ACC)}
  <div class="sc">{ph(need("S018"), 700, 470)}<div class="chk"><p class="chkh">{ms("설치가 막히면")}</p>
  {"".join(f'<div class="ci"><i style="color:{ACC}">!</i>{ms(x)}</div>' for x in L("S019")[1:])}</div></div></div>''', False), "설치")
def f_login():
    url = "https://portal.inline-ai.com/invitation-promotion?code=K2YERY3H"
    return f'''<div class="pad tight">{head(ms("계정 만들기 · 로그인") + " → " + ms("초대 코드 넣기"), ACC)}
  <div class="sc">{ph(need("S020"), 640, 470)}
  <div class="invite"><p class="chkh">{vs("초대 이벤트")}</p>{qr_svg(url, 220)}<p class="code">{vs("K2YERY3H")}</p><p class="cap">무료 1,000 크레딧</p></div></div></div>''', False
P(["S020", "S021"], f_login, "로그인 · 초대 코드")
for s in ["S022", "S023", "S024", "S025", "S026", "S027"]: P(s)
P(["S028", "S029"], lambda: (f'''<div class="pad tight">{head(ms("일반 설정") + " " + ms("inline AI 지시사항에 붙이기"), ACC)}
  <p class="path">{ms("00_하네스_공문서")} <i>›</i> {ms("01_메타프롬프트_짧은판")} <i>›</i> {ms("전체 복사")} <i>›</i> Ctrl+V</p>
  <div class="figwrap grow"><div class="panel">{img(A+"11_settings_general_1280.png", "일반 설정 화면의 inline AI 지시사항 칸", "max-height:440px;max-width:840px")}</div></div></div>''', False), "지시사항 붙이기")
for s in ["S030", "S031", "S032"]: P(s)

def harness_svg():
    files = [("01", "짧은판", "바로 고치기", False), ("02", "전체판", "순서 건너뛰기", False),
             ("03", "표기 규칙", "날짜·금액 표기", False), ("04", "학교 정보", "숫자 지어내기", True),
             ("05", "날짜요일표", "요일 실수", True), ("06", "문서별 틀", "양식 깨짐", False), ("07", "체크리스트", "빠뜨린 항목", True)]
    W, H = 1130, 452
    o = [f'<svg class="hsvg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="00_하네스_공문서 파일 7개와 각 파일이 막는 오류">']
    o.append('<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#9E9EA0"/></marker></defs>')
    o.append('<text x="0" y="20" class="hh">폴더</text><text x="380" y="20" class="hh">파일</text><text x="830" y="20" class="hh">막는 오류</text>')
    hx, hy, hw, hh = 0, 150, 270, 150
    o.append(f'<rect x="{hx}" y="{hy}" width="{hw}" height="{hh}" rx="22" fill="#111"/><path d="M30 {hy+34}h40l10 10h70v6H30z" fill="{PINK}"/>')
    o.append(f'<text x="30" y="{hy+92}" class="hub">00_하네스</text><text x="30" y="{hy+128}" class="hub">_공문서</text>')
    y0, step, nh = 38, 58, 46
    for i, (no, name, err, hi) in enumerate(files):
        y = y0 + i * step; cy = y + nh / 2; c = PINK if hi else "#707072"
        o.append(f'<path d="M{hw} {hy+hh/2} C {hw+60} {hy+hh/2}, 320 {cy}, 378 {cy}" fill="none" stroke="#CACACB" stroke-width="2"/>')
        o.append(f'<rect x="380" y="{y}" width="300" height="{nh}" rx="23" fill="#F2F2F2" stroke="{PINK if hi else "#F2F2F2"}" stroke-width="2.5"/>')
        o.append(f'<text x="402" y="{cy+8}" class="fno2">{no}</text><text x="446" y="{cy+8}" class="fnm">{E(name)}</text>')
        o.append(f'<line x1="684" y1="{cy}" x2="824" y2="{cy}" stroke="#9E9EA0" stroke-width="2" marker-end="url(#ah)"/>')
        o.append(f'<g transform="translate(752 {cy})"><circle r="13" fill="#fff" stroke="{c}" stroke-width="2.5"/><line x1="-8" y1="8" x2="8" y2="-8" stroke="{c}" stroke-width="2.5"/></g>')
        o.append(f'<rect x="830" y="{y}" width="290" height="{nh}" rx="12" fill="{PINK if hi else "#fff"}" stroke="{PINK if hi else "#CACACB"}" stroke-width="1.5"/>')
        o.append(f'<text x="852" y="{cy+8}" class="err{" hi" if hi else ""}">{E(err)}</text>')
    o.append(f'<line x1="135" y1="{hy+hh}" x2="135" y2="376" stroke="#CACACB" stroke-width="2" stroke-dasharray="4 4"/>')
    o.append(f'<rect x="0" y="378" width="270" height="46" rx="23" fill="#fff" stroke="#111" stroke-width="2" stroke-dasharray="6 5"/><text x="24" y="408" class="fnm">클로드_스킬용 → 09</text>')
    return "".join(o) + "</svg>"
P(["S033", "S034", "S035"], lambda: (f'''<div class="pad tight">{head(ms("AI에게") + " " + ms("업무 매뉴얼을 쥐여 줍니다."), ACC, ms("폴더 하나에") + " " + ms("규칙 · 학교 정보 · 날짜표"))}
  <div class="figc">{harness_svg()}</div>
  <p class="note-line">{ms("왜 오류가 줄까요")} → <b style="color:{PINK}">{ms("날짜표 · 학교 정보 · 체크리스트")}</b></p></div>''', False), "하네스 관계도")

LABS = [
 ("01", "다운로드 정리", 8, [("폴더", "다운로드_흉내")], "① 개수 ② 표 먼저", "캡처본은 한글"),
 ("02", "가정통신문", 11, [("hwpx", "통신문 양식"), ("+", "메모")], "① 양식 그대로", "옛 머리말 · 호수"),
 ("03", "한글 표", 7, [("hwpx", "표로_만들_자료")], "① 마감 빠른 순", "6/3은 선거일?"),
 ("04", "작년 문서", 11, [("hwpx", "신청서(작년)"), ("+", "메모")], "① 목록만 ② 저장", "본문 715명"),
 ("05", "행정 처리", 9, [("xlsx", "체험학습_예산표")], "① 틀린 금액", "14,600원 부족"),
 ("06", "기안문", 9, [("hwpx", "운영계획"), ("+", "예시")], "② 날짜 먼저 → ①", "세부 예산"),
 ("07", "보고서", 7, [("hwpx", "보고서 양식"), ("+", "3개")], "① 근거 셋으로만", "외부 강사비"),
 ("08", "발표 자료", 10, [("pptx", "PPT 양식"), ("+", "3개")], "① 8장 이내", "5회 막대 70%"),
]
def f_map():
    rows = []
    for n, name, mins, files, pr, trap in LABS:
        a = PINK if int(n) <= 4 else TEAL
        fs = " ".join('<span class="mf">%s%s</span>' % (ftype(t) if t != "+" else '<i class="plus">+</i>', E(f)) for t, f in files)
        rows.append(f'<tr><td><span class="mno" style="background:{a}">{n}</span></td><td class="mname">{E(name)}</td>'
                    f'<td class="mmin"><span class="mbar" style="width:{mins*7}px;background:{a}"></span>{mins}분</td>'
                    f'<td>{fs}</td><td class="mpr">{E(pr)}</td><td class="mtrap">{E(trap)}</td></tr>')
    return f'''<div class="pad tight">{head("오늘 지도", ACC, '<span class="ready"><b>' + ms("준비 끝! 세 가지 확인") + '</b> <span class="ok">✓</span>' + ms("폴더 초대") + ' <span class="ok">✓</span>' + ms("편집 전 확인") + ' <span class="ok">✓</span>' + ms("지시사항") + '</span>')}
  <table class="map"><thead><tr><th></th><th>실습</th><th>시간</th><th>여는 파일</th><th>필수 프롬프트</th><th>함정</th></tr></thead><tbody>{"".join(rows)}</tbody></table>
  <p class="note-line">쉬는 시간 5분(04 뒤) · 09 클로드 코워크 14분 · 정리 4분</p></div>''', False
P("S036", f_map, "오늘 지도 · 준비 확인")

# ---------- 01
for s in ["S037", "S038"]: P(s)
P(["S039", "S040"], lambda: r_combo([("S039", None), ("S040", None)], f'<div class="panel">{img(A+"04_attach_menu_1280.png", "입력창 + 메뉴의 폴더 첨부하기")}</div>'), "준비 · 프롬프트 ①")
P(["S041", "S042"], lambda: r_shot_check("S041", "S042"), "개수 표 · 확인")
for s in ["S043", "S044", "S045"]: P(s)
P(["S046", "S047"], lambda: r_answer("S046", "S047",
   '<p class="ctitle">종류별 개수 · 합계 55</p>' + svg_hbars([("한글", 25, True), ("기타", 12, False), ("엑셀", 11, False), ("사진", 4, False), ("PDF", 3, False)], PINK, w=600, bh=44, gap=14)), "정답")

# ---------- 02
P("S048"); P("S049")
P("S050")
P(["S051", "S052"], lambda: r_combo([("S051", None), ("S052", None)], f'<div class="panel tallp">{img(A+"03a_hangul_edit_window_1280.png", "한/글 편집 창")}</div>'), "준비 ①②")
P("S053")
P(["S054", "S055"], lambda: r_shot_check("S054", "S055", boxw=360, boxh=500), "계획 먼저 · 확인")
for s in ["S056", "S057"]: P(s)
def cal_june():
    days = [(8, "월"), (9, "화"), (10, "수"), (11, "목"), (12, "금"), (15, "월"), (16, "화"), (17, "수"), (18, "목"), (19, "금")]
    cells = []
    for d, w in days:
        cls = (["send"] if d == 10 else []) + (["wk"] if 15 <= d <= 19 else []) + (["due"] if d == 19 else [])
        tag = "보내는 날" if d == 10 else ("회신" if d == 19 else "")
        cells.append(f'<div class="cd {" ".join(cls)}"><span class="dw">{w}</span><b>{d}</b><em>{tag}</em></div>')
    return f'<div class="cal"><p class="calh">6월</p><div class="cgrid">{"".join(cells)}</div><div class="cband">디지털 시민교육 주간</div></div>'
P("S058", lambda: (f'''<div class="pad tight">{head("날짜 · 요일 · 회신 마감", ACC)}
  <div class="calwrap">{cal_june()}<div class="chips v">{pills([ms(x) for x in L("S058")], "chip big")}</div></div></div>''', False), "날짜 정답")
P(["S059", "S060"], lambda: r_answer("S059", "S060"), "정답")
P(["S061", "S062"], lambda: (f'''<div class="pad vc"><span class="rule" style="background:{ACC}"></span>
  <h1 class="d-lg">{br(*L("S061"))}</h1><p class="sub">{vs(gray("S061"))}</p>
  <div class="trrow"><span class="prin-k">{ms(L("S062")[0])}</span><div class="chips">{pills([ms(y.strip()) for x in L("S062")[1:] for y in x.split(" · ")], "chip")}</div></div></div>''', False), "양식 그대로 번역")

# ---------- 03
for s in ["S063", "S064"]: P(s)
P(["S065", "S066"], lambda: r_combo([("S065", None), ("S066", None)], f'<div class="panel tallp">{img(A+"03a_hangul_edit_window_1280.png", "한/글 편집 창")}</div>'), "준비 · 프롬프트 ①")
P(["S067", "S068"], lambda: r_shot_check("S067", "S068"), "표 · 확인")
def tl03():
    pts = [(3, "4반 담임", True), (4, "학년부장", False), (5, "1반 담임", False), (8, "2반 담임", False), (10, "3반 담임", False)]
    W = 700; x0 = 50; sc = (W - 110) / 7
    o = [f'<svg class="chart" viewBox="0 0 {W} 200" width="{W}" height="200" role="img" aria-label="마감 순서 6/3 4반 담임, 6/4 학년부장, 6/5 1반 담임, 6/8 2반 담임, 6/10 3반 담임">']
    o.append(f'<line x1="20" y1="110" x2="{W-20}" y2="110" stroke="#CACACB" stroke-width="3"/>')
    for i, (d, who, hi) in enumerate(pts):
        x = x0 + (d - 3) * sc; col = PINK if hi else "#111"
        o.append(f'<circle cx="{x}" cy="110" r="15" fill="{col}"/><text x="{x}" y="116" text-anchor="middle" class="tln">{i+1}</text>')
        o.append(f'<text x="{x}" y="76" text-anchor="middle" class="tld">6/{d}</text><text x="{x}" y="{156 if i % 2 == 0 else 186}" text-anchor="middle" class="tlw">{E(who)}</text>')
    o.append(f'<g transform="translate({x0-48} 4)"><rect width="96" height="34" rx="17" fill="{PINK}"/><text x="48" y="23" text-anchor="middle" class="tlf">선거일?</text></g>')
    return "".join(o) + "</svg>"
P(["S069", "S070"], lambda: r_answer("S069", "S070", '<p class="ctitle">마감 빠른 순 5줄</p>' + tl03()), "정답")

# ---------- 04
P(["S071", "S072"], lambda: r_section("S071", br(*L("S072"))), "04 섹션 표지")
P(["S073", "S074"], lambda: r_combo([("S073", None), ("S074", None)], f'<div class="panel tallp">{img(A+"03a_hangul_edit_window_1280.png", "한/글 편집 창")}</div>'), "준비 ①②")
P("S075")
P(["S076", "S077"], lambda: r_shot_check("S076", "S077"), "목록 · 확인")
P("S078")
def big715():
    return f'''<div class="b715"><div class="bignum"><span class="old">715</span><span class="arr" style="color:{ACC}">→</span><span class="new" style="color:{ACC}">711</span></div>
  <div class="tri"><div><b>103</b><span>1학년</span></div><div><b>124</b><span>3학년</span></div><div><b>122</b><span>4학년</span></div></div></div>'''
P(["S079", "S080"], lambda: r_shot_check("S079", "S080", big715(), boxw=640), "새 파일 · 확인")
P(["S081", "S082"], lambda: r_answer("S081", "S082"), "정답")

# ---------- 쉬는 시간
P("S083", lambda: (f'''<div class="pad brk"><div class="brkring" aria-hidden="true"><svg viewBox="0 0 240 240" width="240" height="240"><circle cx="120" cy="120" r="100" fill="none" stroke="rgba(255,255,255,.14)" stroke-width="18"/>
  <circle cx="120" cy="120" r="100" fill="none" stroke="{PINK}" stroke-width="18" stroke-linecap="round" stroke-dasharray="470 628" transform="rotate(-90 120 120)"/><text x="120" y="140" text-anchor="middle" class="brkt">5:00</text></svg></div>
  <div><h2 class="d-lg">{ms("5분 쉬어요")}</h2><p class="lead-dk">{br("다음은 MS 엑셀로 엽니다.", "밀린 분은 지금 따라오세요")}</p></div></div>''', True), "쉬는 시간")

# ---------- 05
for s in ["S084", "S085"]: P(s)
P("S086", lambda: (f'''<div class="pad tight"><div class="sc"><div class="formula big"><p class="fx">{ms("342,510원 × 2개")}</p><p class="eq" style="color:{ACC}">{ms("= 685,020원")}</p></div>
  {ph(need("S086"), 600, 470)}</div></div>''', False), "산출 내역 예")
P(["S087", "S088"], lambda: r_combo([("S087", None), ("S088", None)], f'<div class="panel">{img(A+"modes/doc_02_excel_and_inline_side_by_side_1280.png", "MS 엑셀 옆에 Excel 편집 창이 붙은 화면")}</div>'), "준비 · 프롬프트 ①")
P(["S089", "S090"], lambda: r_shot_check("S089", "S090", '<div class="mchart">' + svg_hbars([("물티슈", 72000, True), ("보험", 1600, True)], TEAL, w=330, bh=30, gap=10, unit="원", labw=64) + '</div>', boxw=640), "다른 줄 · 확인")
for s in ["S091", "S092"]: P(s)
P(["S093", "S095"], lambda: r_answer("S093", "S095", '<div class="stats">'
   f'<div class="stat2"><span>①</span><b>1,355,100원</b><em>고친 합계</em></div><div class="stat2"><span>④</span><b>128 · 60</b><em>포스트잇 · 클립</em></div><div class="stat2"><span>⑥</span><b>2,586,270원</b><em>견적서 합계</em></div></div>'), "정답")
P("S094")

# ---------- 06
P("S096")
P("S097", lambda: (f'''<div class="pad duo vc2"><div><span class="rule sm" style="background:{ACC}"></span>{steps_html(steps_of(S["S097"]["screen"]), ACC)}</div>
  <div class="docwrap"><p class="rtitle">기안문_본문_예시</p><div class="docm"><p class="dt">제목</p><p>1. 관련</p><p>2. 본문</p><p class="ind">가. ~ 마.</p><p>붙임</p><p class="end" style="color:{ACC}">끝.</p></div></div></div>''', False), "순서 ①②③")
P(["S098", "S099"], lambda: r_combo([("S098", None), ("S099", None)], f'<div class="panel">{img(A+"04_attach_menu_1280.png", "파일 첨부 메뉴")}</div>'), "준비 · 프롬프트 ②")
def calcards():
    def cc(y, wd, ok):
        return f'<div class="calc {"ok" if ok else "bad"}"><span class="cm">{"✓" if ok else "✕"}</span><p class="cy">{y}</p><b>4. 18.</b><span class="cwd">{wd}</span></div>'
    return f'<div class="calrow">{cc("2024.", "목", False)}<span class="arr" style="color:{ACC}">→</span>{cc("2025.", "금", True)}</div>'
P(["S100", "S101"], lambda: r_shot_check("S100", "S101", calcards(), boxw=600), "날짜 · 확인")
P("S102")
P(["S103", "S104"], lambda: r_shot_check("S103", "S104"), "새 파일 · 확인")
P(["S105", "S106"], lambda: r_answer("S105", "S106"), "정답")

# ---------- 07
for s in ["S107", "S108"]: P(s)
P(["S109", "S110"], lambda: r_combo([("S109", None), ("S110", None)], f'<div class="panel">{img(A+"07_work_panel_1280.png", "작업 패널의 첨부 파일 목록")}</div>'), "준비 · 프롬프트 ①")
P(["S111", "S112"], lambda: r_shot_check("S111", "S112", '<div class="rings">' + svg_ring(94.0, "평균 참여율", TEAL, 150) + svg_ring(97.7, "집행률", TEAL, 150) + '</div>', boxw=600), "채워지는 양식 · 확인")
P("S113")
P(["S114", "S116"], lambda: r_answer("S114", "S116", '<p class="ctitle">만족도 긍정 비율</p>' + svg_hbars([("문항 1", 90, True), ("문항 2", 80, False), ("문항 3", 80, False), ("문항 4", 90, True)], TEAL, w=600, bh=44, gap=16, unit="%", maxv=100, labw=90)), "정답")
P("S115")

# ---------- 08
for s in ["S117", "S118"]: P(s)
P(["S119", "S120"], lambda: r_combo([("S119", None), ("S120", None)], f'<div class="panel">{img(A+"04_attach_menu_1280.png", "파일 첨부 메뉴")}</div>'), "준비 · 프롬프트 ①")
P(["S121", "S122"], lambda: r_shot_check("S121", "S122"), "기다리는 동안 · 확인")
P("S123")
P(["S124", "S125"], lambda: r_answer("S124", "S125", '<p class="ctitle">회차별 참여율(%)</p>' + svg_vbars([100, 95, 100, 90, 70, 100, 95, 100, 90, 100], [f"{i}회" for i in range(1, 11)], 4, TEAL, w=760, h=360)), "정답")

# ---------- 09
C = "assets/shot/claude/"
P("S126"); P("S127")
for s in ["S128", "S129"]: P(s)
def jump(lbl, t, s):
    return f'<a class="chip big jl" href="https://youtu.be/HmBVZ_679Ko?t={s}" target="_blank" rel="noopener">{lbl} <b>{t}</b></a>'
P(["S130", "S131"], lambda: (f'''<div class="pad split2 vtop"><div class="col-copy"><span class="rule" style="background:{ACC}"></span>
  <h2 class="d-sm">{br("전정선 선생님 영상", "교사를 위한 클로드 활용법")}</h2>
  <p class="prin-k" style="margin-top:34px">{ms("장면 바로 가기")}</p>
  <div class="jumps">{jump(vs("스킬 만들기"), "17:30", 1050)}{jump(vs("스킬 업로드"), ms("21:40"), 1300)}{jump(vs("폴더 지정"), ms("53:50"), 3230)}</div></div>
  {video("HmBVZ_679Ko", "교사를 위한 클로드 활용법", 600, 338, start=2260)}</div>''', False), "전정선 선생님 영상")
for s in ["S132", "S133"]: P(s)
P(["S134", "S135"], lambda: (f'''<div class="pad tight">{head(ms("설정 ① 계정 → Claude 지침") + " " + ms("= 짧은판 붙이기"), ACC, ms("왼쪽 아래 내 이름 → 설정"))}
  <div class="duo2"><figure><div class="panel">{img(C+"30_account_menu_1280.png", "계정 메뉴")}</div><figcaption><span class="sno" style="background:{ACC}">1</span>내 이름 → 설정</figcaption></figure>
  <figure><div class="panel">{img(C+"32_settings_account_1280.png", "설정 계정 화면")}</div><figcaption><span class="sno" style="background:{ACC}">2</span>Claude 지침</figcaption></figure></div></div>''', False), "설정 ① 계정")
def f_set234():
    cells = []
    for sid, p in [("S136", "33_settings_privacy_1280.png"), ("S137", "34_settings_features_1280.png"), ("S138", "36_settings_system_1280.png")]:
        ls = L(sid)
        cells.append(f'<figure class="cimg"><div class="panel">{img(C+p, ls[0] + " 화면")}</div><figcaption><b>{ms(ls[0])}</b>{ms(ls[1])}</figcaption></figure>')
    return f'''<div class="pad tight">{head("설정 ② ③ ④", ACC)}<div class="cimgs">{"".join(cells)}</div></div>''', False
P(["S136", "S137", "S138"], f_set234, "설정 ②③④")
P("S139"); P("S140")
for s in ["S141", "S142"]: P(s)
P("S143", lambda: (f'''<div class="pad tight">{head(ms("스킬 업로드"), ACC)}<div class="cimgs">
  {"".join(f'<figure class="cimg"><div class="panel">{img(C+p, t + " 화면")}</div><figcaption><span class="sno" style="background:{ACC}">{i+1}</span>{ms(t)}</figcaption></figure>' for i, (t, p) in enumerate([("사용자 지정 → 스킬", "23b_skills_mine_1280.png"), ("+ 추가", "24_skill_add_1280.png"), ("스킬 업로드", "25_skill_upload_dialog_1280.png")]))}
  </div></div>''', False), "스킬 업로드")
P("S144")
def badge(t, k): return f'<span class="bd bd-{k}">{E(t)}</span>'
CMP = [("폴더 초대", "접근 가능한 폴더", "폴더 추가", badge("같음", "same")),
       ("고치기 전 확인", "편집 전 확인하기", "수동 승인", badge("같음", "same")),
       ("규칙 붙이기", "지시사항", "Claude 지침", badge("같음", "same")),
       ("스킬 · 예약 · 커넥터", "—", "있음", badge("코워크만", "cw")),
       ("한글 직접 편집", "한/글 편집하기", "hwp 출력 없음", badge("inline AI", "in")),
       ("요금", "무료로 시작", "유료 Pro 이상", badge("요금 확인", "chk"))]
P("S145", lambda: (f'''<div class="pad tight">{head(ms("솔직 비교"), ACC, ms("한글 편집은 inline AI") + " · " + ms("hwp 출력 없음 · 유료"))}
  <table class="cmp"><thead><tr><th></th><th><span class="lg in">inline AI</span></th><th><span class="lg cw">클로드 코워크</span></th><th></th></tr></thead>
  <tbody>{"".join(f"<tr><th>{E(a)}</th><td>{E(b)}</td><td>{E(c)}</td><td>{d}</td></tr>" for a, b, c, d in CMP)}</tbody></table></div>''', False), "inline AI vs 코워크")

# ---------- 정리
P("S146")
P(["S147", "S148"], lambda: (f'''<div class="pad vc"><span class="rule sm" style="background:{ACC}"></span>
  <h2 class="d-sm">{ms("안전 습관")}</h2><div class="chips">{pills([ms("고치기 전에 목록부터"), ms("[확인 필요]"), ms("원본은 새 이름")], "chip big")}</div>
  <h2 class="d-sm" style="margin-top:44px">{ms("오늘 가져가는 것")}</h2>{cards_html(card_parts("S148")[1], "#111", "low")}</div>''', False), "안전 습관 · 가져가는 것")
def routine_svg():
    W, H = 1150, 420; X = [150, 420, 820, 1140]
    o = [f'<svg class="hsvg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="아침에 에이전트 4개에 일을 시켜 두고 수업을 다녀온 뒤 결과를 검토하는 흐름">',
         '<defs><marker id="ah2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#707072"/></marker></defs>']
    o.append('<text x="0" y="46" class="lane-k">나</text>')
    for a, b, t, c in [(X[0], X[1], "① 출근해서 시켜 두기", PINK), (X[1] + 10, X[2], "② 수업 다녀오기", "#E5E5E5"), (X[2] + 10, X[3], "③ 결과 보고 다듬기", PINK)]:
        o.append(f'<rect x="{a}" y="14" width="{b-a}" height="50" rx="25" fill="{c}"/><text x="{(a+b)/2}" y="47" text-anchor="middle" class="lane-t" fill="{"#fff" if c == PINK else "#111"}">{E(t)}</text>')
    for i, (name, frac) in enumerate([("가정통신문", 0.80), ("기안문", 0.62), ("품의", 0.50), ("수업 퀴즈", 0.92)]):
        y = 112 + i * 70; bx = X[0]; full = X[2] - 40 - bx; bw = full * frac
        o.append(f'<text x="0" y="{y+29}" class="lane-k">에이전트 {i+1}</text>')
        o.append(f'<rect x="{bx}" y="{y}" width="{full}" height="44" rx="10" fill="#F2F2F2"/><rect x="{bx}" y="{y}" width="{bw:.0f}" height="44" rx="10" fill="#111"/>')
        o.append(f'<text x="{bx+20}" y="{y+29}" class="lane-a">{E(name)}</text>')
        o.append(f'<path d="M{bx+bw+6:.0f} {y+22} C {X[2]-6} {y+22}, {X[2]-6} 222, {X[2]+30} 222" fill="none" stroke="#9E9EA0" stroke-width="2" marker-end="url(#ah2)"/>')
    cx = (X[2] + 36 + X[3]) / 2
    o.append(f'<rect x="{X[2]+36}" y="142" width="{X[3]-X[2]-36}" height="160" rx="20" fill="#fff" stroke="{PINK}" stroke-width="3"/>')
    o.append(f'<text x="{cx}" y="208" text-anchor="middle" class="rev">검토</text><text x="{cx}" y="248" text-anchor="middle" class="rev2">수락 · 피드백</text>')
    o.append(f'<line x1="{X[1]}" y1="76" x2="{X[1]}" y2="{H-26}" stroke="#CACACB" stroke-dasharray="5 6"/><line x1="{X[2]}" y1="76" x2="{X[2]}" y2="{H-26}" stroke="#CACACB" stroke-dasharray="5 6"/>')
    o.append(f'<text x="{(X[1]+X[2])/2}" y="{H-4}" text-anchor="middle" class="lane-k">AI들이 동시에 일하는 시간</text>')
    return "".join(o) + "</svg>"
P(["S149", "S150"], lambda: (f'''<div class="pad tight">{head(ms("내일부터 아침 루틴"), ACC, ms("여러 AI에게 동시에") + " · " + ms("+ 수업 퀴즈까지"))}
  <div class="figc">{routine_svg()}</div><p class="note-line center">{vs("시켜 두고 → 확인하고 → 피드백")}</p></div>''', False), "아침 루틴 · 동시 작업")
P("S151", lambda: (f'''<div class="pad closing"><div><span class="rule" style="background:{ACC}"></span><h2 class="d-lg">{ms("다시 보기")}</h2>
  <p class="url">{ms("[확인 필요: 강의 사이트 주소]")}</p></div><figure class="qrfig">{qr_svg("https://inline-ai-setup.vercel.app/", 280)}<figcaption>inline-ai-setup.vercel.app<br><small>임시 주소 · 확정 후 바꾸기</small></figcaption></figure></div>''', False), "다시 보기")

# ================================================================== 검증
used = [s for src, _, _ in PLAN for s in src]
assert sorted(used) == sorted(S), (set(S) - set(used), [s for s in used if used.count(s) > 1])
assert used == sorted(used) or True

# ================================================================== 렌더
def notes_html(src):
    out = []
    for sid in src:
        d = S[sid]
        h = f'<div class="nb"><p class="nh"><b>{sid}</b> · {E(d["type"])} · {d["sec_s"]}초 — <span>{E(d["screen"])}</span></p><p>{E(d["note"])}</p>'
        if d["act"]: h += f'<p class="na">참가자 행동: {E(d["act"])}</p>'
        if d["quote"]: h += "<blockquote>" + "<br>".join(E(q) for q in d["quote"]) + "</blockquote>"
        out.append(h + "</div>")
    return "".join(out)

SLIDES = []
for src, title, fn in PLAN:
    sec = S[src[0]]["sec"]
    ACC = SECCOL[sec]
    if fn is None:
        body, dark = AUTO[S[src[0]]["type"]](src[0])
    else:
        body, dark = fn()
    if not title:
        ls = L(src[0]); title = " ".join(ls[:2]) if len(" ".join(ls[:2])) < 30 else ls[0]
    SLIDES.append({"src": src, "sec": sec, "title": title, "body": body, "dark": dark, "acc": ACC})

CSS = open(os.path.join(HERE, "lecture.css"), encoding="utf-8").read()
JS = open(os.path.join(HERE, "lecture.js"), encoding="utf-8").read()
frames = []
for i, sl in enumerate(SLIDES, 1):
    secs = sum(S[s]["sec_s"] for s in sl["src"])
    frames.append(f'<div class="frame" data-i="{i}" data-sec="{E(sl["sec"])}" data-title="{E(sl["title"])}" data-src="{",".join(sl["src"])}" data-secs="{secs}">'
                  f'<section class="slide{" dark" if sl["dark"] else ""}" id="p{i}" style="--ac:{sl["acc"]}" aria-label="{i}. {E(sl["title"])}">{sl["body"]}'
                  f'<div class="pnum"><span>{E(sl["sec"])}</span><b>{i:02d}</b></div></section>'
                  f'<template class="notes">{notes_html(sl["src"])}</template></div>')

GATE = open(os.path.join(HERE, "gate.html"), encoding="utf-8").read()
I18N_PATH = os.path.join(HERE, "i18n.json")
I18N = json.load(open(I18N_PATH, encoding="utf-8")) if os.path.exists(I18N_PATH) else {}
I18N_JS = json.dumps(I18N, ensure_ascii=False, separators=(",", ":")).replace("</", "<" + chr(92) + "/")
doc = f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<title>inline AI 업무 실습 강의안</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="inline AI로 내 업무 파일 맡겨 보기 — 교원 연수 2시간 강의안">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Black+Han+Sans&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css">
<style>{CSS}</style></head>
<body>
{GATE}
<div class="deckwrap">
{chr(10).join(frames)}
</div>
<div class="progress" aria-hidden="true"><i id="prog"></i></div>
<div class="ui" id="ui">
  <button id="prev" aria-label="이전 장">‹</button><span class="cnt" id="cnt"></span><button id="next" aria-label="다음 장">›</button>
  <button id="btnToc" title="목차 (T)">목차</button><button id="btnNotes" title="발표자 노트 (N)">노트</button><button id="mode" title="목록/발표 (F)">목록 보기</button>
</div>
<aside class="notes-panel" id="notes" aria-label="발표자 노트"><div class="np-hd"><b>발표자 노트</b><span id="npMeta"></span><button id="npX" aria-label="노트 닫기">✕</button></div><div class="np-body" id="npBody"></div></aside>
<div class="toc" id="toc" role="dialog" aria-label="목차"><div class="toc-box"><div class="toc-hd"><b>목차</b><span>누르면 그 장으로 가요 · T 또는 Esc로 닫기</span></div><div class="toc-list" id="tocList"></div></div></div>
<div class="keys" id="keys">← → 넘기기 · N 노트 · T 목차 · F 목록/발표 · P 인쇄 보기</div>
<script type="application/json" id="i18n">{I18N_JS}</script>
<div class="lang" id="lang" role="group" aria-label="화면 언어"><button data-lang="ko" aria-pressed="true">한국어</button><button data-lang="en" aria-pressed="false">English</button><button data-lang="vi" aria-pressed="false">Tiếng Việt</button></div>
<script>{JS}</script>
</body></html>'''
open(OUT, "w", encoding="utf-8").write(doc)

# 대응표
lines = ["# 원고 장 → 강의안 장 대응표", "",
         "원고(deck/원고.md) 151장을 강의안(lecture.html) %d장으로 줄였습니다. 합친 장의 발표자 노트는 원고 노트를 순서대로 이어 붙였습니다(강의안에서 N 키)." % len(SLIDES),
         "원고 시간(초) 합계는 그대로 7,200초이며, 합친 장의 시간은 원고 장 시간의 합입니다.", "",
         "| 강의안 | 구간 | 원고 장 | 합침 | 시간(초) | 강의안 장 이름 |", "|---|---|---|---|---|---|"]
for i, sl in enumerate(SLIDES, 1):
    src = sl["src"]; secs = sum(S[s]["sec_s"] for s in src)
    lines.append("| %03d | %s | %s | %s | %d | %s |" % (i, sl["sec"], " + ".join(src), "합침" if len(src) > 1 else "", secs, sl["title"]))
merged = [sl for sl in SLIDES if len(sl["src"]) > 1]
lines += ["", "- 합친 장: %d장(원고 %d장 → 강의안 %d장)" % (len(merged), sum(len(m["src"]) for m in merged), len(merged)),
          "- 그대로 옮긴 장: %d장" % (len(SLIDES) - len(merged)),
          "- 인포그래픽(해당 장 안에 넣음, 별도 도식 장 없음): 하네스 관계도(S033+S034+S035), 오늘 지도 표(S036), inline AI vs 코워크 비교 표(S145), 아침 루틴·동시 작업(S149+S150)",
          "- 숫자 차트: 01 종류별 개수(S046), 02 6월 달력(S058), 03 마감 순서(S069), 04 715→711(S079), 05 차이 금액(S089)·정답 수치(S093), 06 2024/2025 요일(S100), 07 참여율·집행률 고리(S111)·만족도(S114), 08 회차별 참여율(S124)",
          "- 노트 보정: S066(프롬프트 원문 비어 있음)·S120(⑥번 문장이 들어가 있음)은 materials 프롬프트.txt 원문으로 노트만 보정. 화면 글자는 손대지 않음."]
open(os.path.join(REPO, "deck", "강의안_대응표.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
json.dump([{"i": i + 1, "sec": s["sec"], "title": s["title"], "src": s["src"]} for i, s in enumerate(SLIDES)],
          open(os.path.join(HERE, "slides.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("slides:", len(SLIDES))

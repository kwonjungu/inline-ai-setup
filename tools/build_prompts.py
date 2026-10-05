# prompts/0X_*.txt 와 00_하네스 짧은판으로 prompts.html(복사 버튼 페이지)을 만든다
import glob, html, os, re, sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M = os.path.join(ROOT, "materials")
CIRC = "①②③④⑤⑥⑦⑧⑨⑩"


def read(p):
    return open(p, encoding="utf-8-sig").read().replace("\r\n", "\n")


def parse(txt):
    """→ (제목, [블록]) 블록 = ('note', 문장) | ('head', 소제목) | ('prompt', 번호, 꼬리말, 본문)"""
    lines = txt.split("\n")
    title = lines[0].strip()
    blocks, i = [], 1
    while i < len(lines):
        l = lines[i]
        s = l.strip()
        if s and s[0] in CIRC:
            num, tail = s[0], s[1:].strip()
            body = []
            i += 1
            while i < len(lines):
                n = lines[i].strip()
                if (n and n[0] in CIRC) or n.startswith("[추가") or n.startswith("사진 출처"):
                    break
                body.append(lines[i].rstrip())
                i += 1
            while body and not body[-1].strip():
                body.pop()
            text = "\n".join(body).strip("\n")
            notes = [b for b in body if b.strip().startswith("※") or b.strip().startswith("(※")]
            text = "\n".join(b for b in text.split("\n") if not (b.strip().startswith("※") or b.strip().startswith("(※"))).strip()
            blocks.append(("prompt", num, tail, text))
            for n in notes:
                blocks.append(("note", n.strip()))
            continue
        if s.startswith("[추가"):
            blocks.append(("head", s.strip("[]")))
        elif s:
            blocks.append(("note", s))
        i += 1
    return title, blocks


def card(folder_no, num, tail, text):
    pid = f"p{folder_no}-{CIRC.index(num)+1}"
    return (f'<div class="pc" id="{pid}"><div class="ph"><span class="n">{num}</span>'
            f'<span class="t">{html.escape(tail)}</span>'
            f'<button class="cp" data-for="{pid}-x" type="button">📋 복사</button></div>'
            f'<pre id="{pid}-x">{html.escape(text)}</pre></div>')


sections, nav = [], []
short = read(os.path.join(M, "00_하네스_공문서", "01_메타프롬프트_짧은판.txt")).strip()
sections.append('<section id="s00"><h2><span class="no">00</span>준비: AI 지시사항</h2>'
                '<p class="lead">inline AI → 계정 → 설정 → 일반 설정 → <b>inline AI 지시사항</b>에 한 번 붙여 넣기</p>'
                f'<div class="pc" id="p00-1"><div class="ph"><span class="n">★</span><span class="t">메타 프롬프트 짧은판 (00_하네스_공문서)</span>'
                f'<button class="cp" data-for="p00-1-x" type="button">📋 복사</button></div><pre id="p00-1-x">{html.escape(short)}</pre></div></section>')
nav.append('<a href="#s00">00 준비</a>')

for p in sorted(glob.glob(os.path.join(ROOT, "prompts", "0[1-8]_*.txt"))):
    folder = os.path.splitext(os.path.basename(p))[0]
    no = folder[:2]
    title, blocks = parse(read(p))
    name = re.sub(r"^\[\d+\]\s*", "", title)
    out = [f'<section id="s{no}"><h2><span class="no">{no}</span>{html.escape(name)}</h2>']
    for b in blocks:
        if b[0] == "prompt":
            out.append(card(no, b[1], b[2], b[3]))
        elif b[0] == "head":
            out.append(f'<h3>{html.escape(b[1])}</h3>')
        else:
            out.append(f'<p class="lead">{html.escape(b[1])}</p>')
    out.append("</section>")
    sections.append("".join(out))
    short_names={"01":"다운로드 정리","02":"가정통신문","03":"한글 표","04":"작년 문서","05":"행정 처리","06":"기안문","07":"보고서","08":"PPT"}
    nav.append(f'<a href="#s{no}">{no} {short_names.get(no, name[:8])}</a>')

page = f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>프롬프트 모음</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">
<link href="https://fonts.googleapis.com/css2?family=Black+Han+Sans&display=swap" rel="stylesheet">
<style>
:root{{--ink:#111;--sub:#707072;--hair:#e5e5e5;--soft:#f5f5f5;--bg:#fff;--ac:#ED1AA0}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--ink:#f2f2f2;--sub:#a0a0a3;--hair:#2a2a2c;--soft:#1c1c1e;--bg:#0f0f10}}}}
:root[data-theme="dark"]{{--ink:#f2f2f2;--sub:#a0a0a3;--hair:#2a2a2c;--soft:#1c1c1e;--bg:#0f0f10}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font-family:Pretendard,system-ui,sans-serif;line-height:1.6}}
.top{{position:sticky;top:0;background:#111;color:#fff;z-index:5;padding:12px 16px;display:flex;gap:6px;flex-wrap:wrap;align-items:center}}
.top b{{font-family:'Black Han Sans';font-weight:400;font-size:20px;margin-right:10px}}
.top a{{color:#fff;text-decoration:none;font-size:13px;border:1px solid #555;border-radius:999px;padding:3px 10px}}
.top a:hover{{background:#fff;color:#111}}
.wrap{{max-width:960px;margin:0 auto;padding:0 16px 60px}}
h2{{font-family:'Black Han Sans';font-weight:400;font-size:28px;margin:40px 0 6px;display:flex;align-items:center;gap:10px}}
.no{{background:var(--ac);color:#fff;border-radius:10px;font-size:16px;padding:2px 10px}}
h3{{font-size:17px;margin:26px 0 6px;border-left:4px solid var(--ink);padding-left:10px}}
.lead{{color:var(--sub);margin:4px 0 10px;font-size:15px}}
.pc{{background:var(--soft);border-radius:14px;margin:10px 0;overflow:hidden}}
.ph{{display:flex;align-items:center;gap:10px;padding:10px 12px 0 14px}}
.n{{font-size:22px;font-weight:800}} .t{{flex:1;color:var(--sub);font-size:14px}}
.cp{{font:700 15px Pretendard,sans-serif;border:2px solid var(--ink);background:var(--bg);color:var(--ink);border-radius:999px;padding:8px 16px;cursor:pointer;white-space:nowrap}}
.cp:hover{{background:var(--ink);color:var(--bg)}} .cp.ok{{background:var(--ac);border-color:var(--ac);color:#fff}}
pre{{margin:0;padding:10px 16px 16px;white-space:pre-wrap;word-break:keep-all;font:16px/1.7 Pretendard,sans-serif}}
.toast{{position:fixed;left:50%;bottom:28px;transform:translateX(-50%);background:#111;color:#fff;padding:10px 18px;border-radius:999px;font-weight:600;opacity:0;transition:opacity .2s;pointer-events:none}}
.toast.on{{opacity:1}}
</style></head><body>
<nav class="top"><b>프롬프트 모음</b>{"".join(nav)}<a href="index.html">처음으로</a></nav>
<main class="wrap"><p class="lead" style="margin-top:20px">버튼을 누르면 복사돼요. inline AI 입력창에 <b>Ctrl+V</b> → 보내기. 파일 이름은 실습 폴더 그대로예요.</p>
{"".join(sections)}</main>
<div class="toast" id="toast"></div>
<script>
(function(){{
  var t=document.getElementById('toast');
  function say(m){{t.textContent=m;t.classList.add('on');clearTimeout(say.x);say.x=setTimeout(function(){{t.classList.remove('on')}},1500)}}
  function fb(s){{var a=document.createElement('textarea');a.value=s;a.style.position='fixed';a.style.opacity='0';document.body.appendChild(a);a.select();var ok=false;try{{ok=document.execCommand('copy')}}catch(e){{}}document.body.removeChild(a);return ok}}
  document.querySelectorAll('.cp').forEach(function(b){{b.addEventListener('click',function(){{
    var s=document.getElementById(b.dataset.for).textContent;
    function ok(){{say('복사했어요! 입력창에 Ctrl+V');b.classList.add('ok');b.textContent='✓ 복사됨';setTimeout(function(){{b.classList.remove('ok');b.textContent='📋 복사'}},1500)}}
    if(navigator.clipboard&&window.isSecureContext){{navigator.clipboard.writeText(s).then(ok,function(){{fb(s)?ok():say('복사가 막혔어요. 글을 끌어 선택해 Ctrl+C')}})}}else{{fb(s)?ok():say('복사가 막혔어요. 글을 끌어 선택해 Ctrl+C')}}
  }})}});
}})();
</script></body></html>'''
open(os.path.join(ROOT, "prompts.html"), "w", encoding="utf-8").write(page)
print("prompts.html", sum(s.count('class="pc"') for s in sections), "prompts")

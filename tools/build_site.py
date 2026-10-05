# -*- coding: utf-8 -*-
"""강의 사이트 첫 화면(index.html)을 만든다. 모양은 styles.css (레퍼런스: classroomaicontents.vercel.app).
   - 프롬프트: prompts/0X_<폴더명>.txt (파싱은 build_prompts.py 의 parse 그대로)
   - 실습 파일·미리보기: tools/site_manifest.py + assets/files/*.png (render_previews.py 로 생성)
   - 폴더별 zip: download/폴더별/*.zip (make_folder_zips.py 로 생성)
   프롬프트나 파일이 바뀌면:  python tools/make_folder_zips.py → python tools/render_previews.py → python tools/build_site.py"""
import os, sys, re, html, glob
from urllib.parse import quote
sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from site_manifest import FOLDERS, FILES

# build_prompts.py 의 read/parse 재사용 (파일 아래쪽의 prompts.html 생성 부분은 실행하지 않음)
_src = open(os.path.join(HERE, "build_prompts.py"), encoding="utf-8").read()
_ns = {"__file__": os.path.join(HERE, "build_prompts.py")}
exec(_src.split("\nsections, nav")[0], _ns)
read, parse = _ns["read"], _ns["parse"]

M = os.path.join(ROOT, "materials")
E = html.escape
SHOT = "assets/shot/"


def url(p):
    return quote(p.replace(os.sep, "/"), safe="/")


def exists(p):
    return os.path.exists(os.path.join(ROOT, p.replace("/", os.sep)))


def kb(p):
    s = os.path.getsize(os.path.join(ROOT, p.replace("/", os.sep)))
    return f"{s/1024/1024:.1f}MB" if s > 1024 * 1024 else f"{max(1, round(s/1024))}KB"


def nice(name):
    return name.replace("(권준구 강의안 스타일)", "(강의안 스타일)")


MISSING = []


def shotpath(shot):
    """'files:이름' = 계정 이름을 가린 사본(assets/files/), 그 밖은 assets/shot/ 아래"""
    return "assets/files/" + shot[6:] if shot.startswith("files:") else SHOT + shot


def img(src, alt, cls="guide-shot", lazy=True):
    if not exists(src):
        MISSING.append(src)
    return (f'<figure class="{cls}"><a href="{url(src)}" target="_blank" rel="noopener">'
            f'<img src="{url(src)}" alt="{E(alt)}"{" loading=\"lazy\"" if lazy else ""} /></a></figure>')


# ------------------------------------------------------------------ 작은 부품
def key_block(title, lead, items, foot=None, cols=None):
    cells = "".join(f'<div class="key-item"><span class="key-label">{E(a)}</span><p class="key-text">{b}</p></div>' for a, b in items)
    st = f' style="grid-template-columns:repeat({cols},1fr)"' if cols else ""
    return (f'<div class="guide-key"><h3>{E(title)}</h3>' + (f'<p class="key-lead">{lead}</p>' if lead else "")
            + f'<div class="key-grid"{st}>{cells}</div>' + (f'<p class="key-foot">{foot}</p>' if foot else "") + "</div>")


def steps(items):
    out = []
    for i, (t, d, shot) in enumerate(items, 1):
        sh = img(shotpath(shot), t + " 화면") if shot else ""
        out.append(f'<li class="guide-step"><div class="guide-head"><span class="guide-no">{i}</span><div>'
                   f'<p class="guide-title">{E(t)}</p><p class="guide-desc">{d}</p></div></div>{sh}</li>')
    return f'<ol class="guide g{min(len(items), 4) if len(items) != 6 else 3}">{"".join(out)}</ol>'


def copy_row(cat, text, tail=""):
    t = f'<span class="ptail">{E(tail)}</span>' if tail else ""
    return (f'<div class="prompt-row"><span class="pcat{" long" if len(cat) > 2 else ""}">{E(cat)}</span><div class="pbody">{t}'
            f'<span class="ptext">{E(text)}</span></div><button class="prompt-copy" type="button">복사</button></div>')


EXT_ICON = {".hwpx": "HWPX", ".hwp": "HWP", ".xlsx": "XLSX", ".pptx": "PPTX", ".pdf": "PDF", ".md": "MD", ".txt": "TXT", ".png": "PNG", ".mp4": "MP4"}


def file_card(path_rel, label, subj):
    ext = os.path.splitext(path_rel)[1].lower()
    name = os.path.basename(path_rel)
    if not exists(path_rel):
        MISSING.append(path_rel)
    return (f'<div class="file-card"><span class="file-icon ext">{EXT_ICON.get(ext, "FILE")}</span><div class="file-body">'
            f'<p class="file-subj">{E(subj)}</p><p class="file-title">{E(label)}</p></div>'
            f'<a class="btn btn-primary btn-sm" href="{url(path_rel)}" download="{E(nice(name))}">받기 ↓</a></div>')


def preview_grid(entries):
    """entries: [(키, 쪽수, 이름, 파일경로 or None)]"""
    figs = []
    for key, pages, label, fpath in entries:
        for p in range(1, pages + 1):
            png = f"assets/files/{key}.png" if p == 1 else f"assets/files/{key}_{p}.png"
            if not exists(png):
                if p == 1:
                    MISSING.append(png)
                continue
            pg = f" · {p}쪽" if pages > 1 else ""
            dl = f' · <a href="{url(fpath)}" download="{E(nice(os.path.basename(fpath)))}">파일 받기 ↓</a>' if fpath and p == 1 and not fpath.endswith("다운로드_흉내") else ""
            figs.append(f'<figure class="file-shot"><a class="fs-img" href="{url(png)}" target="_blank" rel="noopener">'
                        f'<img src="{url(png)}" alt="{E(label)} 미리보기{pg}" loading="lazy" /></a>'
                        f'<figcaption><strong>{E(label)}{pg}</strong><a href="{url(png)}" target="_blank" rel="noopener">크게 보기</a>{dl}</figcaption></figure>')
    return f'<div class="shot-grid">{"".join(figs)}</div>'


def yt(vid, title, short=False, start=None):
    thumb = f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
    src = f"https://www.youtube.com/embed/{vid}?autoplay=1" + (f"&start={start}" if start else "")
    return (f'<div class="yt-item{" short" if short else ""}"><button class="yt-embed yt-lazy" type="button" data-src="{src}" aria-label="{E(title)} 재생">'
            f'<img src="{thumb}" alt="" loading="lazy" /><span class="yt-play" aria-hidden="true">▶</span></button>'
            f'<p class="yt-cap">{E(title)}</p>'
            f'<div class="prompt-row yt-link"><span class="ptext">https://www.youtube.com/{"shorts/" if short else "watch?v="}{vid}</span><button class="prompt-copy" type="button">링크 복사</button></div></div>')


def mix(title, body, tag=None, cls=""):
    return (f'<div class="guide-mix{" " + cls if cls else ""}">' + (f'<p class="mix-highlight">{tag}</p>' if tag else "")
            + f'<h3>{title}</h3>{body}</div>')


def lecture(sid, no, title, lead, tile, reverse, detail, actions=""):
    return f'''
    <section class="lecture" id="{sid}" aria-label="{E(re.sub("<[^>]+>", " ", title))}">
      <div class="lecture-row{" reverse" if reverse else ""}">
        <div class="lecture-media {tile}"><span class="lecture-no">{no}</span></div>
        <div class="lecture-copy">
          <p class="lecture-kicker">SECTION {no}</p>
          <h2>{title}</h2>
          <p class="lead">{lead}</p>
          <div class="lecture-actions">
            <button class="btn btn-secondary lecture-toggle" type="button" aria-expanded="false" aria-controls="d{sid}"></button>{actions}
          </div>
        </div>
      </div>
      <div class="lecture-detail" id="d{sid}">
        <div class="lecture-detail-inner">{detail}
        </div>
      </div>
    </section>'''


TILES = ["tile-code", "tile-image", "tile-write", "tile-notebook", "tile-eval", "tile-video", "tile-flow"]

# ------------------------------------------------------------------ 프롬프트 저장소
# 화면에 보일 때만 바꾸는 안내 문구 (원본 prompts/*.txt 는 그대로). 접근 가능한 폴더는 inlineAI_실습 하나만.
DISPLAY_FIX = {
    "inline AI 오른쪽 위 '접근 가능한 폴더'에 '다운로드_흉내' 폴더 추가 (파일은 안 열어도 됨)":
        "새 에이전트 → 입력창 + → 폴더 첨부하기 → '다운로드_흉내' (파일은 안 열어도 됨)",
}

def prompt_store(no):
    folder = FOLDERS[no]
    title, blocks = parse(read(os.path.join(ROOT, "prompts", folder + ".txt")))
    out = []
    lst = []

    def flush():
        if lst:
            out.append('<div class="prompt-list">' + "".join(lst) + "</div>")
            lst.clear()

    count = 0
    for b in blocks:
        if b[0] == "prompt":
            lst.append(copy_row(b[1], b[3], b[2].strip("() ")))
            count += 1
        elif b[0] == "head":
            flush()
            out.append(f'<p class="guide-title store-head">{E(b[1])}</p>')
        else:
            flush()
            s = b[1]
            if s.startswith("※ 시작 전"):
                continue  # 하네스는 inlineAI_실습 안에 있어 따로 추가할 필요 없음(폴더는 하나만 초대)
            for a, z in DISPLAY_FIX.items():
                s = s.replace(a, z)
            if s.startswith("준비") or s.startswith("[") and "열고" in s:
                out.append(f'<p class="prep"><span class="prep-tag">준비</span>{E(re.sub(r"^준비\s*:\s*", "", s).strip("[]"))}</p>')
            elif s.startswith("※") or s.startswith("(※"):
                out.append(f'<p class="store-note">{E(s)}</p>')
            else:
                out.append(f'<p class="store-note">{E(s)}</p>')
    flush()
    return "".join(out), count


# ------------------------------------------------------------------ 실습 섹션 내용 (01~08)
S = {
 "01": dict(title="다운로드<br />폴더 정리", lead="파일을 하나도 안 열어도 돼요. 폴더째 맡기면 AI가 종류별로 세고, 정리할 표부터 보여 줘요.",
   keys=("이것만 기억해요", "폴더를 <strong>통째로</strong> 맡기고, 옮기기 전에 <strong>표부터</strong> 받아요.",
         [("폴더째 맡기기", "파일은 열지 않고 <strong>폴더 첨부하기</strong>로 다운로드_흉내만 붙여요."),
          ("표 먼저", "<strong>'원래 이름 → 옮길 폴더'</strong> 표를 보고 좋으면 그때 옮겨요."),
          ("추측은 추측", "어느 게 최신인지는 AI도 <strong>이름만 보고 추측</strong>해요.")]),
   open=("폴더 붙이기", "<strong>새 에이전트</strong> → 입력창 <strong>+</strong> → <strong>폴더 첨부하기</strong> → <strong>다운로드_흉내</strong>를 골라요.", "inline/04_attach_menu_1280.png"),
   check="종류별 개수 표가 나와요. 합계가 <strong>55개</strong>인지, 캡처본_확인필요.hwpx가 <strong>한글</strong>로 세어졌는지 봐요.",
   save="표가 맞으면 <strong>'좋아, 옮겨 줘'</strong>. 탐색기에서 01_공문~99_확인필요 폴더가 생겼는지 확인해요.",
   before=("정리 전 — 실제 다운로드 폴더(911개)", "extra/01_downloads_before_1280.png"),
   traps=[("함정", "<strong>캡처본_확인필요.hwpx</strong>는 이름에 '캡처'가 있지만 한글 파일이에요."),
          ("55개 정답", "한글 25 · PDF 3 · 엑셀 11 · 사진 4 · 기타 12 (odt 10개는 공문 본문)"),
          ("최신 파일", "파일 시각이 모두 같아요. AI가 <strong>'확실하지 않다'</strong>고 말하면 정답이에요."),
          ("사진", "0바이트 사진은 열 수 없어요 → 99_확인필요. 비슷한 이름도 서로 다른 나라 사진이에요.")]),
 "02": dict(title="가정통신문<br />양식 맞추기", lead="예쁘게가 아니라 우리 학교 양식 그대로. 메모만 주면 가정통신문이 돼요.",
   keys=("이것만 기억해요", "열린 양식은 그대로 두고 <strong>내용만</strong> 바꿔 달라고 해요.",
         [("양식 그대로", "머리 표·제목 상자·현황 표·학교장 자리는 <strong>그대로</strong> 둬요."),
          ("새 이름 저장", "원본은 두고 <strong>가정통신문_디지털시민교육.hwpx</strong>로 저장해요."),
          ("[확인 필요]", "메모에 없는 내용은 지어내지 말고 <strong>[확인 필요]</strong>로.")]),
   open=("양식 열고 메모 붙이기", "<strong>오현교육통신_양식</strong>을 한글로 열고 <strong>한/글 편집하기</strong>. <strong>보낼내용_메모.hwpx</strong>는 채팅창에 끌어다 놓아요.", "inline/03a_hangul_edit_window_1280.png"),
   check="AI가 먼저 계획을 보여 줘요. 공사 이야기가 빠졌는지, 날짜가 바뀌었는지 읽고 <strong>이어서 작업하기</strong>.",
   save="같은 폴더에 <strong>새 파일</strong>이 생겼는지, 원본 양식은 그대로인지 확인해요.",
   traps=[("오답 1", "맨 위 <strong>〈겨울방학 공사 안내장〉</strong> 라벨, 공사 표·공사 당부가 남아 있으면 오답이에요."),
          ("오답 2", "날짜 <strong>2025. 12. 29.</strong>, '새해 복 많이' 인사가 6월 통신문에 남으면 오답이에요."),
          ("부서", "양식은 <strong>행정실</strong>, 메모는 <strong>정보부</strong>. AI가 묻거나 [확인 필요]로 두면 좋아요."),
          ("날짜", "6. 15.(월)~6. 19.(금), 회신 6. 19.(금) 모두 맞아요. 학생의 날 문서는 <strong>틀린 곳이 없어요</strong> — 오류를 지어내지 않는지 봐요.")]),
 "03": dict(title="한글<br />표 만들기", lead="줄글을 표로 바꾸는 일, 한 줄이면 돼요. 표 모양과 정렬 기준만 말해 주세요.",
   keys=("이것만 기억해요", "표의 <strong>칸 이름</strong>과 <strong>정렬 기준</strong>을 같이 말해요.",
         [("칸 이름", "'담당 | 맡은 일 | 마감일 | 비고'처럼 <strong>칸을 정해</strong> 줘요."),
          ("정렬", "<strong>마감 빠른 순</strong>처럼 순서 기준을 줘요."),
          ("빈칸", "비워 두지 말고 <strong>'미제출'</strong>처럼 채우라고 해요.")]),
   open=("파일 열기", "<strong>새 에이전트</strong>로 시작하고 <strong>표로_만들_자료.hwpx</strong>를 한글로 열어요.", "inline/03a_hangul_edit_window_1280.png"),
   check="한글 창에 표가 들어와요. 맨 위가 <strong>6/3 4반 담임</strong>, 맨 아래가 <strong>6/10 3반 담임</strong>인지 봐요.",
   save="표 글꼴(④)까지 맞췄으면 <strong>다른 이름으로 저장</strong>해 원본을 남겨요.",
   traps=[("업무분장", "마감 빠른 순: 6/3 4반 → 6/4 학년부장 → 6/5 1반 → 6/8 2반 → 6/10 3반"),
          ("일정표", "수요일 '동의서 마감', 금요일 '현장체험학습'은 <strong>교시가 없어요</strong>. 어디에 넣는지 봐요."),
          ("명렬표", "<strong>미제출 5명 / 전체 26명</strong> (3·7·12·17·22번)"),
          ("시수표", "연간 합계 <strong>455시간</strong>. 원본 '계' 칸은 계산식이라 AI가 못 읽을 수 있어요.")]),
 "04": dict(title="작년 문서<br />업데이트", lead="작년 문서는 바꿀 곳 목록부터 받으면 안전해요. 메모대로만 고치게 해요.",
   keys=("이것만 기억해요", "<strong>목록 먼저</strong>, 고치는 건 그다음이에요.",
         [("목록 먼저", "'바꿔야 할 곳을 <strong>목록으로만</strong>. 아직 고치지 마.'"),
          ("메모대로만", "메모에 없는 숫자는 <strong>[확인 필요]</strong>로 남겨요."),
          ("비교표 보고", "'항목 | 작년 | 올해' 표로 <strong>교감 선생님 보고</strong>까지.")]),
   open=("파일 열고 메모 붙이기", "<strong>2025년 … 신청서(작년).hwpx</strong>를 한글로 열고, <strong>2026_디지털튜터_변경사항_메모</strong>를 첨부해요.", "inline/04_attach_menu_1280.png"),
   check="바꿔야 할 곳 목록이 먼저 나와요. 본문의 <strong>715명</strong>, 표 아래 실적 연도까지 들어 있는지 봐요.",
   save="<strong>2026년 … 신청서.hwpx</strong> 새 파일이 생겼는지, '(작년)' 원본은 그대로인지 확인해요.",
   traps=[("학생 수", "<strong>715 → 711명</strong>. 바뀌는 건 1·3·4학년뿐, 본문의 '715명'도 같이 바뀌어야 해요."),
          ("일괄 바꾸기 금지", "<strong>2025 실적</strong>은 2025 그대로예요. '2025 → 2026' 일괄 바꾸기는 오답."),
          ("[확인 필요]", "교원 수·기기 수·신청 날짜는 메모에 없어요 → [확인 필요]."),
          ("숨은 오류", "예산 합계 칸 27,000 ↔ 항목 합 2,700(천원). 고치지 말고 <strong>지적만</strong>. 소방훈련은 '2024년도' 한 곳만 고쳐요.")]),
 "05": dict(title="행정 처리<br />도움받기", lead="틀린 금액은 AI가 찾고, 마지막 확인은 내 눈으로. 엑셀은 꼭 MS 엑셀로 열어요.",
   keys=("이것만 기억해요", "계산은 <strong>식으로</strong>, 못 맞추면 <strong>못 맞춘다고</strong>.",
         [("계산식", "금액 칸을 <strong>단가×수량 식</strong>, 합계는 <strong>SUM 식</strong>으로."),
          ("억지 금지", "조건 안에서 안 되면 <strong>얼마가 모자라는지</strong> 말하게 해요."),
          ("산출 내역", "<strong>1,500원 × 98개 = 147,000원</strong> 같은 품의 문장으로.")]),
   open=("엑셀 열기", "<strong>체험학습_예산표.xlsx</strong>를 <strong>MS 엑셀</strong>로 열고 inline AI를 옆에 둬요. (한셀은 안 돼요)", "inline/modes/doc_02_excel_and_inline_side_by_side_1280.png"),
   check="다른 줄 <strong>두 곳</strong>(보험·물티슈)을 찾았는지, 차이 금액이 맞는지 봐요.",
   save="고친 금액 칸에 <strong>=단가*수량</strong> 식이 보이는지 확인하고 새 이름으로 저장해요.",
   traps=[("① 틀린 곳", "보험 <strong>1,600원</strong>, 물티슈 <strong>72,000원</strong> 적게 적힘 → 정정 합계 1,355,100원"),
          ("② 정답은 '못 맞춤'", "조건을 지키면 최소 <strong>14,600원 부족</strong>. 억지로 맞추면 오답이에요."),
          ("④ 0원", "포스트잇 <strong>128개</strong> · 클립 <strong>60개</strong> → 잔액 0원"),
          ("⑥⑦ 견적", "교구 <strong>2,586,270원</strong>(금 이백오십팔만육천이백칠십원정). 버스는 행선지 3곳, <strong>6대</strong>, 3,000,000원.")]),
 "06": dict(title="계획서로<br />기안문 쓰기", lead="계획서 하나와 예시 하나면 기안문이 나와요. 날짜 검사부터 시켜요.",
   keys=("이것만 기억해요", "<strong>날짜 먼저</strong>, 형식은 <strong>예시 그대로</strong>.",
         [("날짜 검사", "쓰기 전에 <strong>날짜·요일·연도</strong>부터 확인해요(②번 먼저)."),
          ("예시 형식", "제목 / 1. 관련 / 2. 가~마 / 붙임 / <strong>끝.</strong>"),
          ("없는 건 비우기", "관련 공문·세부 예산은 지어내지 말고 <strong>[확인 필요]</strong>.")]),
   open=("파일 열고 예시 붙이기", "<strong>2025학년도 오현 AI 과학의 날 운영계획</strong>을 열고 <strong>기안문_본문_예시.hwpx</strong>를 첨부해요.", "inline/04_attach_menu_1280.png"),
   check="②번으로 이상한 날짜를 먼저 짚어 받아요. <strong>2024. 4. 18.</strong>을 찾았는지 봐요.",
   save="①번으로 <strong>기안문_오현AI과학의날.hwpx</strong> 새 파일이 생겼는지 확인해요.",
   traps=[("연도 오기", "일시 <strong>2024. 4. 18.</strong> → <strong>2025. 4. 18.(금)</strong>. 2024년 4월 18일은 목요일이에요."),
          ("오타", "'9;00'(쌍반점), '간의 의자' → 지적하면 가산점"),
          ("빈 예산 표", "세부 예산은 비어 있어요. 총액 <strong>9,000,000원</strong>만 쓰고 세부는 지어내면 오답."),
          ("소방훈련 기안", "계획서 4번 제목의 <strong>'2024년도'</strong>를 기안문에 옮겨 쓰면 오답이에요.")]),
 "07": dict(title="계획서로<br />보고서 쓰기", lead="계획서·메모·엑셀 셋을 주면 결과 보고서 양식이 채워져요. 숫자는 AI에게 다시 검산시켜요.",
   keys=("이것만 기억해요", "근거는 <strong>첨부한 자료만</strong>, 숫자는 <strong>엑셀로 계산</strong>.",
         [("근거는 첨부만", "계획서·메모·엑셀에 없는 내용은 <strong>[확인 필요]</strong>."),
          ("숫자는 엑셀로", "참여율·만족도는 <strong>엑셀 숫자로 계산</strong>해서 넣어요."),
          ("검산 시키기", "③번: '항목 | 보고서 | 원래 자료 | 맞음/틀림' 표.")]),
   open=("양식 열고 자료 셋 붙이기", "<strong>결과보고서_양식.hwpx</strong>를 열고 계획서·메모·엑셀 <strong>3개를 한 번에</strong> 첨부해요.", "inline/modes/edit_hwp_03_panel_1280.png"),
   check="양식 칸이 하나씩 채워져요. 평균 참여율 <strong>94.0%</strong>, 최저 <strong>5회 70%</strong>가 맞는지 봐요.",
   save="새 이름 보고서 파일이 생겼는지 확인하고, ③번으로 숫자를 한 번 더 검산해요.",
   traps=[("참여율", "188/200 → 평균 <strong>94.0%</strong>, 최저 <strong>5회(6/27) 70%</strong>"),
          ("만족도", "긍정 비율 <strong>90 · 80 · 80 · 90%</strong>"),
          ("예산", "집행 1,270,000원 / 계획 1,300,000원 → 집행률 <strong>97.7%</strong>"),
          ("수상안전", "계획의 8. 19.~8. 26.이 아니라 실제 <strong>7. 7.(월)~7. 11.(금)</strong>을 써야 해요.")]),
 "08": dict(title="계획서·통계로<br />PPT 만들기", lead="같은 자료를 학교 PPT 양식에 담아요. 스타일 가이드를 주면 결과가 확 달라져요.",
   keys=("이것만 기억해요", "<strong>양식</strong>을 주고, <strong>숫자는 엑셀 그대로</strong>.",
         [("학교 양식", "남색 제목 띠·맑은 고딕 양식을 <strong>열어 두고</strong> 시켜요."),
          ("엑셀 그대로", "그래프 숫자는 <strong>엑셀 값 그대로</strong> 넣게 해요."),
          ("스타일 가이드", "가이드와 참고 PDF를 주면 <strong>같은 스타일</strong>로 만들어요.")]),
   open=("양식 열고 자료 붙이기", "<strong>우리학교_PPT_양식.pptx</strong>를 열고 계획서·메모·엑셀을 첨부해요.", "inline/04_attach_menu_1280.png"),
   check="PPT는 1~2분 걸려요. 기다리는 동안 아래 정답을 봐요. <strong>남색 제목 띠 · 8장 이내</strong>인지 확인해요.",
   save="<strong>동아리_결과발표.pptx</strong>를 열어 막대그래프 5회가 <strong>70%</strong>인지 봐요.",
   traps=[("참여율 막대", "100 · 95 · 100 · 90 · <strong>70</strong> · 100 · 95 · 100 · 90 · 100 (%)"),
          ("만족도", "<strong>90 · 80 · 80 · 90%</strong>, 집행률 97.7%"),
          ("글꼴", "Black Han Sans·Pretendard가 없으면 <strong>대체 글꼴을 알려 주는지</strong> 봐요."),
          ("공문 PPT", "운영기간(2026. 4.~2027. 1.)을 대회 기간으로 착각하면 오답. 응모 마감 <strong>5. 15.(금) 18:00</strong>.")]),
}


def practice_section(no, idx):
    d = S[no]
    folder = FOLDERS[no]
    zip_rel = f"download/폴더별/{folder}.zip"
    if not exists(zip_rel):
        MISSING.append(zip_rel)
    store, n = prompt_store(no)
    items = FILES[no]
    mains = [x for x in items if x[0] in ("main", "extra")]
    answers = [x for x in items if x[0] == "answer"]

    def fp(rel):
        return f"materials/{folder}/{rel}"

    parts = []
    parts.append(key_block(*d["keys"]))
    if d.get("before"):
        cap, shot = d["before"]
        parts.append(mix("이렇죠? 선생님 다운로드 폴더도", f'<p class="mix-lead">강사 컴퓨터의 진짜 다운로드 폴더예요. 파일 이름은 가렸어요.</p>{img(SHOT + shot, cap, "guide-shot md")}', "정리 전"))
    st = [d["open"], ("프롬프트 붙여 넣기", "아래 <strong>프롬프트 저장소</strong>에서 ①번 <strong>[복사]</strong> → 입력창에 <strong>Ctrl+V</strong> → 보내기.",
                      "files:shot_03_input_example_1280.png" if no == "01" else None),
          ("결과 확인", d["check"], "inline/15_plan_then_continue_1280.png" if no == "02" else None),
          ("새 이름으로 저장", d["save"], None)]
    parts.append(f'<h3 class="sec-h">이 순서로 해요</h3>{steps(st)}')

    # 실습 파일 내려받기 + 미리보기
    cards = []
    seen = set()
    for role, rel, key, pages, label in mains:
        if rel == "다운로드_흉내" or rel in seen:
            continue
        seen.add(rel)
        cards.append(file_card(fp(rel), label, "추가 실습" if role == "extra" else "실습 파일"))
    if no == "01":
        cards.append(f'<div class="file-card"><span class="file-icon ext">DIR</span><div class="file-body"><p class="file-subj">실습 폴더</p>'
                     f'<p class="file-title">다운로드_흉내 (파일 {len(os.listdir(os.path.join(M, folder, "다운로드_흉내")))}개 · 대부분 0바이트 흉내 파일)</p></div>'
                     f'<a class="btn btn-primary btn-sm" href="{url(zip_rel)}" download>zip ↓</a></div>')
    body = (f'<p class="mix-lead">한 파일씩 받아도 되고, 이 실습 폴더만 zip으로 받아도 돼요. 바탕화면 <strong>inlineAI_실습</strong> 폴더 안에 풀어 주세요.</p>'
            f'<div class="practice-download row"><a class="btn btn-primary" href="{url(zip_rel)}" download>이 실습 파일만 받기 (zip · {kb(zip_rel)}) ↓</a></div>'
            f'<div class="arcade-files">{"".join(cards)}</div>'
            f'<p class="guide-title sub">파일 미리보기</p><p class="mix-lead">눌러서 크게 볼 수 있어요.</p>'
            + preview_grid([(k, pg, lb, fp(r)) for _, r, k, pg, lb in mains]))
    parts.append(mix("실습 파일", body, "📂 내려받기"))

    parts.append(mix(f"프롬프트 저장소 · {n}개",
                     f'<p class="mix-lead">프롬프트는 여기서 <strong>[복사]</strong> → inline AI 입력창에 <strong>Ctrl+V</strong> → 보내기. 실습이 바뀌면 <strong>새 에이전트</strong>로 시작해요.</p>{store}'
                     '<p class="store-note offline">인터넷이 안 될 때만: 실습 자료의 <a href="materials/00_%ED%94%84%EB%A1%AC%ED%94%84%ED%8A%B8_%EC%A0%84%EC%B2%B4.txt" download><strong>00_프롬프트_전체.txt</strong></a>에 같은 내용이 있어요.</p>',
                     "📋 복사해서 쓰기", "store"))

    tr = "".join(f'<div class="note-card"><span class="trap-tag">{E(a)}</span><p class="mix-lead">{b}</p></div>' for a, b in d["traps"])
    parts.append(mix("정답 미리보기",
                     '<p class="mix-lead">AI 결과와 나란히 놓고 비교해 보세요. 정답 파일도 받을 수 있어요.</p>'
                     + preview_grid([(k, pg, lb, fp(r)) for _, r, k, pg, lb in answers])
                     + f'<p class="guide-title sub">이런 곳을 봐요 — 함정</p><div class="note-cards">{tr}</div>',
                     "✅ 정답"))
    acts = f'<a class="btn btn-primary" href="{url(zip_rel)}" download>파일 받기 ↓</a>'
    return lecture(f"s{no}", no, d["title"], d["lead"], TILES[idx % len(TILES)], idx % 2 == 1, "".join(parts), acts)


# ------------------------------------------------------------------ 00 준비
def prep_section():
    short = read(os.path.join(M, "00_하네스_공문서", "01_메타프롬프트_짧은판.txt")).strip()
    full = read(os.path.join(M, "00_하네스_공문서", "02_메타프롬프트_전체판.txt")).strip()
    login = (glob.glob(os.path.join(ROOT, "assets", "shot", "extra", "*login*_1280.png")) + glob.glob(os.path.join(ROOT, "assets", "shot", "extra", "*login*.png")))
    invite = (glob.glob(os.path.join(ROOT, "assets", "shot", "extra", "*invit*_1280.png")) + glob.glob(os.path.join(ROOT, "assets", "shot", "extra", "*invit*.png")))
    rel = lambda p: os.path.relpath(p, os.path.join(ROOT, "assets", "shot")).replace(os.sep, "/") if p else None
    login_shot = rel(login[0]) if login else "inline/02_home_1280.png"
    invite_shot = rel(invite[0]) if invite else None
    hz = "download/폴더별/00_하네스_공문서.zip"
    parts = []
    parts.append(key_block("로컬이라 좋은 점", "inline AI는 웹 채팅이 아니라 <strong>내 컴퓨터에 깔려서</strong> 파일을 직접 열어요.",
                           [("용량", "<strong>큰 파일도 OK</strong>. 채팅창 올리기 제한에 덜 걸려요."),
                            ("여러 파일", "계획서·예산표·통신문을 <strong>한 번에</strong> 읽고 맞춰 봐요."),
                            ("일괄", "폴더 하나를 맡겨 <strong>50개도 한꺼번에</strong> 정리해요.")],
                           "파일은 내 컴퓨터에 두고 필요한 부분만 읽어요. 그래도 학생 실명·연락처가 든 진짜 파일은 쓰지 마세요."))
    parts.append(key_block("에이전트 AI라서", "묻는 말에 답만 하는 챗봇이 아니에요. <strong>일을 맡기는</strong> AI예요.",
                           [("알아서", "시켜 두면 문서를 <strong>열고 고치고 저장</strong>해요. 그동안 다른 일을 해요."),
                            ("누적", "결과가 폴더에 <strong>쌓여서</strong> 다음 달엔 그 위에 이어 가요."),
                            ("맥락", "학교 양식·규칙·작년 문서가 모이면 그게 AI의 <strong>맥락</strong>이 돼요.")]))
    st = [
        ("설치", "<a href=\"https://inline-ai.com\" target=\"_blank\" rel=\"noopener\">inline-ai.com</a> → 위쪽 <strong>개인용</strong> → <strong>Windows용 다운로드</strong> → 받은 파일 두 번 클릭.<br />막히면: 마우스 오른쪽 <strong>관리자 권한으로 실행</strong> · 파란 창은 <strong>추가 정보 → 실행</strong> · 와이파이가 느리면 핫스팟.", "inline/01_install_site_personal_1280.png"),
        ("로그인", "inline AI를 켜고 계정을 만들거나 로그인해요. 가운데 <strong>입력창</strong>이 보이면 성공. 아래 일 버튼(학교 업무 등)은 누르면 바로 실행되니 <strong>구경만</strong>.", login_shot),
        ("초대 코드", "<a href=\"https://portal.inline-ai.com/invitation-promotion?code=K2YERY3H\" target=\"_blank\" rel=\"noopener\">초대 링크</a>로 들어가거나 앱 위쪽 <strong>초대 이벤트</strong>에 코드 <strong>K2YERY3H</strong>. 무료 <strong>1,000 크레딧</strong>을 더 받아요.", invite_shot),
        ("폴더는 하나만 초대", "오른쪽 위 네모(<strong>작업 패널</strong>) → <strong>접근 가능한 폴더</strong> → <strong>폴더 추가…</strong> → 바탕화면 <strong>inlineAI_실습</strong> 하나만 골라요.<br /><strong>다른 폴더 · 바탕화면 전체 · 다운로드 폴더는 등록하지 마세요.</strong> (그림은 강사 PC라 Desktop이 보여요)", "files:shot_07_work_panel_1280.png"),
        ("승인 모드는 확인만", "입력창 아래가 <strong>모든 편집 허용하기</strong>로 되어 있는지 확인만 해요. 그대로 둬요. 대신 폴더를 실습 폴더 하나로 막아 두고, 고치기 전에 목록을 먼저 받아요.", "inline/modes/edit_hwp_01_window_1280.png"),
        ("지시사항 붙이기", "아래 <strong>짧은판</strong>을 이 사이트에서 <strong>[복사]</strong> → 왼쪽 아래 내 이름 → <strong>설정 → 일반 설정 → inline AI 지시사항</strong>에 <strong>Ctrl+V</strong>. 모든 대화에 적용돼요.", "files:shot_11_settings_general_1280.png"),
    ]
    parts.append(f'<h3 class="sec-h">여섯 단계면 준비 끝</h3>{steps(st)}')
    parts.append(mix("프롬프트는 이 사이트에서 복사해요",
                     '<p class="mix-lead">실습마다 <strong>[펼치기]</strong> → 프롬프트 저장소의 <strong>[복사]</strong> → inline AI 입력창에 <strong>Ctrl+V</strong>. 한 페이지로 모아 둔 <a href="prompts.html"><strong>프롬프트 모음</strong></a>도 있어요.</p>'
                     + img(SHOT + "extra/00_prompts_page_1280.png", "프롬프트 모음 화면 — 복사 버튼", "guide-shot md"), "📋 복사 버튼"))
    parts.append(mix("지시사항 — 메타 프롬프트 짧은판",
                     '<p class="mix-lead">복사해서 <strong>설정 → 일반 설정 → inline AI 지시사항</strong>에 한 번만 붙여 넣어요. 연수가 끝나면 지워도 돼요.</p>'
                     f'<div class="prompt-list">{copy_row("★ 짧은판", short)}</div>', "📋 복사해서 쓰기", "store"))
    parts.append(key_block("안전장치 세 가지", "승인 모드는 '모든 편집 허용하기' 그대로. 대신 이 세 가지로 지켜요.",
                           [("폴더 하나만", "접근 가능한 폴더는 <strong>inlineAI_실습 하나</strong>. 그 밖은 AI가 못 봐요."),
                            ("원본은 새 이름", "프롬프트마다 <strong>'새 이름으로 저장'</strong>이 들어 있어요."),
                            ("목록 먼저", "'고치기 전에 <strong>목록으로 먼저</strong> 보여 줘. 아직 고치지 마.'")],
                           "오늘의 약속: 실습이 바뀌면 <strong>새 에이전트</strong> · 한글 파일은 <strong>하나만</strong> 열기 · 엑셀은 <strong>MS 엑셀</strong> · 모델은 <strong>자동</strong> 그대로"))
    hz_items = [("01 짧은판", "지시사항에 붙여 <strong>매번 같은 규칙</strong>으로"),
                ("02 전체판", "중요한 문서 때 첫 메시지에 같이 → <strong>계획 먼저·검수까지</strong>"),
                ("03 표기 규칙", "날짜·시간·금액 <strong>형식이 틀리는</strong> 오류를 막아요"),
                ("04 학교 정보", "학급 수·부서·담당자를 <strong>지어내는</strong> 오류를 막아요"),
                ("05 날짜요일표", "2026년 <strong>요일 실수</strong>를 막아요"),
                ("06 문서별 틀", "기안문·통신문의 <strong>순서 빠뜨림</strong>을 막아요"),
                ("07 체크리스트", "다 쓴 뒤 <strong>스스로 점검</strong>하게 해요")]
    body = ('<p class="mix-lead">AI가 일하기 전에 먼저 읽는 <strong>업무 매뉴얼</strong>이에요. inlineAI_실습 안에 들어 있어서 폴더를 초대하면 같이 들어가요. '
            '우리 학교에 쓸 땐 <strong>04 학교기본정보</strong>만 고치면 돼요.</p>'
            f'<div class="key-grid hz">{"".join(f"<div class=\"key-item\"><span class=\"key-label\">{E(a)}</span><p class=\"key-text\">{b}</p></div>" for a, b in hz_items)}</div>'
            f'<div class="practice-download row"><a class="btn btn-primary" href="{url(hz)}" download>하네스 폴더만 받기 (zip · {kb(hz)}) ↓</a></div>'
            '<p class="mix-lead">쓰는 법은 한 줄: <strong>"00_하네스_공문서 폴더의 규칙을 따라서, 열려 있는 계획서로 기안문 본문을 써 줘."</strong></p>'
            f'<div class="prompt-list">{copy_row("02 전체판", full, "중요한 문서를 맡길 때 첫 메시지에 함께")}</div>')
    parts.append(mix("00_하네스_공문서 — AI의 업무 매뉴얼", body, "🧭 하네스"))
    acts = '<a class="btn btn-primary" href="https://inline-ai.com" target="_blank" rel="noopener">inline AI 받기 ↗</a>'
    return lecture("s00", "00", "준비하기<br />AI를 내 컴퓨터에", "설치부터 폴더 초대, 지시사항까지. 여섯 단계면 끝나요.", "tile-flow", False, "".join(parts), acts)


# ------------------------------------------------------------------ 09 클로드 코워크
def cowork_section():
    cmp = [("폴더 초대", "접근 가능한 폴더", "프로젝트 또는 폴더 → 폴더 추가", "같음"),
           ("고치기 전 확인", "편집 전 확인하기", "수동 승인", "같음"),
           ("늘 쓰는 규칙", "inline AI 지시사항", "Claude 지침 · 프로젝트 지침 · 스킬", "같음"),
           ("스킬 · 예약 · 커넥터", "—", "있음", "코워크만"),
           ("한글 직접 편집", "한/글 편집하기", "hwp 출력 없음 [확인 필요]", "inline AI"),
           ("요금", "무료로 시작", "유료(Pro 이상)", "요금 확인")]
    rows = "".join(f'<tr><th>{E(a)}</th><td>{E(b)}</td><td>{E(c)}</td><td><span class="bd">{E(d)}</span></td></tr>' for a, b, c, d in cmp)
    parts = []
    parts.append(key_block("상위 호환 — 오늘 습관이 그대로 통해요", "일단 던지기 · 내 컴퓨터에 초대 · 양식 주기는 같고, <strong>프로젝트·스킬·예약·커넥터</strong>가 더해져요.",
                           [("오늘 한 일 그대로", "폴더 정리 · 양식 맞추기 · 문서 쓰기를 <strong>같은 한 줄</strong>로"),
                            ("스킬", "00_하네스를 <strong>스킬로 올리면</strong> 늘 같은 규칙으로"),
                            ("예약", "<strong>매주 월요일 아침</strong> 같은 때 알아서")],
                           "솔직히: 한글 직접 편집은 inline AI가 더 편하고, 코워크는 <strong>유료(Pro 이상)</strong>예요."))
    parts.append(mix("inline AI ↔ 클로드 코워크", f'<div class="table-wrap"><table class="cmp"><thead><tr><th></th><th>inline AI</th><th>클로드 코워크</th><th></th></tr></thead><tbody>{rows}</tbody></table></div>', "비교"))
    parts.append(mix("전정선 선생님 영상 — 교사를 위한 클로드",
                     '<p class="mix-lead">채널 교육티타임의 실시간 강의 다시보기예요. 눌러야 재생돼요. 대표 영상의 코워크 소개는 <strong>약 37:40</strong>, 폴더 지정·공문 정리는 <strong>약 53:50</strong>쯤이에요(추정).</p>'
                     '<div class="yt-grid">'
                     + yt("HmBVZ_679Ko", "대표 · 교사를 위한 최신 클로드 활용법 (2026. 7. 1.)")
                     + yt("AFVEpW0-X8U", "보조 · 클로드 코워크 실전 활용법 (2026. 7. 15.)")
                     + yt("AgLuARcXnbI", "보조 · 교사 업무, 코워크로 어디까지? (2026. 10. 1.)") + "</div>", "▶ 영상"))
    st = [("내려받기", "<a href=\"https://claude.ai/download\" target=\"_blank\" rel=\"noopener\">claude.ai/download</a> → <strong>Windows용 다운로드</strong>.", "claude/01_download_page_1280.png"),
          ("시작하기 · 로그인", "<strong>시작하기</strong> → Google 또는 이메일로 로그인. 코워크는 <strong>Pro 이상</strong> 계정이어야 해요.", "claude/03_login_1280.png"),
          ("Cowork · 폴더 추가", "입력창에서 <strong>Cowork</strong>를 고르고 <strong>프로젝트 또는 폴더 → 폴더 추가</strong>로 inlineAI_실습을 골라요.", "claude/11_folder_pick_1280.png"),
          ("수동 승인", "입력창 아래 <strong>수동</strong> → <strong>수동 승인</strong>. 하나씩 승인하고 넘어가요.", "claude/13_permission_1280.png"),
          ("Claude 지침", "내 이름 → <strong>설정 → 계정 → Claude 지침</strong>에 짧은판을 붙여요.", "claude/32_settings_account_1280.png"),
          ("코드 실행 켜기", "<strong>설정 → 기능 → 클라우드 코드 실행 및 파일 생성</strong>을 켜요. 스킬에 필요해요.", "claude/34_settings_features_1280.png")]
    parts.append(f'<h3 class="sec-h">클로드 앱 준비</h3>{steps(st)}')
    sk = "download/클로드_스킬_school-official-docs.zip"
    seq = ('<div class="arcade-seq">'
           + f'<figure class="seq-item"><a href="{url(SHOT + "claude/23b_skills_mine_1280.png")}" target="_blank" rel="noopener"><img src="{url(SHOT + "claude/23b_skills_mine_1280.png")}" alt="사용자 지정 → 스킬 화면" loading="lazy" /></a><figcaption><strong>① 사용자 지정 → 스킬</strong>내 항목에서 오른쪽 + 추가</figcaption></figure>'
           + '<div class="seq-arrow" aria-hidden="true">&#8594;</div>'
           + f'<figure class="seq-item"><a href="{url(SHOT + "claude/24_skill_add_1280.png")}" target="_blank" rel="noopener"><img src="{url(SHOT + "claude/24_skill_add_1280.png")}" alt="스킬 추가 메뉴" loading="lazy" /></a><figcaption><strong>② 스킬 업로드</strong>추가 메뉴에서 고르기</figcaption></figure>'
           + '<div class="seq-arrow" aria-hidden="true">&#8594;</div>'
           + f'<figure class="seq-item"><a href="{url(SHOT + "claude/25_skill_upload_dialog_1280.png")}" target="_blank" rel="noopener"><img src="{url(SHOT + "claude/25_skill_upload_dialog_1280.png")}" alt="스킬 업로드 창" loading="lazy" /></a><figcaption><strong>③ zip 끌어다 놓기</strong>업로드 → 보안 검사</figcaption></figure>'
           + "</div>")
    for p in ("claude/23b_skills_mine_1280.png", "claude/24_skill_add_1280.png", "claude/25_skill_upload_dialog_1280.png"):
        if not exists(SHOT + p):
            MISSING.append(SHOT + p)
    if not exists(sk):
        MISSING.append(sk)
    body = ('<p class="mix-lead">00_하네스_공문서의 <strong>클로드_스킬용</strong> 폴더(SKILL.md + references)를 zip으로 올려요. 아래 zip은 바로 올릴 수 있게 묶어 두었어요.</p>'
            f'<div class="practice-download row"><a class="btn btn-primary" href="{url(sk)}" download>스킬 zip 받기 ({kb(sk)}) ↓</a></div>'
            + seq +
            '<ul class="plain-steps"><li><strong>내 항목</strong>에 <code>school-official-docs</code>가 보이면 성공</li>'
            '<li><strong>설정 → 기능 → 코드 실행 및 파일 생성</strong>이 켜져 있어야 스킬이 돌아가요</li>'
            '<li>"작년 계획서 올해로 바꿔 줘"처럼 시키면 스킬이 저절로 쓰여요</li>'
            '<li>마음에 드는 결과가 나오면 <strong>"스킬로 저장해 줘"</strong> 한 줄로 업무 매뉴얼이 남아요</li></ul>')
    parts.append(mix("하네스를 스킬로 올리기", body, "🧩 스킬"))
    parts.append(mix("예약 — 정해진 때 알아서",
                     '<p class="mix-lead">왼쪽 <strong>예약됨 → 새 작업</strong>으로 "매주 월요일 아침 다운로드 폴더 정리"처럼 맡겨요. 예시 카드는 누르면 바로 만들어질 수 있으니 구경만 해요.</p>'
                     + img(SHOT + "claude/22_scheduled_1280.png", "예약된 작업 화면", "guide-shot md"), "⏰ 예약"))
    acts = '<a class="btn btn-primary" href="https://claude.ai/download" target="_blank" rel="noopener">클로드 앱 받기 ↗</a>'
    return lecture("s09", "09", "클로드 코워크로<br />한 걸음 더", "오늘 익힌 습관이 그대로 통해요. 스킬·예약까지 더한 상위 호환이에요.", "tile-image", True, "".join(parts), acts)


# ------------------------------------------------------------------ 정리
def wrap_section():
    parts = []
    parts.append(key_block("오늘 한 일, 한 문장", "일단 던지고, 내 폴더로 초대하고, <strong>양식</strong>을 주세요.",
                           [("고치기 전 목록", "'목록 먼저, <strong>아직 고치지 마</strong>'"),
                            ("[확인 필요]", "모르는 건 <strong>지어내지 말고</strong> 표시"),
                            ("원본은 새 이름", "원본은 두고 <strong>새 파일</strong>로 저장")],
                           "학생 실명·연락처가 든 진짜 파일은 쓰지 않아요."))
    flow = ('<div class="arcade-flow">'
            '<div class="flow-step"><span class="flow-no">1</span><h4>출근해서 시켜 두기</h4><p>오늘 할 문서를 먼저 AI에게 맡겨요.</p></div>'
            '<div class="flow-arrow" aria-hidden="true">&#8594;</div>'
            '<div class="flow-step"><span class="flow-no">2</span><h4>수업 다녀오기</h4><p>그동안 AI들이 동시에 일해요.</p></div>'
            '<div class="flow-arrow" aria-hidden="true">&#8594;</div>'
            '<div class="flow-step"><span class="flow-no">3</span><h4>결과 보고 다듬기</h4><p>쉬는 시간에 열어 보고 "여기는 이렇게"만 말해요.</p></div></div>')
    parts.append(mix("내일부터 아침 루틴", '<p class="mix-lead">내가 다 쓰는 게 아니라, AI가 초안을 쓰고 나는 <strong>확인하고 다듬는</strong> 사람이 돼요.</p>' + flow, "☀️ 아침 루틴"))
    parts.append(key_block("여러 AI에게 동시에", "<strong>새 에이전트</strong>를 여러 개 열어 각각 다른 일을 맡겨요.",
                           [("에이전트 1", "<strong>가정통신문</strong> — 02 양식으로"),
                            ("에이전트 2", "그 행사 <strong>기안문</strong> — 06 예시로"),
                            ("에이전트 3", "견적서로 <strong>품의</strong> 산출 내역"),
                            ("에이전트 4", "단원 PDF로 <strong>수업 퀴즈</strong> 10문항, 정답은 따로")],
                           "주의: 한글 문서는 에이전트마다 <strong>다른 파일</strong>로(같은 파일을 둘이 고치면 엉켜요). 크레딧은 맡긴 만큼 쓰여요.", cols=2))
    parts.append(mix("빠른 AI가 좋은 AI일까요?",
                     '<div class="split-short"><div><p class="mix-lead">사람처럼 화면을 보고 마우스를 움직이는 AI예요. 빠르진 않죠? 대신 처음부터 끝까지 <strong>스스로</strong> 해요.</p>'
                     '<p class="mix-lead">요즘 AI는 오래 걸려도 <strong>검토할 게 적은</strong> 쪽으로 가요. 기다리지 말고, 시켜 두고 다른 일을 하세요.</p></div>'
                     + yt("ffSpxalmi9E", "사람처럼 컴퓨터를 쓰는 AI (쇼츠)", short=True) + "</div>", "▶ 쇼츠"))
    parts.append(key_block("오늘 가져가는 것", None,
                           [("00_하네스_공문서", "04 학교기본정보만 고치면 <strong>내일부터</strong>"),
                            ("프롬프트 저장소", "이 페이지에서 <strong>복사</strong>해서 그대로"),
                            ("정답 파일", "결과와 <strong>나란히</strong> 놓고 비교")]))
    acts = '<a class="btn btn-primary" href="download/inlineAI_실습.zip" download>실습 자료 전체 ↓</a>'
    return lecture("s10", "끝", "정리 ·<br />내일부터 이렇게", "아침에 시켜 두고, 수업 다녀와서 확인해요. 여러 AI에게 동시에 맡겨도 돼요.", "tile-write", False, "".join(parts), acts)


# ------------------------------------------------------------------ 페이지
NAV = [("s00", "준비"), ("s01", "다운로드"), ("s02", "가정통신문"), ("s03", "한글 표"), ("s04", "작년 문서"),
       ("s05", "행정"), ("s06", "기안문"), ("s07", "보고서"), ("s08", "PPT"), ("s09", "코워크"), ("s10", "정리")]


def page():
    secs = [prep_section()] + [practice_section(no, i + 1) for i, no in enumerate(FOLDERS)] + [cowork_section(), wrap_section()]
    if not exists("download/inlineAI_실습.zip"):
        MISSING.append("download/inlineAI_실습.zip")
    allzip = f'download/inlineAI_실습.zip'
    nav = "".join(f'<a href="#{a}">{E(b)}</a>' for a, b in NAV)
    toc1 = "".join(f'<a href="#{a}">{a[1:]} {E(b)}</a>' for a, b in NAV[:6])
    toc2 = "".join(f'<a href="#{a}">{a[1:] if a != "s10" else ""} {E(b)}</a>' for a, b in NAV[6:])
    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="color-scheme" content="light" />
  <title>inline AI 업무 실습</title>
  <meta name="description" content="내 업무 파일, AI에게 맡겨 보기 — inline AI 연수 매뉴얼과 프롬프트 저장소. 실습 파일 내려받기, 복사 버튼, 정답 미리보기." />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Black+Han+Sans&display=swap" rel="stylesheet" />
  <link rel="stylesheet" as="style" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css" />
  <link rel="stylesheet" href="styles.css" />
</head>
<body>
<!-- 이 파일은 tools/build_site.py 로 만든다. 직접 고치지 말고 스크립트를 고친 뒤 다시 실행하세요. -->

  <div class="utility-bar">
    <div class="shell">
      <a class="caption-sm" href="#s00">처음 준비</a>
      <a class="caption-sm" href="prompts.html">프롬프트 모음</a>
      <a class="caption-sm deck-tab-pdf" href="{url(allzip)}" download>실습 자료 zip ↓</a>
      <a class="deck-tab" href="lecture.html">강의 화면</a>
      <a class="deck-tab deck-tab-padlet" href="https://portal.inline-ai.com/invitation-promotion?code=K2YERY3H" target="_blank" rel="noopener">초대 이벤트 &#8599;</a>
    </div>
  </div>

  <header class="primary-nav">
    <div class="shell">
      <button class="nav-toggle" type="button" aria-label="메뉴 열기">&#9776;</button>
      <a class="brand" href="#top"><span class="swoosh">inline AI</span> 실습</a>
      <nav class="nav-links" aria-label="실습 목차">{nav}</nav>
      <div class="nav-actions">
        <a class="deck-tab nav-deck" href="lecture.html">강의 화면</a>
      </div>
    </div>
  </header>

  <main class="shell" id="top">

    <section class="hero" aria-label="내 업무 파일, AI에게 맡겨 보기">
      <div class="hero-inner">
        <span class="hero-badge">교원 연수 · inline AI</span>
        <h1 class="display-campaign">내 업무 파일,<br />AI에게<br />맡겨 보기</h1>
        <p class="hero-sub">일단 던지고, 내 컴퓨터에 초대하고, 정해진 양식을 주세요.</p>
        <div class="hero-cta">
          <a class="btn btn-on-image" href="{url(allzip)}" download>실습 자료 전체 내려받기 ({kb(allzip)}) ↓</a>
          <a class="btn btn-ghost" href="lecture.html">강의 화면 보기</a>
        </div>
      </div>
    </section>

    <section class="goal" aria-label="연수 목표">
      <div class="goal-label">연수 목표</div>
      <div>
        <p class="goal-text">내 업무 파일을 AI에게 맡기고, 결과를 확인해 고쳐 쓸 수 있다.</p>
        <div class="goal-tags">
          <span class="goal-tag">① 일단 던지기</span>
          <span class="goal-tag">② 내 컴퓨터에 초대</span>
          <span class="goal-tag">③ 정해진 양식 주기</span>
          <span class="goal-tag">긴 설명보다 자료 하나</span>
        </div>
      </div>
    </section>

    <section class="gemini-cta" aria-label="초대 이벤트">
      <span class="cta-logo cta-num">1,000</span>
      <div class="cta-copy">
        <h3>inline AI 초대 이벤트</h3>
        <p class="cta-notice"><span class="notice-tag">무료</span>초대 코드 <strong class="code">K2YERY3H</strong> 를 넣으면 <strong>1,000 크레딧</strong>을 더 받아요.</p>
      </div>
      <div class="cta-actions">
        <button class="btn btn-secondary copy-code" type="button" data-copy="K2YERY3H">코드 복사</button>
        <a class="btn btn-primary" href="https://portal.inline-ai.com/invitation-promotion?code=K2YERY3H" target="_blank" rel="noopener">초대 링크 열기 &#8599;</a>
      </div>
    </section>

    <div class="howto">
      <p><strong>이 페이지 쓰는 법</strong> — 실습마다 <strong>[펼치기 +]</strong>를 누르면 순서·파일·프롬프트·정답이 열려요. 프롬프트는 <strong>[복사]</strong> → 입력창에 <strong>Ctrl+V</strong>.</p>
      <button class="btn btn-secondary btn-sm" type="button" id="openAll">모두 펼치기</button>
    </div>
{"".join(secs)}

  </main>

  <footer class="site-footer shell">
    <div class="footer-cols">
      <div class="footer-col"><h4>실습 목차</h4>{toc1}</div>
      <div class="footer-col"><h4>실습 목차</h4>{toc2}</div>
      <div class="footer-col"><h4>자료</h4>
        <a href="{url(allzip)}" download>실습 자료 전체 zip</a>
        <a href="{url("download/폴더별/00_하네스_공문서.zip")}" download>하네스 폴더 zip</a>
        <a href="prompts.html">프롬프트 모음(한 페이지)</a>
        <a href="lecture.html">강의 화면</a>
      </div>
      <div class="footer-col"><h4>안내</h4>
        <p class="footer-note">실습 자료 속 학교(오현초등학교)와 사람 이름은 <strong>실습용 가상 정보</strong>예요(실존 인물 아님). 실제 문서는 이름·연락처를 지운 익명화본이에요.</p>
      </div>
    </div>
    <div class="footer-fine utility-xs">
      <span>inline AI 업무 실습 연수</span>
      <span>분리수거 사진: TrashNet (Stanford, MIT License)</span>
      <span>꿀벌·랜드마크·무늬 그림: 다문화 보드</span>
      <span class="grow">화면은 2026. 10. 5. 기준이에요. 앱 업데이트로 바뀔 수 있어요.</span>
    </div>
  </footer>

  <div class="toast" id="toast" role="status" aria-live="polite"></div>
  <script src="site.js"></script>
</body>
</html>
'''


if __name__ == "__main__":
    out = page()
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(out)
    n = out.count('class="prompt-copy"')
    print("index.html", f"{len(out)/1024:.0f}KB", "복사 버튼", n, "개")
    if MISSING:
        print("없는 파일:", *sorted(set(MISSING)), sep="\n  ")
    else:
        print("없는 파일: 0")

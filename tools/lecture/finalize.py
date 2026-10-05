import fitz, pathlib, shutil, secrets
REPO = pathlib.Path(r"C:\Users\권준구\Desktop\inline-ai-setup"); HERE = pathlib.Path(__file__).parent
raw = fitz.open(HERE / "raw.pdf")
raw.set_metadata({"title": "inline AI 업무 실습 강의안", "subject": "교원 연수 · inline AI", "author": "", "creator": "lecture.html"})
out = REPO / "deck" / "강의안.pdf"
raw.save(out, garbage=4, deflate=True, encryption=fitz.PDF_ENCRYPT_AES_256, user_pw="1111", owner_pw=secrets.token_hex(16),
         permissions=fitz.PDF_PERM_PRINT | fitz.PDF_PERM_COPY | fitz.PDF_PERM_ACCESSIBILITY)
# 확인
d = fitz.open(out)
print("needs_pass:", d.needs_pass, "| wrong pw:", d.authenticate("0000"), "| 1111:", d.authenticate("1111"), "| pages:", d.page_count,
      "| size MB:", round(out.stat().st_size / 1e6, 2), "| encryption:", d.metadata.get("encryption"))
prev = REPO / "deck" / "강의안_미리보기"; prev.mkdir(exist_ok=True)
for f in prev.glob("*.png"): f.unlink()
PICK = {1: "표지", 12: "준비_단계표", 27: "업무지침_관계도", 28: "오늘지도", 31: "01_준비_프롬프트표", 42: "02_캡처_계획먼저", 105: "비교표_inlineAI_코워크", 108: "아침루틴_동시작업", 109: "다시보기_QR"}
for n, name in PICK.items():
    d[n - 1].get_pixmap(dpi=96).save(prev / ("%03d_%s.png" % (n, name)))
print("previews:", sorted(p.name for p in prev.glob("*.png")))

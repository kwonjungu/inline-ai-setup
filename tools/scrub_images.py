# 실습 파일 속 그림 중 개인정보(직인·학생 사진·QR)를 문서 모양은 그대로 두고 지우거나 흐리게 바꾼다
import io, os, sys, zipfile, copy
from PIL import Image, ImageFilter
sys.stdout.reconfigure(encoding="utf-8")
M = "materials"
JOBS = {
    "05_행정처리_도움받기/2022 오현초 교구 견적서(마샬 액톤 외).xlsx": {"xl/media/image1.png": "blank", "xl/media/image2.png": "blank", "xl/media/image3.png": "blank"},
    "04_작년도문서_업데이트/2025년 오현초 디지털튜터 신청서 및 운영계획서(작년).hwpx": {"BinData/image8.bmp": "blur", "BinData/image20.bmp": "blur", "BinData/image21.bmp": "blur", "Preview/PrvImage.png": "blur"},
    "04_작년도문서_업데이트/정답_예시/정답_2026년 오현초 디지털튜터 신청서 및 운영계획서.hwpx": {"BinData/image8.BMP": "blur", "BinData/image20.BMP": "blur", "BinData/image21.BMP": "blur", "Preview/PrvImage.png": "blur"},
    "06_계획서로_기안문쓰기/2025학년도 오현 AI 과학의 날 운영계획.hwpx": {"BinData/image4.png": "blur", "Preview/PrvImage.png": "blur"},
}
def fix(data, name, how):
    im = Image.open(io.BytesIO(data)); fmt = im.format or "PNG"
    if how == "blank":
        out = Image.new("RGBA", im.size, (255, 255, 255, 0)) if im.mode in ("RGBA", "LA", "P") else Image.new(im.mode, im.size, "white")
    else:
        base = im.convert("RGB"); small = base.resize((max(1, base.width // 24), max(1, base.height // 24)))
        out = small.resize(base.size, Image.NEAREST).filter(ImageFilter.GaussianBlur(6))
        if im.mode not in ("RGB",): out = out.convert(im.mode) if im.mode in ("L", "RGBA") else out
    b = io.BytesIO(); out.save(b, format=fmt); return b.getvalue()
for rel, items in JOBS.items():
    p = os.path.join(M, rel)
    if not os.path.exists(p): print("없음", rel); continue
    zin = zipfile.ZipFile(p); tmp = p + ".tmp"; done = []
    with zipfile.ZipFile(tmp, "w") as zo:
        for i in zin.infolist():
            d = zin.read(i.filename)
            if i.filename in items:
                d = fix(d, i.filename, items[i.filename]); done.append(i.filename)
            zo.writestr(copy.copy(i), d, compress_type=zipfile.ZIP_STORED if i.filename == "mimetype" else zipfile.ZIP_DEFLATED)
    zin.close(); os.replace(tmp, p); print(rel, done)

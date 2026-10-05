# -*- coding: utf-8 -*-
"""실습 폴더마다 zip을 만든다 → download/폴더별/<폴더명>.zip
   zip 안 최상위 폴더 = 실습 폴더 이름, 파일 이름은 UTF-8(zip 표준 플래그)로 저장."""
import os, sys, zipfile
sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M = os.path.join(ROOT, "materials")
OUT = os.path.join(ROOT, "download", "폴더별")
os.makedirs(OUT, exist_ok=True)

for name in sorted(os.listdir(M)):
    src = os.path.join(M, name)
    if not os.path.isdir(src):
        continue
    dst = os.path.join(OUT, name + ".zip")
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for dp, dns, fns in os.walk(src):
            dns.sort()
            rel_dir = os.path.relpath(dp, M).replace(os.sep, "/")
            z.writestr(zipfile.ZipInfo(rel_dir + "/"), b"")
            for fn in sorted(fns):
                z.write(os.path.join(dp, fn), rel_dir + "/" + fn)
    # 확인: 이름이 UTF-8 플래그로 들어갔는지
    with zipfile.ZipFile(dst) as z:
        n = len([i for i in z.infolist() if not i.is_dir()])
        utf8 = all((i.flag_bits & 0x800) or i.filename.isascii() for i in z.infolist())
    print(f"{name}.zip  파일 {n}개  {os.path.getsize(dst)/1024:,.0f} KB  UTF-8 {'OK' if utf8 else '확인 필요'}")

# 클로드 스킬 업로드용: zip 안에 school-official-docs/SKILL.md + references/
skill = os.path.join(M, "00_업무지침", "클로드_스킬용")
dst = os.path.join(ROOT, "download", "클로드_스킬_school-official-docs.zip")
with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for dp, dns, fns in os.walk(skill):
        dns.sort()
        for fn in sorted(fns):
            rel = os.path.relpath(os.path.join(dp, fn), skill).replace(os.sep, "/")
            z.write(os.path.join(dp, fn), "school-official-docs/" + rel)
print(f"클로드_스킬_school-official-docs.zip  {os.path.getsize(dst)/1024:,.0f} KB")

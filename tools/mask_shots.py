# -*- coding: utf-8 -*-
"""사이트에 쓰는 앱 캡처 중 계정 이름이 보이는 것을 가린 사본을 assets/files/ 에 만든다(원본은 그대로)."""
import os
from PIL import Image, ImageDraw
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = os.path.join(ROOT, "assets", "shot", "inline")
O = os.path.join(ROOT, "assets", "files")
GRAY = (236, 236, 236)
JOBS = {
    "03_input_example_1280.png": [(728, 196, 856, 232)],     # 인사말 속 계정 이름
    "07_work_panel_1280.png": [(492, 200, 652, 232)],        # 인사말 속 계정 이름
    "11_settings_general_1280.png": [(352, 124, 600, 156)],  # 이름 칸
}
for name, boxes in JOBS.items():
    im = Image.open(os.path.join(S, name)).convert("RGB")
    d = ImageDraw.Draw(im)
    for b in boxes:
        d.rectangle(b, fill=GRAY)
    out = os.path.join(O, "shot_" + name)
    im.save(out, optimize=True)
    print(out)

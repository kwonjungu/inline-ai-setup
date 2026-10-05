import os
import subprocess, pathlib, re, html
REPO = pathlib.Path(r"C:\Users\권준구\Desktop\inline-ai-setup"); HERE = pathlib.Path(__file__).parent
url = (REPO / "lecture.html").as_uri() + "?print=1&code=1111&audit=1" + (("&lang=" + os.environ["LANGX"]) if os.environ.get("LANGX") else "")
edge = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
r = subprocess.run([edge, "--headless=new", "--disable-gpu", "--user-data-dir=" + str(HERE / "edgeprof"), "--window-size=1400,900",
                    "--virtual-time-budget=30000", "--dump-dom", url], capture_output=True, timeout=240)
dom = r.stdout.decode("utf-8", "replace")
m = re.search(r"<pre id=\"audit\">AUDIT-BEGIN(.*?)AUDIT-END", dom, re.S)
print(html.unescape(m.group(1)).strip() if m else "NO AUDIT OUTPUT")

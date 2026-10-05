# 원고.md 장 번호를 순서대로 다시 매기고 원고_목차.md 표·띄워 두는 장 목록을 다시 계산
import re,sys
sys.stdout.reconfigure(encoding='utf-8')
p='deck/원고.md'; s=open(p,encoding='utf-8').read()
n=[0]
def ren(m): n[0]+=1; return f"### S{n[0]:03d} "
s=re.sub(r'(?m)^### S(?:\d{3}|[A-Z]\d) ',ren,s); open(p,'w',encoding='utf-8').write(s)
rows=[];hold=[];t0=0;tot=0
for sec in re.split(r'(?m)^## ',s)[1:]:
    name=sec.split('\n',1)[0].split('  (')[0].strip()
    sl=re.findall(r'^### (S\d{3}) \[[^\]]+\] .*? · (\d+)\s*\n- 화면 글자: ([^\n]*)',sec,flags=re.M)
    if not sl: continue
    ss=sum(int(x[1]) for x in sl); c=len(sl); tot+=c
    st=f"{t0//3600:02d}:{t0%3600//60:02d}"; t0+=ss; en=f"{t0//3600:02d}:{t0%3600//60:02d}"
    rows.append(f"| {st}–{en} | {name} | {sl[0][0]}–{sl[-1][0]} | {c} | {ss//60} | {ss} | {ss//c} |")
    b=max(sl,key=lambda x:int(x[1])); hold.append(f"- {name}: {b[0]} ({b[1]}초) — {b[2].replace(' / ',' ')}")
table="| 시각 | 구간 | 슬라이드 | 장수 | 시간(분) | 시간(초) | 장당 평균(초) |\n|---|---|---|---|---|---|---|\n"+"\n".join(rows)+f"\n| | **합계** | S001–S{tot:03d} | **{tot}** | **{t0//60}** | **{t0}** | **{t0//tot}** |"
q='deck/원고_목차.md'; m=open(q,encoding='utf-8').read()
m=re.sub(r'(?s)\| 시각 \| 구간 \|.*?\*\*합계\*\*[^\n]*',lambda _:table,m,count=1)
m=re.sub(r'(?s)(## 구간별 띄워 두는 장\(실습 대기\)\n\n).*?(?=\n## |\n- 여는 말 S002|\n- 정리 S|\n- 도입 S|\Z)',lambda x:x.group(1)+'\n'.join(hold)+'\n',m,count=1)
open(q,'w',encoding='utf-8').write(m); print(tot,'slides',t0,'sec')

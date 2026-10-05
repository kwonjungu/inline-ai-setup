import zipfile,os,glob,copy,re,sys
sys.stdout.reconfigure(encoding='utf-8')
M="materials"
def rdf_for(z):
    secs=sorted(n for n in z.namelist() if re.match(r'Contents/section\d+\.xml',n))
    body=''
    for p in ['Contents/header.xml']+secs:
        t='HeaderFile' if 'header' in p else 'SectionFile'
        body+=f'<rdf:Description rdf:about=""><ns0:hasPart xmlns:ns0="http://www.hancom.co.kr/hwpml/2016/meta/pkg#" rdf:resource="{p}"/></rdf:Description><rdf:Description rdf:about="{p}"><rdf:type rdf:resource="http://www.hancom.co.kr/hwpml/2016/meta/pkg#{t}"/></rdf:Description>'
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes" ?><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'+body+'<rdf:Description rdf:about=""><rdf:type rdf:resource="http://www.hancom.co.kr/hwpml/2016/meta/pkg#Document"/></rdf:Description></rdf:RDF>').encode()
META_HWPX=[(r'(<opf:meta name="(?:creator|lastsaveby)"[^>]*>)[^<]*(</opf:meta>)',r'\1홍길동\2')]
META_OOXML=[(r'(<dc:creator>)[^<]*(</dc:creator>)',r'\1홍길동\2'),(r'(<cp:lastModifiedBy>)[^<]*(</cp:lastModifiedBy>)',r'\1홍길동\2')]
for f in glob.glob(M+'/**/*.*',recursive=True):
    if not f.endswith(('.hwpx','.xlsx','.pptx')) or os.path.getsize(f)==0: continue
    z=zipfile.ZipFile(f); names=z.namelist(); changed=[]
    out={}
    for i in z.infolist():
        d=z.read(i.filename)
        if f.endswith('.hwpx') and i.filename=='META-INF/container.rdf' and b'HeaderFile' not in d:
            d=rdf_for(z); changed.append('rdf')
        if f.endswith('.hwpx') and i.filename=='Contents/content.hpf':
            s=d.decode('utf-8'); s2=s
            for a,b in META_HWPX: s2=re.sub(a,b,s2)
            if s2!=s: d=s2.encode('utf-8'); changed.append('meta')
        if i.filename=='docProps/core.xml':
            s=d.decode('utf-8'); s2=s
            for a,b in META_OOXML: s2=re.sub(a,b,s2)
            if s2!=s: d=s2.encode('utf-8'); changed.append('meta')
        out[i.filename]=(i,d)
    z.close()
    if changed:
        tmp=f+'.tmp'
        with zipfile.ZipFile(tmp,'w') as zo:
            for n,(i,d) in out.items():
                zo.writestr(copy.copy(i),d,compress_type=zipfile.ZIP_STORED if n=='mimetype' else zipfile.ZIP_DEFLATED)
        os.replace(tmp,f); print(changed,f)

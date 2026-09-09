"""Відновлює static2.jsonl (тексти статичних сторінок) із джерел v9 у designs/.
Оригінал лежав у scratchpad старої сесії і зник. Формат запису: {"src": "hunch-about", "d": {kicker,title,lead,body}}.
body = блок після .page-hdr до підвалу, без атрибутів class/style (як робив перший витяг)."""
import re,json,os,html as H
D=os.path.dirname(os.path.abspath(__file__)); SRC=os.path.dirname(D)
SOURCES=['hunch-leaderboard','hunch-echo-library','hunch-patterns','hunch-methodology','hunch-sources','membership','hunch-signup','hunch-account','hunch-mobile-app','hunch-about','hunch-team','hunch-partners','hunch-press','hunch-careers','hunch-contact','hunch-newsletter','hunch-help','hunch-status','hunch-api','hunch-sitemap','hunch-accessibility','hunch-terms','hunch-privacy','hunch-cookies','hunch-acceptable-use','hunch-licences','hunch-policy','hunch-editorial-code','hunch-responsible-play']
def text(rx,s):
    m=re.search(rx,s,re.S); return re.sub(r'\s+',' ',H.unescape(re.sub('<[^>]+>','',m.group(1)))).strip() if m else ''
def strip_attrs(h):
    h=re.sub(r'<!--.*?-->','',h,flags=re.S)
    h=re.sub(r'\s(class|style)="[^"]*"','',h)
    return h
out=[]
for src in SOURCES:
    s=open(os.path.join(SRC,src+'.html'),encoding='utf-8').read()
    end=s.find('<div class="footer-full">'); end=end if end>0 else s.find('<footer')
    d={}
    mh=re.search(r'<div class="page-hdr"[^>]*>',s); a=mh.start() if mh else -1
    if a>0:
        hdr_end=s.find('</div>',s.find('<p class="page-lead">',a) if '<p class="page-lead">' in s[a:a+2000] else a)
        # кінець page-hdr: перший </div> після ліду (або після title)
        hdr=s[a:s.find('</div>',hdr_end)+6] if hdr_end>0 else s[a:s.find('</div>',a)+6]
        d['kicker']=text(r'<div class="page-kicker">(.*?)</div>',hdr); d['title']=text(r'<h1 class="page-title">(.*?)</h1>',hdr); d['lead']=text(r'<p class="page-lead">(.*?)</p>',hdr)
        body=s[a+len(hdr):end]
    else:
        a=-1
        for start in ('<div class="doc-grid">','<div class="v10">','<main'):
            a=s.find(start)
            if a>0: break
        if a<0: a=s.find('</aside>')+len('</aside>')
        blk=s[a:end]
        d['kicker']=text(r'<div class="(?:v9-cat-k|kicker|hero-eyebrow)">(.*?)</div>',blk); d['title']=text(r'<h1[^>]*>(.*?)</h1>',blk); d['lead']=text(r'<(?:p|div) class="(?:v9-cat-lede|page-lead|hero-sub)">(.*?)</(?:p|div)>',blk)
        body=blk
    body=re.sub(r'\s*·\s*<a href="#what">[^<]*included[^<]*</a>','',body)  # кнопку знято (Pavlo 7 Sep)
    body=re.sub(r'<a[^>]*>[^<]*Start your 14-day trial[^<]*</a>','',body)  # кнопку знято (Pavlo 7 Sep)
    d['body']=strip_attrs(body).strip()
    out.append({'src':src,'d':d})
open(os.path.join(D,'static2.jsonl'),'w',encoding='utf-8').write('\n'.join(json.dumps(r,ensure_ascii=False) for r in out)+'\n')
print('static2.jsonl:',len(out),'records')
for r in out[:3]+out[-2:]: print(r['src'],'|',r['d']['kicker'],'|',r['d']['title'][:40],'| body',len(r['d']['body']))

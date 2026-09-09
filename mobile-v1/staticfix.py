"""Перетворює безкласові діви витягнутих статичних сторінок на компоненти збірки.
Нічого не дописує: тільки перегруповує наявний текст і вішає класи."""
import re
from html.parser import HTMLParser

VOID={'br','img','input','hr','meta','link','source'}

class Node:
    __slots__=('tag','attrs','kids','text')
    def __init__(self,tag,attrs=None,text=''):
        self.tag=tag; self.attrs=attrs or []; self.kids=[]; self.text=text

class P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.root=Node('#root'); self.stack=[self.root]
    def handle_starttag(self,t,a):
        n=Node(t,a); self.stack[-1].kids.append(n)
        if t not in VOID: self.stack.append(n)
    def handle_startendtag(self,t,a): self.stack[-1].kids.append(Node(t,a))
    def handle_endtag(self,t):
        for i in range(len(self.stack)-1,0,-1):
            if self.stack[i].tag==t: del self.stack[i:]; return
    def handle_data(self,d):
        if d.strip(): self.stack[-1].kids.append(Node('#text',text=d))
        elif d and self.stack[-1].kids: self.stack[-1].kids.append(Node('#text',text=' '))
    def handle_entityref(self,n): self.stack[-1].kids.append(Node('#text',text='&%s;'%n))
    def handle_charref(self,n): self.stack[-1].kids.append(Node('#text',text='&#%s;'%n))

def parse(h):
    p=P(); p.feed(h); return p.root

def txt(n):
    if n.tag=='#text': return n.text
    return ''.join(txt(k) for k in n.kids)

def clean(s): return re.sub(r'\s+',' ',s).strip()

def els(n): return [k for k in n.kids if k.tag not in ('#text',)]

def leaf(n):
    return n.tag!='#text' and all(k.tag=='#text' or k.tag in ('span','b','strong','em','i','a','br') for k in n.kids)

def attrstr(a):
    return ''.join(f' {k}="{v}"' for k,v in a if v is not None and k not in ('class','style'))

def ser(n, cls=None):
    if n.tag=='#text': return n.text
    if n.tag=='#root': return ''.join(ser(k) for k in n.kids)
    c=f' class="{cls}"' if cls else ''
    if n.tag in VOID: return f'<{n.tag}{c}{attrstr(n.attrs)}>'
    return f'<{n.tag}{c}{attrstr(n.attrs)}>' + ''.join(ser(k) for k in n.kids) + f'</{n.tag}>'

NUM=re.compile(r'^[£$€]?[\d.,]+\s*(%|\+|min|HP)?$|^\d{1,2}$')

def kv(n):
    """<div><div>A</div><div>B</div></div> → рядок ключ-значення"""
    e=els(n)
    if n.tag!='div' or len(e)!=2: return None
    if not all(x.tag=='div' and leaf(x) for x in e): return None
    a,b=clean(txt(e[0])),clean(txt(e[1]))
    if not a or not b or len(a)>44 or len(b)>44: return None
    a_val = bool(NUM.match(a)) or (len(a)<=12 and re.search(r'\d', a) and not re.search(r'[a-z]{3}', a.lower()))
    b_val = bool(NUM.match(b)) or (len(b)<=12 and re.search(r'\d', b) and not re.search(r'[a-z]{3}', b.lower()))
    if a_val and not b_val:
        return f'<div class="kv"><span class="v">{a}</span><span class="k">{b}</span></div>'
    if NUM.match(b) or len(b)<=24:
        return f'<div class="kv"><span class="k">{a}</span><span class="v">{b}</span></div>'
    return None

def card(n):
    """<div><div>кікер</div><div>заголовок</div><div>текст</div>[…]</div> → картка"""
    e=els(n)
    if n.tag!='div' or len(e)<3: return None
    a,b,c=e[0],e[1],e[2]
    if not (a.tag in ('div','span') and leaf(a) and b.tag in ('div','h3','h4') and leaf(b)): return None
    ta,tb,tc=clean(txt(a)),clean(txt(b)),clean(txt(c))
    if not(ta and tb and tc): return None
    if len(ta)>60 or len(tb)>120 or len(tc)<20: return None
    rest=''.join(walk(x) for x in e[3:])
    meta_second = (('\u00b7' in tb) or re.match(r'^(Archive|Updated|Collection|Since|Est)\b', tb)) \
                  and not re.fullmatch(r'\d{1,2}', ta)
    if meta_second:
        head, sub = ta, f'<div class="s-meta">{tb}</div>'
    else:
        head, sub = tb, ''
    kick = '' if meta_second else f'<div class="kick">{ta}</div>'
    return (f'<article class="scard">{kick}'
            f'<h3 class="item-h">{head}</h3>{sub}<p class="item-s">{tc}</p>{rest}</article>')

def step(n):
    """<div><div>1</div><div>…</div></div> → нумерований крок"""
    e=els(n)
    if n.tag!='div' or len(e)!=2: return None
    a,b=e[0],e[1]
    if not(leaf(a) and re.fullmatch(r'\d{1,2}', clean(txt(a)))): return None
    inner=els(b)
    if b.tag=='div' and len(inner)>=2 and leaf(inner[0]):
        t=clean(txt(inner[0])); rest=''.join(walk(x) for x in inner[1:])
        return (f'<div class="step"><span class="n">{clean(txt(a))}</span>'
                f'<div class="s-b"><h3 class="item-h">{t}</h3>{rest}</div></div>')
    return None

def numcard(n):
    """<div><div>01</div><h4>…</h4><p>…</p></div>"""
    e=els(n)
    if n.tag!='div' or len(e)<3: return None
    if not(leaf(e[0]) and re.fullmatch(r'\d{1,2}', clean(txt(e[0])))): return None
    if e[1].tag not in ('h3','h4'): return None
    rest=''.join(walk(x) for x in e[2:])
    return (f'<div class="step"><span class="n">{clean(txt(e[0]))}</span>'
            f'<div class="s-b"><h3 class="item-h">{clean(txt(e[1]))}</h3>{rest}</div></div>')

def kids_html(n):
    """обробляє дітей із заглядом уперед: короткий лід-заголовок перед сіткою стає h2"""
    out=[]; k=n.kids; i=0
    while i < len(k):
        cur=k[i]
        if cur.tag=='div' and leaf(cur):
            t=clean(txt(cur))
            nxt=None
            for j in range(i+1,len(k)):
                if k[j].tag!='#text': nxt=k[j]; break
            if t and len(t)<=60 and not t.endswith('.') and nxt is not None:
                if nxt.tag in ('h1','h2','h3'):
                    out.append(f'<div class="kick">{t}</div>'); i+=1; continue
                if nxt.tag in ('div','section','ul') and els(nxt):
                    out.append(f'<h2>{t}</h2>'); i+=1; continue
        out.append(walk(cur)); i+=1
    return ''.join(out)


def spanjoin(n):
    """склеєні спани розділяє крапкою; текстові вузли не губить"""
    sp=[k for k in n.kids if k.tag=='span']
    has_text=any(k.tag=='#text' and k.text.strip() for k in n.kids)
    if len(sp)>=2 and not has_text and all(clean(txt(x)) for x in sp):
        return ' \u00b7 '.join(clean(txt(x)) for x in sp)
    parts=[]
    for k in n.kids:
        t=clean(txt(k))
        if not t: continue
        parts.append(t)
    out=' '.join(parts)
    out=re.sub(r'\s*\u00b7\s*', ' \u00b7 ', out)
    return clean(out)

def art(n):
    """<article> з мета-рядком, заголовком і текстом → картка"""
    if n.tag!='article': return None
    e=els(n)
    head=next((x for x in e if x.tag in ('h2','h3','h4')), None)
    par=next((x for x in e if x.tag=='p'), None)
    if not head or not par: return None
    metas=[x for x in e if x.tag=='div' and leaf(x)]
    kick = spanjoin(metas[0]) if metas else ''
    foot = spanjoin(metas[-1]) if len(metas)>1 else ''
    k = f'<div class="kick">{kick}</div>' if kick else ''
    f = f'<div class="s-meta">{foot}</div>' if foot else ''
    return (f'<article class="scard">{k}<h3 class="item-h">{clean(txt(head))}</h3>'
            f'<p class="item-s">{clean(txt(par))}</p>{f}</article>')


PRICE=re.compile(r'^[£$€]\s?[\d.,]+')

def tier(n):
    """картка тарифу: назва, ціна, примітка, список переваг, кнопка"""
    if n.tag!='div': return None
    e=els(n)
    if len(e)<4: return None
    ul=next((x for x in e if x.tag=='ul'), None)
    if ul is None: return None
    price=next((x for x in e if x.tag=='div' and leaf(x) and PRICE.match(clean(txt(x)))), None)
    if price is None: return None
    name=e[0]
    if not(name.tag=='div' and leaf(name)): return None
    notes=[x for x in e if x.tag=='div' and leaf(x) and x is not name and x is not price]
    cta=next((x for x in e if x.tag in ('a','button')), None)
    p_txt=spanjoin(price)
    note=f'<div class="s-meta">{clean(txt(notes[0]))}</div>' if notes else ''
    items=''.join(f'<li>{clean(txt(li))}</li>' for li in els(ul) if li.tag=='li')
    btn=f'<button class="tier-cta" type="button" disabled aria-disabled="true">{clean(txt(cta))}</button>' if cta is not None else ''
    return (f'<div class="scard tier"><div class="kick">{spanjoin(name)}</div>'
            f'<div class="price">{p_txt}</div>{note}'
            f'<ul class="blist">{items}</ul>{btn}</div>')


PCT=re.compile(r'^\d{1,3}%$')

def predrow(n):
    """рядок прогнозу: питання, відсоток, дата, статус"""
    if n.tag!='div': return None
    e=els(n)
    if not (3 <= len(e) <= 4): return None
    if not all(x.tag=='div' and leaf(x) for x in e): return None
    t=[clean(txt(x)) for x in e]
    if not (PCT.match(t[1]) or t[1] in ('\u2014','\u2013','-')): return None
    if len(t[0])<20: return None
    meta=''.join(f'<span>{x}</span>' for x in t[2:])
    return (f'<div class="prow"><div class="q">{t[0]}</div>'
            f'<div class="m"><span class="pct">{t[1]}</span>{meta}</div></div>')


def chips(n):
    """кілька посилань підряд: мертві → чипи фільтрів, живі → рядок кнопок"""
    if n.tag not in ('div','p'): return None
    e=els(n)
    if len(e)<2 or not all(x.tag=='a' and leaf(x) for x in e): return None
    ts=[clean(txt(x)) for x in e]
    if not all(0 < len(t) <= 40 for t in ts): return None
    hrefs=[dict(x.attrs).get('href','') for x in e]
    live=[h for h in hrefs if h and h!='#']
    if len(live)==len(e):
        return '<div class="acts">'+''.join(
            f'<a class="cta s" href="{h}">{t}</a>' for h,t in zip(hrefs,ts))+'</div>'
    if len(e)<3 or not all(len(t)<=20 for t in ts): return None
    def one(h,t):
        if h and h!='#': return f'<a class="chip" href="{h}">{t}</a>'
        return f'<span class="chip">{t}</span>'
    return '<div class="chips">'+''.join(one(h,t) for h,t in zip(hrefs,ts))+'</div>'

META=re.compile(r'\u00b7')

def metaline(n):
    """рядок дрібної статистики: «6 collections · 81 Echoes · Latest update…»"""
    if n.tag!='div' or not leaf(n): return None
    t=spanjoin(n)
    if not t or len(t)>140: return None
    if not META.search(t) or not re.search(r'\d', t): return None
    return f'<div class="s-meta wide">{t}</div>'


def linkcta(n):
    """самотнє посилання-заклик у власному дів → кнопка"""
    if n.tag!='div': return None
    e=els(n)
    if len(e)!=1 or e[0].tag!='a': return None
    a=e[0]; href=dict(a.attrs).get('href','')
    t=clean(txt(a))
    if not t or len(t)>60 or not href or href=='#': return None
    return f'<div class="acts"><a class="cta p" href="{href}">{t}</a></div>'


def pair_card(n):
    """<div><div>Назва</div><div>довгий опис</div></div> → маленька картка"""
    if n.tag!='div': return None
    e=els(n)
    if len(e)!=2 or not all(x.tag=='div' and leaf(x) for x in e): return None
    a,b=clean(txt(e[0])),clean(txt(e[1]))
    if not a or not b: return None
    if len(a)>48 or len(b)<40: return None
    return f'<article class="scard sm"><h3 class="item-h">{a}</h3><p class="item-s">{b}</p></article>'


def qa(n):
    """питання і відповідь двома дівами → блок Q&A"""
    if n.tag!='div': return None
    e=els(n)
    if len(e)!=2 or not all(x.tag=='div' and leaf(x) for x in e): return None
    q,a=clean(txt(e[0])),clean(txt(e[1]))
    if not q.endswith('?') or len(a)<40: return None
    return f'<div class="qa"><div class="q">{q}</div><p>{a}</p></div>'

def walk(n):
    if n.tag=='#text': return n.text
    for f in (art, tier, chips, linkcta, qa, predrow, kv, numcard, step, card, pair_card, metaline):
        r=f(n)
        if r: return r
    if n.tag=='a' and dict(n.attrs).get('role')=='button':
        t=clean(txt(n)); href=dict(n.attrs).get('href','')
        if href and href!='#':
            return f'<div class="acts"><a class="cta p" href="{href}">{t}</a></div>'
        return ('<div class="acts"><button class="cta p" type="button" disabled '
                f'aria-disabled="true">{t}</button></div>')
    if n.tag=='ul': return '<ul class="blist">'+''.join(walk(k) for k in n.kids)+'</ul>'
    if n.tag=='li': return '<li>'+''.join(walk(k) for k in n.kids)+'</li>'
    if n.tag in ('h4','h5'): return f'<h3 class="item-h">{clean(txt(n))}</h3>'
    if n.tag=='#root': return kids_html(n)
    if n.tag in VOID: return ser(n)
    inner=kids_html(n)
    if n.tag=='div':
        e=els(n)
        kids_cards = e and all(x.tag in ('div','article') and (art(x) or tier(x) or qa(x) or predrow(x) or card(x) or pair_card(x) or kv(x) or step(x) or numcard(x)) for x in e)
        if kids_cards:
            if any(qa(x) for x in e): klass='qalist'
            elif any(predrow(x) for x in e): klass='plist'
            elif any(art(x) or tier(x) or card(x) or pair_card(x) or step(x) or numcard(x) for x in e): klass='sgrid'
            else: klass='kvrow'
            return f'<div class="{klass}">{inner}</div>'
        if leaf(n) and clean(txt(n)):
            t=spanjoin(n)
            return f'<p>{t}</p>'
        return f'<div>{inner}</div>'
    return f'<{n.tag}{attrstr(n.attrs)}>{inner}</{n.tag}>'

def strip_hero(root, title, lead, kicker):
    """знімає дубль шапки, який уже виводить сторінка"""
    def drop(n):
        e=[k for k in n.kids if k.tag!='#text']
        kill=set()
        for i,k in enumerate(e):
            if k.tag=='h1' and title and clean(txt(k))==clean(title):
                kill.add(id(k))
                if i>0 and e[i-1].tag=='div' and leaf(e[i-1]) and len(clean(txt(e[i-1])))<=40:
                    kill.add(id(e[i-1]))
                if i+1<len(e) and e[i+1].tag in ('p','div') and leaf(e[i+1]) and lead \
                   and clean(txt(e[i+1]))==clean(lead):
                    kill.add(id(e[i+1]))
        out=[]
        for k in n.kids:
            if k.tag=='#text': out.append(k); continue
            if id(k) in kill: continue
            t=clean(txt(k))
            if k.tag in ('div','p') and leaf(k) and lead and t==clean(lead): continue
            if k.tag=='div' and leaf(k) and kicker and t.lower()==clean(kicker).lower(): continue
            drop(k); out.append(k)
        n.kids=out
    drop(root); return root

def _block_end(h, start):
    """кінець дів-блоку, що починається на start"""
    i=start; depth=0
    while i < len(h):
        m=re.compile(r'<(/?)div\b').search(h, i)
        if not m: return len(h)
        if m.group(1): 
            depth-=1
            if depth==0: return h.index('>', m.end())+1
        else: depth+=1
        i=m.end()
    return len(h)

def dedupe_tiers(h):
    """сторінка не показує ті самі тарифи двічі: лишається перший блок"""
    spans=[]; pos=0
    while True:
        i=h.find('<div class="sgrid">', pos)
        if i<0: break
        e=_block_end(h, i)
        if 'scard tier' in h[i:e]: spans.append((i,e))
        pos=e
    if len(spans)<2: return h
    out=h
    for i,e in reversed(spans[1:]):
        cut=i
        head=out.rfind('<div class="kick">', 0, i)
        h2=out.rfind('<h2>', 0, i)
        for cand in (head, h2):
            if cand>=0 and i-cand < 320: cut=min(cut, cand)
        out=out[:cut]+out[e:]
    return out

def fix(body, title='', lead='', kicker=''):
    root=parse(body)
    strip_hero(root, title, lead, kicker)
    return dedupe_tiers(walk(root))

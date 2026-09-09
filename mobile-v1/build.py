#!/usr/bin/env python3
"""
HUNCH MOBILE — збірка прототипу з нуля. 5 Sep 2026.
Контент береться як є: Echo/маркети з content-2026/*.json,
статичні сторінки — витяг тексту з чинних HTML.
Стилі, блоки і організація — нові (m.css).
Нічого не дописується.
"""
import json, os, re, glob, html as H
import staticfix
from datetime import datetime

SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.dirname(os.path.abspath(__file__))
# Веб-режим (Pavlo 7 Sep: одне джерело для мобільної і веб). Збірка йде у вкладені теки як web-draft2.
OUT_WEB = os.environ.get('HUNCH_OUT_WEB') or os.path.join(os.path.dirname(OUT),'web-draft2')
VER = datetime.now().strftime('%Y%m%d%H%M')
SITE = os.environ.get('HUNCH_SITE','https://readhunch.com')   # перший реліз на readhunch.com (Pavlo 7 Sep); бренд лишається byhunch.com
PUBLIC = os.environ.get('HUNCH_PUBLIC','0')=='1'               # 0 = noindex + robots Disallow (до резолюції ринків); 1 = відкрито для пошуку
META = {}                                                        # slug → (description, og-image path у веб-дереві), заповнює main()   # версія в ?v= для css/js — кеш Safari не бреше
CONTENT = os.path.join(SRC, 'content-2026')

CATS = [('politics','Politics'),('sports','Sports'),('finance','Finance'),
        ('tech','Tech'),('culture','Culture'),('regional','Regional')]
ECHO116 = 'zelenskyy-office-purge'
FEATURED_SLUG = None   # прибити Featured головної вручну: 'slug' або None = автоправило

# ---------------------------------------------------------------- утиліти
def esc(s): return H.escape(str(s or ''), quote=False)

def load_echoes():
    out=[]
    for cat,_ in CATS:
        for f in sorted(glob.glob(os.path.join(CONTENT,cat,'*.json'))):
            try: d=json.load(open(f,encoding='utf-8'))
            except Exception: continue
            if d.get('slug'): out.append(d)
    out.sort(key=lambda d: d.get('date',''), reverse=True)
    return out

ALLOWED = re.compile(r'</?(a|em|strong|b|i|br)\b[^>]*>', re.I)
def rich(t):
    """наш власний контент: лишаємо a/em/strong/b/i/br, решту тегів екрануємо"""
    t = str(t or '')
    parts=[]; last=0
    for m in ALLOWED.finditer(t):
        parts.append(H.escape(t[last:m.start()], quote=False)); parts.append(m.group(0)); last=m.end()
    parts.append(H.escape(t[last:], quote=False))
    return ''.join(parts)

def fmt_date(d, full=False):
    """2026-08-21 -> '21 Aug' або '21 Aug 2026'. Формат тільки, зміст не міняється."""
    try:
        dt=datetime.strptime(str(d)[:10], '%Y-%m-%d')
    except Exception:
        return str(d or '')
    return dt.strftime('%d %b %Y') if full else dt.strftime('%d %b')

def pat_frac(e):
    b=e.get('base_rate') or {}
    if b.get('num') is not None and b.get('den'): return b['num'], b['den']
    return None, None

def pat_pct(e):
    n,d=pat_frac(e)
    return round(100*n/d) if n is not None and d else None

def mk_pp(e, m):
    """History для конкретного ринку: база Echo, інвертована, якщо ринок питає протилежне патерну (аудит 7 Sep, hist_inverse)."""
    pp=pat_pct(e); n,d=pat_frac(e)
    if m and m.get('adjacent'): return None,None,None   # суміжний ринок: база патерну не переноситься, History не показуємо
    if m and m.get('hist_inverse') and pp is not None and n is not None: return 100-pp, d-n, d
    return pp,n,d

def first_market(e):
    for m in (e.get('markets') or []):
        if m.get('status')=='live': return m
    return (e.get('markets') or [None])[0]

# ---------------------------------------------------------------- каркас
ICON_SHARE='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.6" y1="13.5" x2="15.4" y2="17.5"/><line x1="15.4" y1="6.5" x2="8.6" y2="10.5"/></svg>'
ICON_SAVE='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>'
ICON_CMT='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 11.5a8.4 8.4 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.4 8.4 0 0 1-3.8-.9L3 21l1.9-5.7a8.4 8.4 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.4 8.4 0 0 1 3.8-.9h.5a8.5 8.5 0 0 1 8 8v.5z"/></svg>'
ICON_HOME='<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M3.5 10.2 12 3.6l8.5 6.6V20a1 1 0 0 1-1 1h-15a1 1 0 0 1-1-1z" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/><path d="M9.6 21v-6.2h4.8V21" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/></svg>'
ICON_THEME='<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="12" cy="12" r="8.2" stroke="currentColor" stroke-width="1.8"/><path d="M12 3.8a8.2 8.2 0 0 0 0 16.4z" fill="currentColor"/></svg>'
ICON_SUN='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>'
ICON_MOON='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M20 14.5A8.5 8.5 0 1 1 9.5 4a6.8 6.8 0 0 0 10.5 10.5z"/></svg>'
ICON_MENU='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M3 6h18M3 12h18M3 18h18"/></svg>'

def cats_bar(active):
    home_on = ' class="home on"' if active in ('', 'index') else ' class="home"'
    parts=['<a href="index{D}"'+home_on+'>Today</a>']
    for s,n in CATS:
        cls=' class="on"' if s==active else ''
        parts.append('<a href="'+s+'{D}"'+cls+'>'+n+'</a>')
    return '<nav class="cats">'+''.join(parts)+'</nav>'


MENU_GROUPS=[
 ('Read',[('index','Today'),('echo-library','Echo library'),('archive','Archive')]),  # Patterns і Sources зняті (Pavlo 7 Sep)
 ('Predict',[('markets','Markets'),('leaderboard','Leaderboard'),('methodology','Methodology')]),
 ('Account',[('membership','Membership'),('signin','Sign in'),('account','Your account'),('mobile-app','Mobile app')]),
]

def menu(slug=''):
    g=''
    for h,items in MENU_GROUPS:
        links=''.join(f'<a href="{s}{{D}}">{n}</a>' for s,n in items)
        g+=f'<div class="menu-g"><div class="ft-h">{h}</div>{links}</div>'
    _unused=('<div class="menu-g"><div class="ft-h">Appearance</div>'
           '<div class="thm">'
           f'<a class="thm-o on" href="{slug}.html" aria-current="true">{ICON_SUN}<span>Light</span></a>'
           f'<a class="thm-o" href="{slug}-dark.html">{ICON_MOON}<span>Dark</span></a>'
           '</div></div>')
    _unused2=('<div class="menu-g"><div class="ft-h">Appearance</div>'
           '<div class="thm">'
           f'<a class="thm-o" href="{slug}.html">{ICON_SUN}<span>Light</span></a>'
           f'<a class="thm-o on" href="{slug}-dark.html" aria-current="true">{ICON_MOON}<span>Dark</span></a>'
           '</div></div>')
    return ('<div class="menu" id="menu"><div class="menu-top">'
            '{THEME}'
            '<button class="menu-x" id="mx" aria-label="Close">&times;</button></div>'
            f'{g}</div>')

FOOT_COLS=[('Read',[('index','Today'),('markets','Markets'),('echo-library','Echo'),
                    ('archive','Archive'),('newsletter','Blog'),('api','API')]),
           ('Topics',[('politics','Politics'),('sports','Sports'),('finance','Finance'),('tech','Tech')]),
           ('Company',[('about','About'),('methodology','How it works'),('careers','Careers'),
                       ('press','Press'),('partners','Partners'),('contact','Contact')]),
           ('Legal',[('terms','Terms'),('privacy','Privacy'),('cookies','Cookies'),
                     ('licences','Licences'),('editorial-code','Editorial Code'),
                     ('responsible-play','Responsible play')])]

def footer():
    cols=''
    for h,items in FOOT_COLS:
        links=''.join(f'<a href="{s}{{D}}">{n}</a>' for s,n in items)
        cols+=f'<div><div class="ft-h">{h}</div>{links}</div>'
    return ('<footer class="ft"><div class="ft-wm">Hunch<sup>&reg;</sup></div>'
            '<div class="ft-tag">Intuition based on experience</div>'
            '<div class="ft-social"><a href="https://x.com/readhunch" aria-label="X" title="X" target="_blank" rel="noopener"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg></a><a href="https://www.linkedin.com/company/123234090/" aria-label="LinkedIn" title="LinkedIn" target="_blank" rel="noopener"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.063 2.063 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg></a><span class="soon" aria-label="Instagram — soon" title="Instagram — soon"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/></svg></span><span class="soon" aria-label="YouTube — soon" title="YouTube — soon"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg></span><span class="soon" aria-label="Substack — soon" title="Substack — soon"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M22.539 8.242H1.46V5.406h21.08v2.836zM1.46 10.812V24L12 18.11 22.54 24V10.812H1.46zM22.54 0H1.46v2.836h21.08V0z"/></svg></span><span class="soon" aria-label="RSS — soon" title="RSS — soon"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M19.199 24C19.199 13.467 10.533 4.8 0 4.8V0c13.165 0 24 10.835 24 24h-4.801zM3.291 17.415a3.293 3.293 0 100 6.585c1.817 0 3.295-1.474 3.295-3.291S5.108 17.415 3.291 17.415zM15.909 24h-4.665C11.243 17.736 6.264 12.759 0 12.756v-4.668c8.833.003 15.905 7.075 15.909 15.912z"/></svg></span></div>'
            f'<div class="ft-cols">{cols}</div>'
            '<div class="ft-legal">&copy; Krok Group Ltd 2026. HUNCH is a registered trade mark of '
            'Krok Group Ltd (UK00004388957). Company No. 17183343 &middot; Registered in England &amp; Wales. '
            'Hunch Points carry no monetary value and cannot be exchanged for money or prizes. '
            'Forecasting is free to all registered readers.</div></footer>')

JS = ("<script>(function(){var b=document.getElementById('mb'),m=document.getElementById('menu'),"
      "x=document.getElementById('mx');if(b)b.onclick=function(){m.classList.add('open')};"
      "if(x)x.onclick=function(){m.classList.remove('open')};"
      "var mb2=document.getElementById('moreBtn'),ol=document.getElementById('older');"
      "if(mb2&&ol)mb2.onclick=function(){ol.hidden=false;mb2.remove();};"
      "var acts=document.querySelectorAll('.art-m .act');"
      "if(acts.length){var ack=document.createElement('span');ack.className='act-ack';"
      "ack.setAttribute('aria-live','polite');acts[0].parentNode.appendChild(ack);"
      "var key='hunch.saved:'+location.pathname.split('/').pop();"
      "if(localStorage.getItem(key))acts[1].classList.add('on');"
      "acts[0].onclick=function(){if(document.getElementById('shareModal'))return;var u=location.href,t=document.title;"
      "if(navigator.share){navigator.share({title:t,url:u});return;}"
      "if(navigator.clipboard)navigator.clipboard.writeText(u);ack.textContent='Link copied';"
      "setTimeout(function(){ack.textContent=''},2000);};"
      "acts[1].onclick=function(){var on=acts[1].classList.toggle('on');"
      "if(on)localStorage.setItem(key,'1');else localStorage.removeItem(key);"
      "ack.textContent=on?'Saved':'Removed';setTimeout(function(){ack.textContent=''},2000);};"
      "acts[2].onclick=function(){var c=document.getElementById('comment');"
      "if(c)c.scrollIntoView({behavior:'smooth',block:'center'});};}"
      "})();</script>")


SHEET = ("<div class=\"fc-bd\" id=\"fcBd\" hidden></div>"
 "<div class=\"fc\" id=\"fcSheet\" role=\"dialog\" aria-modal=\"true\" aria-label=\"Your forecast\" hidden></div>"
 "<script>(function(){"
 "var COM=.05,START=2500;"
 "function ls(k,d){try{return JSON.parse(localStorage.getItem(k))||d}catch(e){return d}}"
 "function st(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}}"
 "function bal(){return Math.max(0,START-ls('hunch_calls',[]).reduce(function(s,c){return s+(c.stake||0)},0))}"
 "function fmt(n){return Math.round(n).toLocaleString('en-GB')}"
 "var bd=document.getElementById('fcBd'),sh=document.getElementById('fcSheet'),S=null,src=null;"
 "function pct(){if(S.m.type!=='binary'){var o=(S.m.options||[]).filter(function(x){return x.name===S.pick})[0];return o?o.pct:50}"
 "return S.side==='yes'?S.m.yes:100-S.m.yes}"
 "function calc(){var p=Math.max(1,pct())/100;var sh2=S.amt/p;return{p:p,win:Math.max(0,(sh2-S.amt)*(1-COM))}}"
 "function esc(s){return String(s).replace(/[&<>\"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[c]})}"
 "function html(){var m=S.m,c=calc(),p=pct();var pill='<span class=\"fc-pill'+(m.type==='binary'&&S.side==='no'?' no':'')+'\">'+(m.type==='binary'?(S.side==='yes'?'Yes ':'No ')+p+'%':p+'%')+'</span>';"
 "var pick='';"
 "if(m.type==='binary'){pick='<div class=\"fc-tabs\"><button class=\"fc-tab'+(S.side==='yes'?' on':'')+'\" data-side=\"yes\">Yes <b>'+m.yes+'%</b></button>'"
 "+'<button class=\"fc-tab no'+(S.side==='no'?' on':'')+'\" data-side=\"no\">No <b>'+(100-m.yes)+'%</b></button></div>'}"
 "else{pick='<div class=\"fc-opts\">'+(m.options||[]).map(function(o){return '<button class=\"fc-opt'+(o.name===S.pick?' on':'')+'\" data-pick=\"'+esc(o.name)+'\"><span>'+esc(o.name)+'</span><b>'+o.pct+'%</b></button>'}).join('')+'</div>'}"
 "return '<div class=\"fc-grip\"></div>'"
 "+'<div class=\"fc-hd\"><span class=\"fc-t\">Your hunch</span>'+pill+'<button class=\"fc-x\" data-close aria-label=\"Close\">&times;</button></div>'"
 "+'<p class=\"fc-q\">'+esc(m.q)+'</p>'+pick"
 "+'<div class=\"fc-lbl\"><span>Amount</span><span>Balance '+fmt(bal())+' HP</span></div>'"
 "+'<div class=\"fc-amt\"><input type=\"text\" inputmode=\"numeric\" id=\"fcAmt\" value=\"'+S.amt+'\" aria-label=\"Amount in Hunch Points\"><span>HP</span></div>'"
 "+'<div class=\"fc-chips\"><button data-add=\"10\">+10</button><button data-add=\"50\">+50</button><button data-add=\"100\">+100</button><button data-max>Max</button></div>'"
 "+'<div class=\"fc-calc\"><div class=\"fc-row\"><span>Avg price</span><span>'+Math.round(c.p*100)+' HP / share</span></div>'"
 "+'<div class=\"fc-row win\"><span>If you are right</span><span class=\"v\">+'+fmt(c.win)+' HP</span></div></div>'"
 "+'<button class=\"fc-cta'+(m.type==='binary'&&S.side==='no'?' no':'')+'\" data-go>Sign '+fmt(S.amt)+' HP on '+(m.type==='binary'?(S.side==='yes'?'Yes':'No'):'this outcome')+'</button>'"
 "+'<p class=\"fc-fine\">Parimutuel pool. Hunch Points only, no money.</p>'}"
 "function draw(){sh.innerHTML=html();"
 "sh.querySelectorAll('[data-side]').forEach(function(x){x.onclick=function(){S.side=x.dataset.side;draw()}});"
 "sh.querySelectorAll('[data-pick]').forEach(function(x){x.onclick=function(){S.pick=x.dataset.pick;draw()}});"
 "sh.querySelectorAll('[data-add]').forEach(function(x){x.onclick=function(){S.amt+=+x.dataset.add;draw()}});"
 "var mx=sh.querySelector('[data-max]');if(mx)mx.onclick=function(){S.amt=bal();draw()};"
 "var a=sh.querySelector('#fcAmt');if(a)a.oninput=function(){S.amt=Math.max(0,parseInt(a.value.replace(/\\D/g,''),10)||0);var c=calc();"
 "var w=sh.querySelector('.fc-row.win .v');if(w)w.textContent='+'+fmt(c.win)+' HP';"
 "var g=sh.querySelector('[data-go]');if(g)g.textContent='Sign '+fmt(S.amt)+' HP on '+(S.m.type==='binary'?(S.side==='yes'?'Yes':'No'):'this outcome')};"
 "var x=sh.querySelector('[data-close]');if(x)x.onclick=close_;"
 "var g=sh.querySelector('[data-go]');if(g)g.onclick=function(){"
 "if(S.amt<=0){g.textContent='Enter an amount';return}"
 "if(S.amt>bal()){g.textContent='Not enough HP';return}"
 "var calls=ls('hunch_calls',[]);calls.push({q:S.m.q,side:S.side,pick:S.pick,stake:S.amt,ts:Date.now()});st('hunch_calls',calls);"
 "g.textContent='Signed';"
 "if(src){var box=src.closest('.mk');box.querySelectorAll('.btn').forEach(function(e){e.classList.remove('on')});"
 "var win=box.querySelectorAll('.btn');var lbl=S.m.type==='binary'?(S.side==='yes'?'Yes':'No'):S.pick;"
 "win.forEach(function(e){if(e.textContent.trim()===lbl)e.classList.add('on')});"
 "var ack=box.querySelector('.mk-ack');if(ack)ack.textContent='Forecast recorded: '+lbl+' \u00b7 '+fmt(S.amt)+' HP. Points only, no money.'}"
 "setTimeout(close_,700)}}"
 "function open_(m,side,pick,el){src=el;S={m:m,side:side||'yes',pick:pick||(m.options&&m.options[0]&&m.options[0].name),amt:100};"
 "draw();bd.hidden=false;sh.hidden=false;requestAnimationFrame(function(){bd.classList.add('on');sh.classList.add('on')});"
 "document.body.style.overflow='hidden'}"
 "function close_(){bd.classList.remove('on');sh.classList.remove('on');document.body.style.overflow='';"
 "setTimeout(function(){bd.hidden=true;sh.hidden=true},200)}"
 "bd.onclick=close_;document.addEventListener('keydown',function(e){if(e.key==='Escape'&&!sh.hidden)close_()});"
 "document.addEventListener('click',function(e){var t=e.target.closest('.mk .btn[data-fc]');if(!t)return;e.preventDefault();"
 "try{open_(JSON.parse(t.dataset.fc),t.dataset.side,t.dataset.pick,t)}catch(err){}});"
 "})();</script>")

def theme_switch(slug, dark):
    """Просто іконка. Стоїть у рядку із хрестиком, ліворуч."""
    href = f'{slug}.html' if dark else f'{slug}-dark.html'
    to   = 'Light' if dark else 'Dark'
    return (f'<a class="thm-ic" href="{href}" aria-label="Switch to {to}" title="{to}">'
            f'{ICON_THEME}</a>')


DOC_JS=('<script>(function(){'
 'document.querySelectorAll(".doc-page .toggle:not(.locked)").forEach(function(t){t.addEventListener("click",function(){t.classList.toggle("on")})});'
 'document.querySelectorAll(".doc-page form").forEach(function(f){f.addEventListener("submit",function(e){e.preventDefault();var n=f.querySelector(".form-note");if(!n){n=document.createElement("p");n.className="form-note";f.appendChild(n)}n.textContent="Thank you. We reply within two working days."})});'
 'var secs=Array.prototype.slice.call(document.querySelectorAll(".doc-grid h2[id]")),links=Array.prototype.slice.call(document.querySelectorAll(".toc a[href^=\\"#\\"]"));'
 'if(secs.length&&links.length){var map={};links.forEach(function(a){map[a.getAttribute("href").slice(1)]=a});'
 'function on(){var cur=secs[0].id;secs.forEach(function(s){if(s.getBoundingClientRect().top-120<=0)cur=s.id});links.forEach(function(a){a.classList.remove("active")});if(map[cur])map[cur].classList.add("active")}'
 'document.addEventListener("scroll",on,{passive:true});on()}'
 '})();</script>')

ICON_SEARCH='<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>'
ICON_BURGER='<svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>'
H_MARK='<svg class="mh-mark" viewBox="0 0 100 100" width="20" height="20" aria-hidden="true"><rect x="3" y="3" width="94" height="94" rx="14" fill="#FFFDF7" stroke="#7A5210" stroke-width="2"/><text x="50" y="73" font-family="Cormorant Garamond, Garamond, serif" font-size="80" font-weight="600" fill="#7A5210" text-anchor="middle">H</text></svg>'
def web_header(active):
    """Веб-шапка (≥1024): лупа, дата, вордмарк, Sign in, бургер; другий ряд — категорії і Subscribe. Лінки плоскі, переписує web_links()."""
    tabs='<a href="index{D}"'+(' class="on"' if active in ('','index') else '')+'>Today</a>'
    for s,n in CATS:
        tabs+=f'<a href="{s}{{D}}"'+(' class="on"' if s==active else '')+f'>{n}</a>'
    return ('<header class="mh"><div class="mh-r1"><div class="mh-l"><button class="mh-s" type="button" aria-label="Search">'+ICON_SEARCH+'</button>'
            '<span class="mh-d" id="mhDate"></span></div><a class="mh-b" href="index{D}">Hunch<sup>&reg;</sup></a>'
            '<div class="mh-rt"><a class="mh-si" href="signin{D}">Sign in</a><button class="mh-m" type="button" aria-label="Menu">'+ICON_BURGER+'</button></div></div>'
            '<nav class="mh-r2"><div class="mh-t">'+tabs+'<span class="mh-sep"></span><a class="mh-sub" href="membership{D}">'+H_MARK+'Subscribe</a></div></nav></header>')

WEB_JS=("<script>(function(){var b=document.querySelector('.mh-m');var m=document.getElementById('mb');var panel=document.getElementById('menu');"
 "var bd=document.createElement('div');bd.className='mh-bd';document.body.appendChild(bd);"
 "function close(){panel.classList.remove('open');bd.classList.remove('on');document.body.style.overflow='';}"
 "function open(){panel.classList.add('open');bd.classList.add('on');document.body.style.overflow='hidden';}"
 "if(b)b.onclick=function(){open()};if(m)m.onclick=function(){open()};var x=document.getElementById('mx');if(x)x.onclick=close;bd.onclick=close;"
 "document.addEventListener('keydown',function(e){if(e.key==='Escape')close();});"
 "var d=document.getElementById('mhDate');if(d){var n=new Date();var W=['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];var M=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];"
 "d.textContent=(W[n.getDay()]+', '+n.getDate()+' '+M[n.getMonth()]+' '+n.getFullYear()).toUpperCase();}})();</script>")

ECHO_CAT={}   # slug → category, заповнює main()
def web_path(flat, dark):
    """Плоске імʼя сторінки → шлях у веб-дереві. index → index.html; echo-x → cat/x/index.html; y → y/index.html; dark → …/dark/index.html"""
    d='dark/' if dark else ''
    if flat=='index': return d+'index.html'
    if flat.startswith('echo-'):
        s=flat[5:]; return f'{ECHO_CAT.get(s,"echo")}/{s}/{d}index.html'
    return f'{flat}/{d}index.html'
def web_links(html, cur_dir):
    """Переписує плоскі href="x.html" / "x-dark.html" на відносні шляхи веб-дерева."""
    def f(m):
        name=m.group(1); dark=name.endswith('-dark')
        flat=name[:-5] if dark else name
        tgt=web_path(flat,dark)
        rel=os.path.relpath(tgt, cur_dir or '.').replace(os.sep,'/')
        # чисті адреси без index.html (Pavlo 7 Sep): GitHub Pages віддає index.html за текою
        if rel.endswith('index.html'): rel=rel[:-len('index.html')] or './'
        return 'href="'+rel+'"'
    return re.sub(r'href="([A-Za-z0-9_\-]+)\.html"', f, html)

# ---------------------------------------------------------------- кукі-плашка (Pavlo 7 Sep): лише необхідне сховище; вибір у localStorage hunch_consent
COOKIE_BAR=('<div class="ck" id="ck" hidden><p>We use only essential storage: your theme, saved Echoes and your calls stay in this browser. '
            'Optional analytics is off until you allow it. <a href="cookies{D}">Cookie settings</a></p>'
            '<div class="ck-b"><button type="button" class="ck-ok" data-ck="all">Accept</button><button type="button" class="ck-no" data-ck="essential">Essential only</button></div></div>')
CONSENT_JS=("<script>(function(){var t=document.querySelector('.thm-ic');if(t)t.addEventListener('click',function(){try{localStorage.setItem('hunch_theme',/Switch to Dark/.test(t.getAttribute('aria-label')||'')?'dark':'light')}catch(e){}});})();</script>"
 "<script>(function(){var K='hunch_consent';function get(){try{return localStorage.getItem(K)}catch(e){return null}}function set(v){try{localStorage.setItem(K,v)}catch(e){}}"
 "var bar=document.getElementById('ck');if(bar&&!get()){bar.hidden=false;bar.querySelectorAll('[data-ck]').forEach(function(x){x.onclick=function(){set(x.getAttribute('data-ck'));bar.hidden=true}})}"
 "var page=document.querySelector('.doc-page .cookie-card');if(page){var cards=document.querySelectorAll('.doc-page .cookie-card');"
 "function apply(v){cards.forEach(function(c){var t=c.querySelector('.toggle');if(!t||t.classList.contains('locked'))return;var name=(c.querySelector('h3')||{}).textContent||'';"
 "if(/preferences/i.test(name))t.classList.add('on');else t.classList.toggle('on',v==='all')})}"
 "apply(get()||'essential');"
 "document.querySelectorAll('.doc-page .btn-primary,.doc-page .btn-secondary').forEach(function(btn){var tx=btn.textContent.trim().toLowerCase();"
 "if(/save/.test(tx))btn.addEventListener('click',function(e){e.preventDefault();var any=false;cards.forEach(function(c){var t=c.querySelector('.toggle');var n=(c.querySelector('h3')||{}).textContent||'';if(t&&!t.classList.contains('locked')&&!/preferences/i.test(n)&&t.classList.contains('on'))any=true});set(any?'all':'essential');btn.textContent='Saved';setTimeout(function(){btn.textContent='Save preferences'},1600)});"
 "if(/reject/.test(tx))btn.addEventListener('click',function(e){e.preventDefault();set('essential');apply('essential');btn.textContent='Done';setTimeout(function(){btn.textContent='Reject all optional'},1600)})})}"
 "window.hunchConsent=get;})();</script>")

def shell(title, body, active='', dark=False, slug='', web=False):
    D='-dark.html' if dark else '.html'
    attr=' data-theme="dark"' if dark else ''
    if web:
        tgt=web_path(slug if slug else 'index', dark); cur=os.path.dirname(tgt)
        rel=os.path.relpath('assets', cur or '.').replace(os.sep,'/')+'/'
        css=(f'<link rel="stylesheet" href="{rel}m.css?v={VER}"><link rel="stylesheet" href="{rel}doc.css?v={VER}">')
        tail=(f'<script src="{rel}hunch-search.js?v={VER}" defer></script><script src="{rel}list.js?v={VER}" defer></script>')
        head_extra=web_header(active)
    else:
        css=(f'<link rel="stylesheet" href="m.css?v={VER}"><link rel="stylesheet" href="doc.css?v={VER}">')
        tail=(f'<script src="hunch-search.js?v={VER}" defer></script><script src="list.js?v={VER}" defer></script>')
        head_extra=web_header(active)   # плоска збірка теж адаптивна: на широкому екрані без веб-шапки шапки не було зовсім (Pavlo 7 Sep 14:01)
    m=META.get(slug or 'index') or {}
    desc=m.get('desc') or 'Hunch pairs the news with the historical pattern behind it, and lets readers call what happens next.'
    light_path=web_path(slug if slug else 'index', False); canon=SITE+'/'+light_path.replace('index.html','')
    og_img=SITE+'/'+(m.get('og') or 'assets/og-default.png')
    robots='<meta name="robots" content="index,follow">' if PUBLIC else '<meta name="robots" content="noindex,nofollow,noarchive">'
    icons_rel=(rel if web else '')   # web: assets/…, flat: поруч із html
    seo=(robots+f'<meta name="description" content="{esc(desc)}"><link rel="canonical" href="{canon}">'
         f'<meta property="og:type" content="{"article" if (slug or "").startswith("echo-") else "website"}"><meta property="og:site_name" content="Hunch">'
         f'<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{canon}">'
         f'<meta property="og:image" content="{og_img}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'
         f'<meta name="twitter:card" content="summary_large_image"><meta name="twitter:site" content="@readhunch"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(desc)}"><meta name="twitter:image" content="{og_img}">'
         f'<link rel="icon" href="{icons_rel}favicon.ico" sizes="any"><link rel="icon" type="image/svg+xml" href="{icons_rel}favicon.svg"><link rel="apple-touch-icon" href="{icons_rel}apple-touch-icon.png">'
         f'<meta name="theme-color" content="{"#0E0F11" if dark else "#FAF7EF"}">'
         # заголовки безпеки мета-тегами: GitHub Pages не дає власних HTTP-заголовків (7 Sep). Дозволяємо лише свій код і Google Fonts.
         '<meta http-equiv="Content-Security-Policy" content="default-src \'self\'; script-src \'self\' \'unsafe-inline\'; style-src \'self\' \'unsafe-inline\' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src \'self\' data:; connect-src \'none\'; frame-ancestors \'none\'; base-uri \'self\'; form-action \'self\'">'
         '<meta name="referrer" content="strict-origin-when-cross-origin">')
    # тема з пристрою (Pavlo 7 Sep): без збереженого вибору беремо prefers-color-scheme і йдемо на близнюка; ручний вибір у меню = localStorage hunch_theme
    if web:
        twin=os.path.relpath(web_path(slug if slug else 'index', not dark), cur or '.').replace(os.sep,'/')
        if twin.endswith('index.html'): twin=twin[:-len('index.html')] or './'
    else:
        twin=(slug or 'index')+('.html' if dark else '-dark.html')
    theme_js=("<script>(function(){try{var s=localStorage.getItem('hunch_theme');var d="+('true' if dark else 'false')+";"
              "var want=s?s:(window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');"
              "if((want==='dark')!==d){location.replace('"+twin+"'+location.search+location.hash)}}catch(e){}})();</script>")
    redirect=''
    if slug=='account':
        tgt=(os.path.relpath(web_path('signin',dark), cur or '.').replace(os.sep,'/') if web else 'signin'+D)
        if tgt.endswith('index.html'): tgt=tgt[:-len('index.html')] or './'
        redirect=f'<meta http-equiv="refresh" content="0;url={tgt}"><script>location.replace("{tgt}")</script>'
    doc=(f'<!doctype html><html lang="en"{attr}>'
         '<head><meta charset="utf-8">'+theme_js+redirect+
         '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
         + seo +
         f'<title>{esc(title)} — Hunch</title>'
         '<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,wght@0,400;0,600;1,400&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">'
         + css + '</head><body>' + head_extra +
         '<header class="bar">'
         '<button class="bar-btn" id="mb" aria-label="Menu">'+ICON_MENU+'</button>'
         '<a class="bar-wm" href="index{D}">Hunch<sup>&reg;</sup></a>'
         '<a class="bar-act" href="signin{D}">Sign in</a></header>'
         + cats_bar(active) + menu(slug).replace('{THEME}', theme_switch(slug, dark))
         + f'<main>{body}</main>' + footer() + COOKIE_BAR + SHEET + JS + WEB_JS + tail + DOC_JS + SHARE_JS + CONSENT_JS + '</body></html>')
    doc=re.sub(r'[A-Za-z0-9._-]+@byhunch\.com','info@byhunch.com',doc)  # одна публічна адреса (Pavlo 7 Sep)
    doc=doc.replace('{D}', D).replace('.html-dark.html','-dark.html')
    if web:
        doc=web_links(doc, cur)
        doc=doc.replace('src="share/','src="'+rel+'share/').replace('href="share/','href="'+rel+'share/')
    return doc

# ---------------------------------------------------------------- блоки
def feat_block(e):
    """фіч-ехо: однаковий на головній і в категоріях"""
    m=first_market(e); pp,n,d=mk_pp(e,m)
    slug=e['slug']
    pat=''
    if n is not None:
        pat=(f'<p class="pat"><b>{n} of {d}</b>'
             f'<span>{esc((e.get("pattern") or {}).get("card_echo") or (e.get("base_rate") or {}).get("text",""))}</span></p>')
    q=f'<p class="q">{esc(m["question"])}</p>' if m and m.get('question') else ''
    gap=''
    if m and pp is not None and m.get('yes_pct') is not None:
        gap=(f'<div class="gap"><div><span class="k">History</span>'
             f'<span class="v h">{pp}%</span><span class="n">{n} of {d} cases</span></div>'
             f'<div><span class="k">Readers</span><span class="v r">{m["yes_pct"]}%</span>'
             f'<span class="n">say it repeats</span></div></div>')
    res=f'<div class="res">Resolves {esc(m.get("resolves",""))}</div>' if m and m.get('resolves') else ''
    side=f'<div class="feat-side">{q}{gap}{res}</div>' if (q or gap or res) else ''
    # кейси патерну з роками (веб ≥1024; на мобільному CSS ховає). Підпис: label, інакше короткий підмет із тексту
    cases=sorted((e.get('pattern') or {}).get('cases') or [], key=lambda c: -(c.get('year') or 0))[:8]   # у Featured показуємо не більше 8 останніх (Pavlo 7 Sep); база лишається повною
    def _lab(c):
        for k in ('label','title','name'):
            if c.get(k): return c[k]
        t=re.sub('<[^>]+>','',c.get('text','')); t=re.split(r',| was | created | published',t)[0].strip()
        return re.sub(r'^The ','',t)
    lst=('<ul class="pp-l inl">'+''.join(f'<li><b>{c.get("year","")}</b><span>{esc(_lab(c))}</span></li>' for c in cases if c.get('year'))+'</ul>') if cases else ''
    return (f'<article class="feat"><div class="feat-top">'
            f'<span class="kick acc">Featured</span><span class="date">{fmt_date(e.get("date",""))}</span></div>'
            f'<h1 class="feat-h"><a href="echo-{slug}{{D}}">{esc(e["headline"])}</a></h1>'
            f'<p class="feat-l">{esc(e.get("lead",""))}</p>{pat}{lst}{side}</article>')

def feed_item(e):
    pp=pat_pct(e); m=first_market(e)
    stat=''
    if pp is not None and m and m.get('yes_pct') is not None:
        stat=(f'<div class="item-m"><b>{pp}%</b><span class="ar">&rarr;</span>'
              f'<i>{m["yes_pct"]}%</i></div>')
    return (f'<article class="item"><div class="item-top">'
            f'<span class="kick">{esc(e.get("tag") or e.get("category",""))}</span>'
            f'<span class="date">{fmt_date(e.get("date",""))}</span></div>'
            f'<h2 class="item-h"><a href="echo-{e["slug"]}{{D}}">{esc(e["headline"])}</a></h2>'
            f'<p class="item-s">{esc(e.get("brief") or e.get("lead",""))}</p>{stat}</article>')

def sec_head(t, right=''):
    return (f'<div class="sep-hd"><span class="kick">{esc(t)}</span>'
            f'<span class="date">{esc(right)}</span></div>')


def feed_item_short(e):
    """Той самий компонент, але текст — рядок ехо (card_echo), до 4 рядків."""
    pp=pat_pct(e); m=first_market(e)
    txt=(e.get('pattern') or {}).get('card_echo') or e.get('brief','')
    stat=''
    if pp is not None and m and m.get('yes_pct') is not None:
        stat=(f'<div class="item-m"><b>{pp}%</b><span class="ar">&rarr;</span>'
              f'<i>{m["yes_pct"]}%</i></div>')
    return (f'<article class="item"><div class="item-top">'
            f'<span class="kick">{esc(e.get("tag") or e.get("category",""))}</span>'
            f'<span class="date">{fmt_date(e.get("date",""))}</span></div>'
            f'<h2 class="item-h"><a href="echo-{e["slug"]}{{D}}">{esc(e["headline"])}</a></h2>'
            f'<p class="item-s">{esc(txt)}</p>{stat}</article>')


def market_row(e, m):
    """Компактний ринок для головної: питання як заголовок, під ним патерн."""
    pp,n,d=mk_pp(e,m)
    txt=(e.get('pattern') or {}).get('card_echo') or ''
    stat=''
    if pp is not None and m.get('yes_pct') is not None:
        stat=(f'<div class="item-m"><b>{pp}%</b><span class="ar">&rarr;</span>'
              f'<i>{m["yes_pct"]}%</i>'
              f'<span class="mr-res">Resolves {esc(m.get("resolves",""))}</span></div>')
    elif pp is not None and (m.get('options') or []):
        # ринок з варіантами: частка лідера і сам варіант (Pavlo 7 Sep: без цифр і дати рядки виглядали порожніми)
        top=max(m['options'], key=lambda o: o.get('pct',0))
        stat=(f'<div class="item-m"><b>{pp}%</b><span class="ar">&rarr;</span>'
              f'<i>{top.get("pct",0)}%</i><span class="mr-opt">{esc(top.get("name",""))}</span>'
              f'<span class="mr-res">Resolves {esc(m.get("resolves",""))}</span></div>')
    return (f'<article class="item mrow">'
            f'<div class="item-top"><span class="kick">{esc(e.get("category","")).title()}</span>'
            f'<span class="date">{fmt_date(e.get("date",""))}</span></div>'
            f'<h2 class="item-h"><a href="echo-{e["slug"]}{{D}}">{esc(m.get("question",""))}</a></h2>'
            f'<p class="item-s">{esc(txt)}</p>{stat}</article>')


# ---------------------------------------------------------------- сторінки
SS=os.path.dirname(os.path.abspath(__file__))  # static2.jsonl тепер поруч; відновлюється static_extract.py
STATIC={}
for line in open(os.path.join(SS,'static2.jsonl'),encoding='utf-8'):
    r=json.loads(line); STATIC[r['src']]=r['d']

def pick_eow(E):
    """Echo тижня: серед 40 найсвіжіших — найсильніший патерн, не менше 4 кейсів."""
    best=None
    for e in E[:40]:
        b=e.get('base_rate') or {}
        n,d=b.get('num'),b.get('den')
        if not d or d<4 or n is None: continue
        cs=(e.get('pattern') or {}).get('cases') or []
        if len(cs)<3: continue
        score=(n/d, d)
        if best is None or score>best[0]: best=(score,e)
    return best[1] if best else (E[1] if len(E)>1 else E[0])


def eow_block(e):
    n,d=pat_frac(e); pp=pat_pct(e)
    cases=(e.get('pattern') or {}).get('cases') or []
    years=[str(c.get('year','')) for c in cases if c.get('year')]
    since=min(years) if years else ''
    intro=(e.get('pattern') or {}).get('summary') or (e.get('base_rate') or {}).get('text','')
    rows=''
    for c in cases:
        lab=(c.get('label') or '').strip()
        if not lab:
            # перше речення тексту кейса; розмітку лишаємо, крапку зберігаємо
            t=(c.get('text') or '').strip()
            m=re.search(r'^(.{20,150}?[.!?])(\s|$)', t)
            lab=(m.group(1) if m else t[:150])
        rows+=(f'<li><span class="y">{esc(c.get("year",""))}</span>'
               f'<span class="t">{rich(lab)}</span></li>')
    stat=''
    if pp is not None:
        stat=(f'<div class="eow-stat"><span class="v">{pp}%</span>'
              f'<span class="l">historical rate<i>&middot;</i>'
              f'{d} cases{" since " + since if since else ""}</span></div>')
    return (f'<section class="eow">'
            f'<div class="eow-top"><span class="eow-k">Echo of the week</span></div>'
            f'<h2 class="eow-h"><a href="echo-{e["slug"]}{{D}}">{esc(e["headline"])}</a></h2>'
            f'<p class="eow-i">{esc(intro)}</p>'
            f'<ul class="eow-cases">{rows}</ul>{stat}</section>')


def page_home(E):
    feat=E[0]
    used={feat['slug']}
    body=f'<div class="wrap">{feat_block(feat)}'

    # 1. девʼять Echo у повному форматі (Pavlo 7 Sep: 9, не 10)
    full=[e for e in E if e['slug'] not in used][:9]
    used |= {e['slug'] for e in full}
    body+=sec_head('Latest', f'{len(E)} Echoes')
    body+='<div class="feed">'+''.join(feed_item(e) for e in full)+'</div>'

    # 2. Echo of the week — один, розібраний детально
    eow=pick_eow([e for e in E if e['slug'] not in used])
    used.add(eow['slug'])
    body+=eow_block(eow)

    # 3. девʼять Echo у короткому форматі
    short=[e for e in E if e['slug'] not in used][:9]
    used |= {e['slug'] for e in short}
    body+=sec_head('More this week', str(len(short)))
    body+='<div class="feed">'+''.join(feed_item_short(e) for e in short)+'</div>'

    # 4. дванадцять ринків — з Echo, які ще не показані вище (Pavlo 7 Sep: 12)
    rows=[]
    for e in E:
        if e['slug'] in used: continue
        for m in (e.get('markets') or []):
            if m.get('status')=='live' and m.get('question'):
                rows.append((e,m)); used.add(e['slug']); break
        if len(rows)>=12: break
    body+=sec_head('Markets', f'{len(rows)} live')
    body+='<div class="feed">'+''.join(market_row(e,m) for e,m in rows)+'</div>'
    body+='</div>'
    return body


def page_cat(E, slug, name):
    sub=[e for e in E if e.get('category')==slug]
    if not sub:
        return f'<div class="wrap"><div class="pg"><h1 class="pg-h">{name}</h1></div></div>'
    # від найсвіжішого до найстаршого
    sub=sorted(sub, key=lambda x: x.get('date',''), reverse=True)
    feat=sub[0]; rest=sub[1:]
    full=rest[:10]; short=rest[10:20]; older=rest[20:]

    body=f'<div class="wrap">{feat_block(feat)}'
    if full:
        body+=sec_head(name, f'{len(sub)} Echoes')
        body+='<div class="feed">'+''.join(feed_item(e) for e in full)+'</div>'
    if short:
        body+=sec_head('More this week', str(len(short)))
        body+='<div class="feed">'+''.join(feed_item_short(e) for e in short)+'</div>'
    if older:
        body+=('<div class="feed more-hid" id="older" hidden>'
               +''.join(feed_item_short(e) for e in older)+'</div>')
        body+=(f'<button class="more-btn" id="moreBtn" type="button" '
               f'data-n="{len(older)}">More {esc(name.lower())} &rarr;</button>')

    # ринки: спершу з Echo, не показаних вище; якщо живих там немає — з решти
    rows=[]; shown={e['slug'] for e in [feat]+full+short}; taken=set()
    for prefer_unused in (True, False):
        for e in sub:
            if len(rows)>=10: break
            if e['slug'] in taken: continue
            if prefer_unused and e['slug'] in shown: continue
            for m in (e.get('markets') or []):
                if m.get('status')=='live' and m.get('question'):
                    rows.append((e,m)); taken.add(e['slug']); break
        if len(rows)>=10: break
    if rows:
        body+=sec_head('Markets', f'{len(rows)} live')
        body+='<div class="feed">'+''.join(market_row(e,m) for e,m in rows)+'</div>'
    body+='</div>'
    return body


def page_echo(e):
    n,d=pat_frac(e); pp=pat_pct(e)
    b=f'<div class="wrap"><div class="art-wrap"><div class="pg"><div class="art-head">'
    b+=(f'<div class="feat-top"><span class="kick acc">{esc(e.get("tag") or e.get("category",""))}</span>'
        f'<span class="date">{fmt_date(e.get("date",""), True)}</span></div>')
    b+=f'<h1 class="art-h">{esc(e["headline"])}</h1>'
    b+=f'<p class="art-l">{esc(e.get("lead",""))}</p>'
    b+=('<div class="art-m">'
        '<div class="acts">'
        f'<button class="act" type="button" id="ecShare" aria-label="Share this Echo">{ICON_SHARE}</button>'
        f'<button class="act" type="button" aria-label="Save this Echo">{ICON_SAVE}</button>'
        f'<button class="act" type="button" aria-label="Comments">{ICON_CMT}</button>'
        '</div>'
        f'<span class="rt">{esc(e.get("read_mins","4"))} min read</span></div>')
    b+='</div><div class="art-main">'
    # What happened
    t=e.get('today') or {}
    ev=e.get('event') or {}
    b+=art_sec(ev.get('h2') or 'What happened')
    if t.get('text'):
        b+=f'<p>{rich(t["text"])}</p>'
        if t.get('source'):
            u=t.get('url','')
            txt=f'({esc(t["source"])}, {esc(t.get("date",""))})'
            b+='<div class="src">'+(f'<a href="{esc(u)}">{txt}</a>' if u else txt)+'</div>'
    b+=''.join(f'<p>{rich(p)}</p>' for p in (ev.get('paras') or []))

    # The Echo
    pt=e.get('pattern') or {}
    if pt.get('h2'):
        b+=art_sec('The Pattern')
        if pt.get('intro'): b+=f'<p>{rich(pt["intro"])}</p>'
        for c in (pt.get('cases') or []):
            yr=c.get('year') or c.get('date') or ''
            txt=c.get('text') or c.get('summary') or ''
            b+=f'<div class="case"><div class="case-y">{esc(yr)}</div><div class="case-t">{rich(txt)}</div></div>'
        br=e.get('base_rate') or {}
        if br.get('text'):
            b+=(f'<div class="base"><div class="base-n">{n} of {d}</div>'
                f'<div class="base-t">{rich(br["text"])}</div></div>')
        if pt.get('summary'): b+=f'<p>{rich(pt["summary"])}</p>'
    exc=e.get('exclusions') or []
    if exc:
        b+='<h3 class="h">What this pattern excludes</h3>'
        for x in exc:
            b+=f'<div class="case"><div class="case-y">{esc(x.get("case",""))}</div><div class="case-t">{rich(x.get("reason",""))}</div></div>'

    # The Read
    rd=e.get('read') or {}
    if rd.get('paras'):
        b+=art_sec('The Read')
        b+=''.join(f'<p>{rich(p)}</p>' for p in (rd.get('paras') or []))

    b+='</div>'
    # The Market — на десктопі права колонка, на телефоні просто наступний блок
    mk=e.get('markets') or []
    if mk:
        b+='<aside class="art-rail">'+art_sec('The Market')
        vf=e.get('verify') or []
        for i,m in enumerate(mk):
            pp_,n_,d_=mk_pp(e,m)
            b+=market_block(m, pp_, n_, d_, verify=(vf[i] if i<len(vf) else ''))
        b+='</aside>'
    b+='<div class="art-tail">'+art_sec('Disclaimer')+DISC
    b+=art_sec('Comment')+CMT+'</div>'
    b+='</div></div></div>'
    _body=b
    return _body+share_modal(e)

def art_sec(t):
    return f'<h2 class="asec">{esc(t)}</h2>'

DISC=('<p class="disc">Hunch works only from sources that are publicly available, and publishes on the '
 'basis of analysis of that material. We do not form an editorial opinion or take sides, we give a '
 'simpler and wider view of news that already exists. If information in a source we used was '
 'inaccurate, distorted, or later disputed but had already entered our analysis, Hunch accepts no '
 'liability for that. Predictions are not advice. Phase 1 markets use Hunch Points, not money.</p>')

CMT=('<div class="cmt" id="comment">'
 '<textarea class="cmt-f" rows="3" maxlength="600" placeholder="Comments open with accounts, soon." disabled></textarea>'
 '<div class="cmt-r"><span class="cmt-h">Comments are moderated. Members post under their prediction record.</span>'
 '<button class="cmt-p" type="button" disabled>Post</button></div></div>')

def days_left(resolves):
    """Скільки днів лишилось до резолюції. Порожньо, якщо дата в минулому або не парситься."""
    from datetime import date, datetime
    for fmt in ('%d %b %Y','%d %B %Y','%Y-%m-%d'):
        try:
            d=datetime.strptime(resolves.strip(), fmt).date(); break
        except Exception:
            d=None
    if not d: return ''
    n=(d - date.today()).days
    return f'{n} days left' if n > 0 else ''

def market_block(m, pp=None, n=None, d=None, show_q=True, verify=''):
    yes=m.get('yes_pct')
    st=(m.get('status') or 'live').lower()
    opts=m.get('options') or []
    right=days_left(m.get('resolves','')) if st=='live' else ''
    if st=='live':
        left='<span class="lv"><b></b>Live</span>'
    else:
        left=f'<span class="lv off">{esc(st.capitalize())}</span>'
    head=f'<div class="mk-st">{left}<span class="rt">{right}</span></div>'
    rows=''
    if pp is not None:
        rows+=(f'<div class="pr"><span class="pl">History</span>'
               f'<span class="pt"><i class="h" style="width:{pp}%"></i></span>'
               f'<span class="pv h">{pp}%</span></div>')
    if opts:
        for o in opts:
            p=o.get('pct')
            if p is None: continue
            rows+=(f'<div class="pr"><span class="pl wide">{esc(o.get("name",""))}</span>'
                   f'<span class="pt"><i class="r" style="width:{p}%"></i></span>'
                   f'<span class="pv r">{p}%</span></div>')
    elif yes is not None:
        rows+=(f'<div class="pr"><span class="pl">Readers</span>'
               f'<span class="pt"><i class="r" style="width:{yes}%"></i></span>'
               f'<span class="pv r">{yes}%</span></div>')
    plot=f'<div class="plot">{rows}</div>' if rows else ''
    ech=f'<p class="mk-e">{esc(m.get("echo",""))}</p>' if m.get('echo') else ''
    qline = f'<div class="mk-q">{esc(m.get("question",""))}</div>' if show_q else ''
    acts=''
    if st=='live':
        pay={'q':m.get('question',''),
             'type':'multi' if opts else 'binary',
             'yes':yes if yes is not None else 50,
             'options':[{'name':o.get('name',''),'pct':o.get('pct',0)} for o in opts]}
        fc=H.escape(json.dumps(pay, ensure_ascii=False), quote=True)
        if opts:
            btns=''.join(f'<button class="btn o" data-fc="{fc}" data-pick="{esc(o.get("name",""))}">'
                         f'{esc(o.get("name",""))}</button>' for o in opts)
            acts=(f'<div class="ask">Your forecast</div><div class="btns col">{btns}</div>'
                  '<div class="mk-ack" role="status"></div>')
        else:
            acts=('<div class="ask">Your forecast</div>'
                  f'<div class="btns"><button class="btn y" data-fc="{fc}" data-side="yes">Yes</button>'
                  f'<button class="btn n" data-fc="{fc}" data-side="no">No</button></div>'
                  '<div class="mk-ack" role="status"></div>')
    out=''
    if st=='resolved' and m.get('outcome'):
        note=f'<p class="mk-on">{rich(m.get("outcome_note",""))}</p>' if m.get('outcome_note') else ''
        oc=str(m['outcome'])
        cls='pill' if oc.strip().upper()=='YES' else 'pill neu'
        out=(f'<div class="mk-out"><span class="{cls}">Resolved: {esc(oc)}</span>{note}</div>')
    date_lbl=('Resolved ' + esc(m.get('resolved',''))) if st=='resolved' and m.get('resolved') \
             else ('Resolves ' + esc(m.get('resolves','')) if m.get('resolves') else '')
    foot=(f'<div class="mk-f"><span>{int(m.get("volume",0)):,} points signed</span>'
          f'<span>{date_lbl}</span></div>')
    return (f'<div class="mk">{head}{qline}{ech}{plot}{acts}{out}{foot}'
            + (f'<div class="mk-v"><div class="mk-vh">How this resolves</div>'
               f'<p>{rich(verify)}</p></div>' if verify else '')
            + '</div>')

def page_markets(E):
    rows=[]
    for e in E:
        for m in (e.get('markets') or []):
            if m.get('status')=='live' and m.get('question'):
                pp,n,d=mk_pp(e,m); rows.append((e,m,pp,n,d))
    b=f'<div class="wrap"><div class="pg pg-wide pg-tight">'
    b+=f'<h1 class="pg-h">Open forecasts</h1></div>'
    b+=sec_head('Open', f'{len(rows)} live')
    b+='<div class="mkgrid">'
    for e,m,pp,n,d in rows[:60]:
        blk=market_block(m,pp,n,d)
        blk=blk.replace('<div class="mk-q">','<div class="mk-q"><a href="echo-'+e['slug']+'{D}">',1).replace('</div><div class="plot">','</a></div><div class="plot">',1)
        b+=blk
    b+='</div></div>'
    return b

def page_market_detail(E):
    for e in E:
        m=first_market(e)
        if m and m.get('status')=='live': break
    pp=pat_pct(e); n,d=pat_frac(e)
    b='<div class="wrap"><div class="pg">'
    b+=f'<div class="feat-top"><span class="kick acc">Market</span><span class="date">{fmt_date(e.get("date",""), True)}</span></div>'
    b+=f'<h1 class="art-h">{esc(m.get("question",""))}</h1>'
    b+=f'<div class="art-m"><span>{esc(m.get("type","binary")).title()}</span><span>Resolves {esc(m.get("resolves",""))}</span></div>'
    b+=market_block(m,pp,n,d,show_q=False)
    b+=art_sec('The pattern behind it')
    br=e.get('base_rate') or {}
    if br.get('text'):
        b+=f'<div class="base"><div class="base-n">{n} of {d}</div><div class="base-t">{rich(br["text"])}</div></div>'
    b+=f'<p>{rich((e.get("pattern") or {}).get("intro",""))}</p>'
    b+=f'<div class="acts"><a class="cta p" href="echo-{e["slug"]}{{D}}">Read the full Echo</a></div>'
    b+='</div></div>'
    return b

# сортування + пошук усередині сторінки (Pavlo 7 Sep); логіка в list.js
TOOLBAR=('<div class="tb" data-list="archive"><label class="tb-sel"><select aria-label="Sort">'
         '<option value="newest">Newest first</option><option value="oldest">Oldest first</option>'
         '<option value="az">Title A&ndash;Z</option><option value="topic">By topic</option></select></label>'
         '<button class="tb-s" type="button" aria-label="Search this page"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg></button>'
         '<form class="tb-q" role="search"><input type="search" placeholder="Search the archive" aria-label="Search this page" autocomplete="off"></form></div>')

def page_archive(E):
    b='<div class="wrap"><div class="pg pg-wide pg-tight pg-row">'
    b+='<h1 class="pg-h">Archive</h1>'+TOOLBAR+'</div>'
    cur=None; opened=False
    for e in E:
        mon=(e.get('date','') or '')[:7]
        if mon!=cur:
            cur=mon
            try: lbl=datetime.strptime(mon,'%Y-%m').strftime('%B %Y')
            except Exception: lbl=mon
            b+=('</div>' if opened else '')+sec_head(lbl)+'<div class="feed">'; opened=True
        b+=feed_item(e)
    b+=('</div>' if opened else '')+'</div>'
    return b

# перелінковка витягнутих статичних тіл на нові слаги
LINKMAP={'hunch-layout-v9-clean-20260824':'index','hunch-signup':'signup','hunch-echo-library':'echo-library'}
def clean_body(h):
    """таблиці у прокручувану обгортку; мертві href='#' перестають вдавати посилання;
       неактивні кнопки позначені. Текст не змінюється."""
    h = re.sub(r'<table', '<div class="twh"><div class="tw"><table', h)
    h = re.sub(r'</table>', '</table></div></div>', h)
    h = re.sub(r'<a href="#"([^>]*)>(.*?)</a>', r'<span class="inert"\2</span>'.replace('\2','>\2'), h)
    h = re.sub(r'<a href="#"[^>]*>', '<span class="inert">', h)
    h = h.replace('</a></span>', '</span>')
    h = re.sub(r'<button(?![^>]*disabled)', '<button data-inert="1" disabled aria-disabled="true"', h)
    return h

def relink(h, D):
    def f(m):
        name=m.group(1)
        base=name[:-5] if name.endswith('.html') else name
        base=base[:-5] if base.endswith('-dark') else base
        base=LINKMAP.get(base, base[6:] if base.startswith('hunch-') else base)
        return 'href="'+base+D+'"'
    return re.sub(r'href="([A-Za-z0-9_\-]+\.html)"', f, h)

def page_static(key, kicker_fallback=''):
    d=STATIC.get(key) or {}
    kick=d.get('kicker') or kicker_fallback
    b='<div class="wrap"><div class="pg'+(' pg-center' if key=='membership' else '')+'">'
    if kick: b+=f'<span class="kick acc">{esc(kick)}</span>'
    if d.get('title'): b+=f'<h1 class="pg-h">{esc(d["title"])}</h1>'
    if d.get('lead'): b+=f'<p class="pg-l">{esc(d["lead"])}</p>'
    fixed=staticfix.fix(d.get('body',''), d.get('title',''), d.get('lead',''), kick)
    b+=f'<div class="body">{clean_body(relink(fixed, "{D}"))}</div>'
    b+='</div></div>'
    return b


# ---------------------------------------------------------------- сторінки підвалу з v9 (Pavlo 7 Sep: картки, перемикачі, форми як на вебі)
DOC_SRC={'terms':'hunch-terms','privacy':'hunch-privacy','cookies':'hunch-cookies','licences':'hunch-licences',
         'responsible-play':'hunch-responsible-play','about':'hunch-about','methodology':'hunch-methodology',
         'careers':'hunch-careers','press':'hunch-press','partners':'hunch-partners','contact':'hunch-contact',
         'newsletter':'hunch-newsletter','api':'hunch-api','editorial-code':'hunch-editorial-code','echo-library':'hunch-echo-library'}
CMAP={'#1F241F':'var(--ink)','#216945':'var(--accent)','#4C463C':'var(--body)','#6B6455':'var(--meta)','#FFFDF7':'var(--surf)',
      '#D5CCB8':'var(--line-2)','#E4DCC8':'var(--line)','#7A5210':'var(--gold)','#FAF7EF':'var(--bg)','#194D2E':'var(--yes-b)',
      '#741F17':'var(--no-b)','#EFE8D8':'var(--accent-t)','#FFF':'var(--btn-i)','#FFFFFF':'var(--btn-i)'}
def _tok(h):
    h=re.sub(r'style="([^"]*)"',lambda m:'style="'+re.sub(r'#[0-9A-Fa-f]{3,8}\b',lambda x:CMAP.get(x.group(0).upper(),x.group(0)),m.group(1)).replace("'Source Serif 4',serif","var(--serif)")+'"',h)
    return h
def page_doc(src):
    s=open(os.path.join(os.path.dirname(OUT),src+'.html'),encoding='utf-8').read()
    end=s.find('<div class="footer-full">')
    if src=='hunch-editorial-code':
        a=s.find('<div class="doc-grid">'); e=s.find('</article>',a)+len('</article>'); blk=s[a:s.find('</div>',e)+6]
        inner='<div class="wrap">'+blk+'</div>'
    else:
        m=re.search(r'<div class="page-hdr"[^>]*>',s); a=m.start() if m else s.find('<div class="v10">')
        blk=s[a:end]
        inner='<div class="wrap"><div class="doc-page">'+blk+'</div></div>'
    inner=re.sub(r'<!--.*?-->','',inner,flags=re.S)
    inner=_tok(inner)
    if src=='hunch-api':
        # Pavlo 7 Sep: лишити Public і Commercial, під ними легка форма «Get a quote»
        inner=re.sub(r'\s*<div class="api-tier"><div class="name">Developer</div>.*?</div>\s*(?=<div class="api-tier">)','',inner,count=1,flags=re.S)
        inner=inner.replace(' Developer: 10,000 req / 24h with 100/min burst.','')
        quote=('<form class="quote" novalidate><h3>Get a quote</h3><div class="fr2">'
               '<div class="form-row"><label for="qn">Name</label><input id="qn" type="text" autocomplete="name"></div>'
               '<div class="form-row"><label for="qe">Work email</label><input id="qe" type="email" autocomplete="email"></div></div>'
               '<div class="form-row"><label for="qm">What you want to build</label><textarea id="qm" rows="3"></textarea></div>'
               '<button type="submit" class="btn-primary">Request a quote</button><p class="quote-note">We respond within two working days.</p></form>')
        i=inner.find('<div class="tier-grid">'); depth=0; end=None
        for mm in re.finditer(r'<div\b|</div>',inner[i:]):
            depth+=1 if mm.group(0)=='<div' else -1
            if depth==0: end=i+mm.end(); break
        if end: inner=inner[:end]+quote+inner[end:]
    def lk(m):
        h=m.group(1)
        if h.startswith(('http','mailto:','#')): return m.group(0)
        base=h[:-5] if h.endswith('.html') else h
        base=LINKMAP.get(base, base[6:] if base.startswith('hunch-') else base)
        return 'href="'+base+'{D}"'
    inner=re.sub(r'href="([^"]+)"',lk,inner)
    return inner


# ---------------------------------------------------------------- шер-модал (Pavlo 3 Aug / 7 Sep): превʼю банера + лінк + мережі + зберегти картинку
NET_ICONS={
 'x':'<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M18.9 1.2h3.7l-8.1 9.3L24 22.8h-7.5l-5.9-7.7-6.7 7.7H.2l8.7-9.9L0 1.2h7.7l5.3 7 6-7zm-1.3 19.4h2.1L6.6 3.3H4.4l13.2 17.3z"/></svg>',
 'linkedin':'<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M20.4 20.4h-3.6v-5.6c0-1.3 0-3-1.9-3s-2.1 1.4-2.1 2.9v5.7H9.2V9h3.4v1.6h.1c.5-.9 1.7-1.9 3.4-1.9 3.6 0 4.3 2.4 4.3 5.5v6.2zM5.2 7.4a2.1 2.1 0 1 1 0-4.2 2.1 2.1 0 0 1 0 4.2zM7 20.4H3.4V9H7v11.4zM22.2 0H1.8C.8 0 0 .8 0 1.7v20.6c0 .9.8 1.7 1.8 1.7h20.4c1 0 1.8-.8 1.8-1.7V1.7c0-.9-.8-1.7-1.8-1.7z"/></svg>',
 'whatsapp':'<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M17.5 14.4c-.3-.1-1.8-.9-2-1-.3-.1-.5-.1-.7.1-.2.3-.8 1-.9 1.2-.2.2-.3.2-.6.1-.3-.2-1.3-.5-2.4-1.5-.9-.8-1.5-1.8-1.7-2.1-.2-.3 0-.5.1-.6l.5-.6c.2-.2.2-.3.3-.5.1-.2 0-.4 0-.5l-.9-2.2c-.2-.6-.5-.5-.7-.5h-.6c-.2 0-.5.1-.8.4-.3.3-1 1-1 2.5s1.1 2.9 1.2 3.1c.2.2 2.1 3.2 5.1 4.5.7.3 1.3.5 1.7.6.7.2 1.4.2 1.9.1.6-.1 1.8-.7 2-1.4.2-.7.2-1.3.2-1.4-.1-.2-.3-.2-.7-.3zM12 21.8h0c-1.8 0-3.5-.5-5-1.4l-.4-.2-3.7 1 1-3.6-.2-.4a9.8 9.8 0 1 1 8.3 4.6zM12 0a12 12 0 0 0-10.4 18L0 24l6.2-1.6A12 12 0 1 0 12 0z"/></svg>',
 'telegram':'<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0a12 12 0 1 0 0 24 12 12 0 0 0 0-24zm5.9 8.2-2 9.3c-.1.7-.5.8-1.1.5l-3-2.2-1.4 1.4c-.2.2-.3.3-.6.3l.2-3 5.4-4.9c.2-.2 0-.3-.3-.1l-6.7 4.2-2.9-.9c-.6-.2-.6-.6.1-.9l11.4-4.4c.5-.2 1 .1.9.7z"/></svg>',
 'email':'<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></svg>',
}
def share_modal(e):
    nets=''.join(f'<a class="sm-net" data-net="{k}" title="{k.title()}" aria-label="Share on {k.title()}">{v}</a>' for k,v in NET_ICONS.items())
    return ('<div class="share-backdrop" id="shareBackdrop"></div>'
            '<div class="share-modal" id="shareModal" role="dialog" aria-label="Share this Echo">'
            '<div class="sm-hdr"><span class="sm-title">Share this Echo</span><button class="sm-close" id="shareClose" aria-label="Close">&times;</button></div>'
            f'<a class="sm-preview" id="shareImg" href="share/{e["slug"]}.png" download="hunch-{e["slug"]}.png"><img src="share/{e["slug"]}.png" alt=""></a>'
            '<div class="sm-linkrow"><input class="sm-link" id="shareLink" type="text" readonly value=""><button class="sm-copy" id="shareCopy" type="button">Copy</button></div>'
            f'<div class="sm-nets" id="shareNets">{nets}<a class="sm-net sm-save" href="share/{e["slug"]}.png" download="hunch-{e["slug"]}.png" title="Save image">Save image</a></div></div>')

SHARE_JS=("<script>(function(){var s=document.getElementById('ecShare'),sb=document.getElementById('shareBackdrop'),sm=document.getElementById('shareModal'),"
 "sl=document.getElementById('shareLink'),sc=document.getElementById('shareCopy'),sx=document.getElementById('shareClose');if(!s||!sm)return;"
 "function u(){return location.href}"
 "function copy(){var v=u();var done=function(){sc.textContent='Copied';sc.classList.add('done');setTimeout(function(){sc.textContent='Copy';sc.classList.remove('done')},1600)};"
 "if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(v).then(done,fb)}else fb();function fb(){sl.focus();sl.select();try{document.execCommand('copy');done()}catch(e){}}}"
 "function open(){sl.value=u();var t=encodeURIComponent(document.title.replace(/ \\u2014 Hunch$/,'')),x=encodeURIComponent(u());"
 "var nets={x:'https://twitter.com/intent/tweet?text='+t+'&url='+x,linkedin:'https://www.linkedin.com/sharing/share-offsite/?url='+x,whatsapp:'https://wa.me/?text='+t+'%20'+x,telegram:'https://t.me/share/url?url='+x+'&text='+t,email:'mailto:?subject='+t+'&body='+x};"
 "sm.querySelectorAll('.sm-net[data-net]').forEach(function(a){a.href=nets[a.getAttribute('data-net')];if(a.getAttribute('data-net')!=='email'){a.target='_blank';a.rel='noopener'}});"
 "sb.classList.add('open');sm.classList.add('open')}"
 "function close(){sb.classList.remove('open');sm.classList.remove('open')}"
 "s.addEventListener('click',function(e){e.preventDefault();open()});sx.addEventListener('click',close);sb.addEventListener('click',close);sc.addEventListener('click',copy);"
 "document.addEventListener('keydown',function(e){if(e.key==='Escape')close()});"
 "if(location.hash==='#share')open();})();</script>")

# ---------------------------------------------------------------- вхід / реєстрація
G_ICON=('<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>'
        '<path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>'
        '<path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>'
        '<path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>')
A_ICON=('<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/></svg>')
L_ICON=('<svg viewBox="0 0 24 24" fill="#0A66C2" aria-hidden="true"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.063 2.063 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452z"/></svg>')

AUTH_JS = ('<script>(function(){var au=document.getElementById("au");if(!au)return;'
  'function mode(m){au.classList.toggle("signup",m==="signup");'
  'au.querySelectorAll(".au-tab").forEach(function(t){t.classList.toggle("on",t.dataset.mode===m)});'
  'var n=au.querySelector(".au-ack");if(n)n.textContent="";}'
  'au.querySelectorAll("[data-mode]").forEach(function(b){b.onclick=function(e){e.preventDefault();mode(b.dataset.mode)}});'
  'var f=au.querySelector("form");if(f)f.onsubmit=function(e){e.preventDefault();'
  'var n=au.querySelector(".au-ack");if(n)n.textContent="Accounts open soon — with the public beta."};'
  'au.querySelectorAll(".au-soc a,.au-soc button,.au-lnk").forEach(function(a){a.onclick=function(e){e.preventDefault();'
  'var n=au.querySelector(".au-ack");if(n)n.textContent="Accounts open soon — with the public beta.";'
  'n.scrollIntoView({behavior:"smooth",block:"center"})}});'
  '})();</script>')

def page_signin(E):
    """Вхід і реєстрація на одному екрані. Текст — дослівно з веб-версії signin.html.
       Вкладки перемикають режим; форма і соцкнопки відповідають повідомленням про бету."""
    b='<div class="wrap"><div class="pg au" id="au">'
    b+=('<div class="au-tabs" role="tablist">'
        '<button class="au-tab on" type="button" role="tab" data-mode="login">Log in</button>'
        '<button class="au-tab" type="button" role="tab" data-mode="signup">Sign up</button></div>')
    b+='<h1 class="pg-h"><span class="li">Welcome back.</span><span class="su">Back your hunch.</span></h1>'
    b+='<p class="pg-l li">When accounts open, you will track your accuracy and make your calls here.</p>'
    b+='<p class="pg-l su">Free to start. No crypto. No jargon. Just intuition with a track record.</p>'
    b+=('<div class="au-soc">'
        f'<button type="button" class="soc-b">{G_ICON}Continue with Google</button>'
        f'<button type="button" class="soc-b">{A_ICON}Continue with Apple</button>'
        f'<button type="button" class="soc-b">{L_ICON}Continue with LinkedIn</button></div>')
    b+='<div class="au-or"><span>or with email</span></div>'
    b+=('<form class="au-form" novalidate>'
        '<div class="au-f su"><label for="au-name">Display name</label>'
        '<input id="au-name" type="text" placeholder="e.g. WestminsterOwl" autocomplete="username"></div>'
        '<div class="au-f"><label for="au-mail">Email</label>'
        '<input id="au-mail" type="email" placeholder="you@example.com" autocomplete="email" inputmode="email"></div>'
        '<div class="au-f"><label for="au-pass">Password</label>'
        '<input id="au-pass" type="password" placeholder="&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;" autocomplete="current-password"></div>'
        '<div class="au-row li"><label><input type="checkbox"> Remember me</label>'
        '<button type="button" class="au-lnk">Forgot password?</button></div>'
        '<div class="au-row su"><label><input type="checkbox"> <span>I accept the '
        '<a href="terms{D}">Terms</a> &amp; <a href="privacy{D}">Privacy Policy</a></span></label></div>'
        '<button class="au-cta" type="submit"><span class="li">Log in</span><span class="su">Create account</span></button>'
        '<p class="au-ack" aria-live="polite"></p>'
        '</form>')
    b+='<p class="au-sw li">Don\'t have an account? <button type="button" data-mode="signup">Sign up</button></p>'
    b+='<p class="au-sw su">Already have an account? <button type="button" data-mode="login">Log in</button></p>'
    b+='<p class="au-legal">Hunch Points carry no monetary value and cannot be exchanged for money or prizes.</p>'
    b+='</div></div>'
    return b + AUTH_JS

# ---------------------------------------------------------------- main
def main():
    E=load_echoes()
    # Featured на головній (Pavlo 7 Sep: «онови, бо ще з серпня»). FEATURED_SLUG прибиває вручну;
    # інакше правило: найсвіжіша дата → політика перша → найближчий live-резолв, що ще не минув.
    if FEATURED_SLUG:
        f=next((x for x in E if x['slug']==FEATURED_SLUG), None)
    else:
        from datetime import datetime as _dt
        def _res(x):
            best=None
            for m in x.get('markets') or []:
                if m.get('status')!='live': continue
                try: d=_dt.strptime(m.get('resolves',''),'%d %b %Y')
                except Exception: continue
                if d>=_dt.now().replace(hour=0,minute=0,second=0,microsecond=0) and (best is None or d<best): best=d
            return best
        cands=[x for x in E if _res(x)]
        top=max(x.get('date','') for x in cands) if cands else ''
        cands=[x for x in cands if x.get('date','')==top]
        cands.sort(key=lambda x:(0 if x.get('category')=='politics' else 1, _res(x)))
        f=cands[0] if cands else None
    if f: E=[f]+[x for x in E if x is not f]
    print('Featured:', f['slug'] if f else '—')
    print(f'Echo у контенті: {len(E)}')

    PAGES=[]
    PAGES.append(('index','Today',       lambda: page_home(E), ''))
    for slug,name in CATS:
        PAGES.append((slug,name, (lambda s=slug,n=name: page_cat(E,s,n)), slug))
    for ec in E:
        PAGES.append((f'echo-{ec["slug"]}', ec['headline'][:60],
                      (lambda x=ec: page_echo(x)), ec.get('category','')))
    PAGES.append(('markets','Markets',   lambda: page_markets(E), ''))
    PAGES.append(('market-detail','Market', lambda: page_market_detail(E), ''))
    PAGES.append(('archive','Archive',   lambda: page_archive(E), ''))
    PAGES.append(('signin','Sign in',    lambda: page_signin(E), ''))

    STATIC_MAP=[
      ('leaderboard','hunch-leaderboard','Leaderboard'),('echo-library','hunch-echo-library','Echo'),
      ('patterns','hunch-patterns','Patterns'),('methodology','hunch-methodology','Method'),
      ('sources','hunch-sources','Sources'),
      ('membership','membership','Membership'),
      ('signup','hunch-signup','Account'),('account','hunch-account','Account'),
      ('mobile-app','hunch-mobile-app','Apps'),
      ('about','hunch-about','About'),('team','hunch-team','Team'),
      ('partners','hunch-partners','Partners'),('press','hunch-press','Press'),
      ('careers','hunch-careers','Careers'),('contact','hunch-contact','Contact'),
      ('newsletter','hunch-newsletter','Newsletter'),
      ('help','hunch-help','Help'),('status','hunch-status','Status'),
      ('api','hunch-api','Developers'),('sitemap','hunch-sitemap','Sitemap'),
      ('accessibility','hunch-accessibility','Accessibility'),
      ('terms','hunch-terms','Legal'),('privacy','hunch-privacy','Legal'),
      ('cookies','hunch-cookies','Legal'),('acceptable-use','hunch-acceptable-use','Legal'),
      ('licences','hunch-licences','Legal'),('policy','hunch-policy','Legal'),
      ('editorial-code','hunch-editorial-code','Legal'),
      ('responsible-play','hunch-responsible-play','Legal'),
    ]
    for out_slug, src, kick in STATIC_MAP:
        d=STATIC.get(src) or {}
        if out_slug=='account':
            PAGES.append((out_slug,'Your account',(lambda: '<div class="wrap"><div class="pg"><p class="pg-l">Accounts open with the public beta. Taking you to sign in&hellip;</p><p><a href="signin{D}">Sign in</a></p></div></div>'),''))
            continue
        if out_slug in DOC_SRC:
            PAGES.append((out_slug, d.get('title') or out_slug, (lambda s=DOC_SRC[out_slug]: page_doc(s)), ''))
            continue
        PAGES.append((out_slug, d.get('title') or out_slug,
                      (lambda s=src,k=kick: page_static(s,k)), ''))

    for ec in E: ECHO_CAT[ec['slug']]=ec.get('category','echo')
    for ec in E:
        META['echo-'+ec['slug']]={'desc':(ec.get('lead') or ec.get('brief') or '')[:300],'og':'assets/share/'+ec['slug']+'.png'}
    META['index']={'desc':'Today on Hunch: the news, the historical pattern behind it, and the call readers are making.','og':'assets/share/'+E[0]['slug']+'.png'}
    for s_,n_ in CATS: META[s_]={'desc':f'{n_} on Hunch: every story with the historical pattern behind it and a market that resolves on a date.'}
    n=0; nw=0
    for slug,title,fn,active in PAGES:
        body=fn()
        for dark in (False,True):
            D='-dark.html' if dark else '.html'
            html=shell(title, body, active, dark, slug)
            open(os.path.join(OUT, slug+D),'w',encoding='utf-8').write(html); n+=1
            if WEB:
                html=shell(title, body, active, dark, slug, web=True)
                p=os.path.join(OUT_WEB, web_path(slug,dark)); os.makedirs(os.path.dirname(p),exist_ok=True)
                open(p,'w',encoding='utf-8').write(html); nw+=1
    if WEB:
        import shutil
        os.makedirs(os.path.join(OUT_WEB,'assets'),exist_ok=True)
        for f in ('m.css','doc.css','list.js','hunch-search.js'):
            shutil.copy(os.path.join(OUT,f), os.path.join(OUT_WEB,'assets',f))
        # банери для шер-модалу: designs/social-banners/hunch-social-<slug>-B-og.png → share/<slug>.png (обидва дерева)
        src=os.path.join(os.path.dirname(OUT),'social-banners'); os.makedirs(os.path.join(OUT,'share'),exist_ok=True); os.makedirs(os.path.join(OUT_WEB,'assets','share'),exist_ok=True); nb=0
        for ec in E:
            p=os.path.join(src,f'hunch-social-{ec["slug"]}-B-og.png')
            if os.path.exists(p):
                shutil.copy(p,os.path.join(OUT,'share',ec['slug']+'.png')); shutil.copy(p,os.path.join(OUT_WEB,'assets','share',ec['slug']+'.png')); nb+=1
        print('share banners copied:',nb)
        # sitemap + robots + фавікони
        urls=[]
        for slug,title,fn,active in PAGES:
            p=web_path(slug,False).replace('index.html',''); urls.append(SITE+'/'+p)
        sm='<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(f'<url><loc>{u}</loc></url>' for u in urls)+'</urlset>'
        open(os.path.join(OUT_WEB,'sitemap.xml'),'w',encoding='utf-8').write(sm)
        open(os.path.join(OUT_WEB,'robots.txt'),'w',encoding='utf-8').write(('User-agent: *\nAllow: /\n' if PUBLIC else 'User-agent: *\nDisallow: /\n')+f'Sitemap: {SITE}/sitemap.xml\n')
        for f in ('favicon.ico','favicon.svg','apple-touch-icon.png','og-default.png'):
            p=os.path.join(OUT,f)
            if os.path.exists(p): shutil.copy(p, os.path.join(OUT_WEB,'assets',f))
        print('sitemap:',len(urls),'urls | robots:', 'Allow' if PUBLIC else 'Disallow')
    print(f'сторінок записано: {n}  ({len(PAGES)} унікальних × 2 теми)' + (f'; веб: {nw} у {OUT_WEB}' if WEB else ''))
    return [p[0] for p in PAGES]

WEB = os.environ.get('HUNCH_WEB','1')=='1'   # HUNCH_WEB=0 → лише мобільна плоска збірка

if __name__=='__main__':
    main()

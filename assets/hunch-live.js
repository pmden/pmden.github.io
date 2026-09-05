/* Hunch live layer — dark. Bet modal (canon: hunch-bet-modal-dark), votes, filters, sort, waitlist.
   Phase 1: Hunch Points, localStorage persistence. Deploy: set WAITLIST_ENDPOINT to POST emails. */
(function () {
  'use strict';
  var WAITLIST_ENDPOINT = ''; // e.g. https://byhunch.com/api/waitlist — wired at deploy
  var COMMISSION = 0.05;
  var LS = {
    get: function (k, d) { try { return JSON.parse(localStorage.getItem(k)) || d; } catch (e) { return d; } },
    set: function (k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
  };
  function balance() {
    var calls = LS.get('hunch_calls', []);
    var spent = calls.reduce(function (s, c) { return s + (c.stake || 0); }, 0);
    return Math.max(0, 2500 - spent);
  }
  var fmt = function (n) { return Math.round(n).toLocaleString('en-GB'); };

  /* ---------- modal shell ---------- */
  var backdrop = document.createElement('div');
  var modal = document.createElement('div');
  backdrop.className = 'hb-backdrop'; modal.className = 'hb-modal'; modal.setAttribute('role', 'dialog');
  var css = document.createElement('style');
  css.textContent = "\
.hb-backdrop{position:fixed;inset:0;background:rgba(5,7,8,.74);-webkit-backdrop-filter:blur(2px);backdrop-filter:blur(2px);opacity:0;pointer-events:none;transition:opacity .18s;z-index:40;}\
.hb-backdrop.open{opacity:1;pointer-events:auto;}\
.hb-modal{position:fixed;z-index:50;top:50%;left:50%;transform:translate(-50%,-46%);width:min(400px,calc(100vw - 40px));background:#FFFDF7;border:1px solid #E4DCC8;border-radius:14px;padding:22px;box-shadow:0 24px 60px rgba(0,0,0,.6);opacity:0;pointer-events:none;transition:opacity .18s,transform .18s;font-family:'Inter',system-ui,sans-serif;color:#1F241F;}\
.hb-modal.open{opacity:1;pointer-events:auto;transform:translate(-50%,-50%);}\
@media(max-width:560px){.hb-modal{top:auto;bottom:0;left:0;transform:translateY(102%);width:100%;border-radius:18px 18px 0 0;border-bottom:none;padding:16px 20px 26px;}.hb-modal.open{transform:translateY(0);}.hb-grip{display:block;}}\
.hb-grip{display:none;width:38px;height:4px;border-radius:3px;background:#D8D2C2;margin:0 auto 14px;}\
.hb-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;}\
.hb-side{display:flex;align-items:center;gap:9px;font-family:'Source Serif 4',serif;font-size:17px;font-weight:600;}\
.hb-pill{font-family:'Inter',sans-serif;font-size:11px;letter-spacing:.06em;text-transform:uppercase;padding:3px 9px;border-radius:20px;font-weight:600;}\
.hb-pill.yes{background:#D9EAE0;color:#1F241F;border:1px solid #B9D6C4;}\
.hb-pill.no{background:#F3DBD7;color:#741F17;border:1px solid #D9A79F;}\
.hb-pill.opt{background:#F5EFE1;color:#7A5107;border:1px solid #D9C391;}\
.hb-close{background:none;border:none;color:#6B6455;font-size:24px;line-height:1;cursor:pointer;padding:0 2px;}\
.hb-close:hover{color:#1F241F;}\
.hb-q{font-size:15.5px;color:#6B6455;line-height:1.45;margin:0 0 16px;}\
.hb-tabs{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:16px;}\
.hb-tab{font-family:inherit;font-size:13px;padding:11px;border-radius:9px;background:#F5EFE1;border:1px solid #E4DCC8;color:#4C463C;cursor:pointer;display:flex;justify-content:center;gap:7px;transition:.12s;}\
.hb-tab b{color:#1F241F;}\
.hb-tab.on.yes{background:#216945;border-color:#1B5A39;color:#FAF7EF;}.hb-tab.on.yes b{color:#FAF7EF;}\
.hb-tab.on.no{background:#8F2B21;border-color:#741F17;color:#FAF7EF;}.hb-tab.on.no b{color:#FAF7EF;}\
.hb-opts{display:flex;flex-direction:column;gap:8px;margin-bottom:16px;max-height:180px;overflow-y:auto;}\
.hb-opt{font-family:inherit;display:flex;justify-content:space-between;gap:8px;font-size:13px;padding:11px 13px;border-radius:9px;background:#F5EFE1;border:1px solid #E4DCC8;color:#4C463C;cursor:pointer;text-align:left;}\
.hb-opt.on{border-color:#7A5210;color:#1F241F;box-shadow:0 0 0 1px #7A5210 inset;}\
.hb-opt b{color:#1F241F;}\
.hb-lbl{display:flex;justify-content:space-between;align-items:baseline;font-size:12px;color:#6B6455;margin-bottom:7px;}\
.hb-lbl .bal{color:#4C463C;}\
.hb-amt{display:flex;align-items:center;background:#FAF7EF;border:1px solid #E4DCC8;border-radius:10px;padding:0 14px;margin-bottom:10px;}\
.hb-amt input{flex:1;background:none;border:none;outline:none;color:#1F241F;font-family:'Source Serif 4',serif;font-size:26px;font-weight:600;padding:13px 0;width:100%;}\
.hb-amt .unit{font-size:12px;color:#6B6455;letter-spacing:.05em;}\
.hb-chips{display:flex;gap:7px;margin-bottom:16px;}\
.hb-chips button{flex:1;font-family:inherit;font-size:12px;color:#4C463C;background:#F5EFE1;border:1px solid #E4DCC8;border-radius:8px;padding:8px 0;cursor:pointer;transition:.12s;}\
.hb-chips button:hover{border-color:#216945;color:#1F241F;}\
.hb-calc{background:#FAF7EF;border:1px solid #E4DCC8;border-radius:10px;padding:13px 15px;margin-bottom:16px;}\
.hb-row{display:flex;justify-content:space-between;align-items:center;font-size:13px;margin-bottom:8px;}\
.hb-row:last-child{margin-bottom:0;}\
.hb-row .k{color:#6B6455;}.hb-row .v{color:#4C463C;font-weight:500;}\
.hb-row.win .k{color:#4C463C;}.hb-row.win .v{color:#216945;font-family:'Source Serif 4',serif;font-size:18px;font-weight:600;}\
.hb-cta{width:100%;font-family:inherit;font-size:15px;font-weight:600;color:#1F241F;border:none;border-radius:10px;padding:15px;cursor:pointer;transition:filter .12s;}\
.hb-cta:hover{filter:brightness(1.08);}\
.hb-cta.yes{background:#216945;color:#FAF7EF;}\
.hb-cta.no{background:#8F2B21;color:#FBEFED;}\
.hb-cta.opt{background:#7A5210;color:#F3E9CF;}\
.hb-fine{font-size:11px;color:#6B6455;line-height:1.6;margin:12px 0 0;text-align:center;}";
  document.head.appendChild(css);
  document.addEventListener('DOMContentLoaded', function () {
    document.body.appendChild(backdrop); document.body.appendChild(modal);
  });

  var state = null; // {bet, side, pick, amount}
  function pctFor() {
    var b = state.bet;
    if (b.type === 'binary') return state.side === 'yes' ? b.yes : 100 - b.yes;
    var o = (b.options || []).filter(function (x) { return x.name === state.pick; })[0];
    return o ? o.pct : 50;
  }
  function calc() {
    var price = Math.max(1, pctFor()) / 100;
    var shares = state.amount / price;
    var win = Math.max(0, (shares - state.amount) * (1 - COMMISSION));
    return { price: price, win: win };
  }
  function slipHTML() {
    var b = state.bet, c = calc(), pct = pctFor();
    var pill, tabs = '';
    if (b.type === 'binary') {
      pill = '<span class="hb-pill ' + state.side + '">' + (state.side === 'yes' ? 'Yes ' + b.yes + '%' : 'No ' + (100 - b.yes) + '%') + '</span>';
      tabs = '<div class="hb-tabs">' +
        '<button class="hb-tab yes ' + (state.side === 'yes' ? 'on' : '') + '" data-tab="yes">Yes <b>' + b.yes + '%</b></button>' +
        '<button class="hb-tab no ' + (state.side === 'no' ? 'on' : '') + '" data-tab="no">No <b>' + (100 - b.yes) + '%</b></button></div>';
    } else {
      pill = '<span class="hb-pill opt">' + pct + '%</span>';
      tabs = '<div class="hb-opts">' + (b.options || []).map(function (o) {
        return '<button class="hb-opt ' + (o.name === state.pick ? 'on' : '') + '" data-pick="' + o.name.replace(/"/g, '&quot;') + '"><span>' + o.name + '</span><b>' + o.pct + '%</b></button>';
      }).join('') + '</div>';
    }
    var ctaCls = b.type === 'binary' ? state.side : 'opt';
    var ctaLabel = b.type === 'binary' ? ('Buy ' + (state.side === 'yes' ? 'Yes' : 'No')) : 'Back this outcome';
    return '<div class="hb-grip"></div>' +
      '<div class="hb-head"><div class="hb-side">Your call ' + pill + '</div><button class="hb-close" data-close aria-label="Close">&times;</button></div>' +
      '<div class="hb-q">' + b.q + '</div>' + tabs +
      '<div class="hb-lbl"><span>Your call</span><span class="bal">Balance ' + fmt(balance()) + ' HP</span></div>' +
      '<div class="hb-amt"><input type="text" inputmode="numeric" id="hbAmt" value="' + state.amount + '"><span class="unit">HP</span></div>' +
      '<div class="hb-chips"><button data-add="10">+10</button><button data-add="50">+50</button><button data-add="100">+100</button><button data-max>Max</button></div>' +
      '<div class="hb-calc"><div class="hb-row"><span class="k">Avg price</span><span class="v">' + Math.round(c.price * 100) + ' HP / share</span></div>' +
      '<div class="hb-row win"><span class="k">If you’re right</span><span class="v">+' + fmt(c.win) + ' HP</span></div></div>' +
      '<button class="hb-cta ' + ctaCls + '" data-confirm>' + ctaLabel + ' · ' + fmt(state.amount) + ' HP</button>' +
      '<p class="hb-fine">Parimutuel pool.</p>';
  }
  function render() {
    modal.innerHTML = slipHTML();
    modal.querySelectorAll('[data-tab]').forEach(function (b) { b.onclick = function () { state.side = b.dataset.tab; render(); }; });
    modal.querySelectorAll('[data-pick]').forEach(function (b) { b.onclick = function () { state.pick = b.dataset.pick; render(); }; });
    var amt = modal.querySelector('#hbAmt');
    if (amt) amt.oninput = function () { state.amount = Math.max(0, parseInt(amt.value.replace(/\D/g, ''), 10) || 0); refresh(); };
    modal.querySelectorAll('[data-add]').forEach(function (b) { b.onclick = function () { state.amount += +b.dataset.add; render(); }; });
    var mx = modal.querySelector('[data-max]');
    if (mx) mx.onclick = function () { state.amount = balance(); render(); };
    var cl = modal.querySelector('[data-close]');
    if (cl) cl.onclick = close;
    var cf = modal.querySelector('[data-confirm]');
    if (cf) cf.onclick = function () {
      if (state.amount <= 0 || state.amount > balance()) { cf.textContent = state.amount <= 0 ? 'Enter an amount' : 'Not enough HP'; return; }
      var calls = LS.get('hunch_calls', []);
      calls.push({ slug: state.bet.slug, mi: state.bet.mi, side: state.side, pick: state.pick, stake: state.amount, ts: Date.now() });
      LS.set('hunch_calls', calls);
      cf.textContent = 'Call placed ✓';
      cf.style.filter = 'brightness(.9)';
      setTimeout(close, 900);
    };
  }
  function refresh() {
    var c = calc();
    var w = modal.querySelector('.hb-row.win .v'); if (w) w.textContent = '+' + fmt(c.win) + ' HP';
    var cf = modal.querySelector('[data-confirm]');
    if (cf) cf.textContent = (state.bet.type === 'binary' ? 'Buy ' + (state.side === 'yes' ? 'Yes' : 'No') : 'Back this outcome') + ' · ' + fmt(state.amount) + ' HP';
  }
  function open(bet, side, pick) {
    state = { bet: bet, side: side || 'yes', pick: pick || (bet.options && bet.options[0] && bet.options[0].name), amount: 100 };
    render();
    backdrop.classList.add('open'); modal.classList.add('open');
  }
  function close() { backdrop.classList.remove('open'); modal.classList.remove('open'); }
  backdrop.addEventListener('click', close);
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });

  document.addEventListener('click', function (e) {
    var b = e.target.closest('.fcbtn');
    // Розмітку кнопкам ставить інший блок і кладе payload у data-forecast,
    // а тут читалось data-bet, тому віджет не відкривався ЖОДНОГО разу.
    // Приймаємо обидва імені (Pavlo, 4 Sep).
    var raw = b && (b.dataset.bet || b.dataset.forecast);
    if (!b || !raw) return;
    e.preventDefault();
    try {
      var bet = JSON.parse(raw);
      open(bet, bet.side, bet.pick);
    } catch (err) {}
  });

  /* ---------- category filters + sort ---------- */
  document.addEventListener('click', function (e) {
    var f = e.target.closest('[data-filter]');
    if (!f) return;
    e.preventDefault();
    var subs = f.closest('.subs'); if (!subs) return;
    subs.querySelectorAll('a').forEach(function (a) { a.classList.remove('on'); });
    f.classList.add('on');
    var tag = f.dataset.filter;
    document.querySelectorAll('.echo-card').forEach(function (c) {
      c.style.display = (tag === 'all' || c.dataset.tag === tag) ? '' : 'none';
    });
  });
  document.addEventListener('click', function (e) {
    var s = e.target.closest('[data-sort]');
    if (!s) return;
    var grid = document.querySelector('.echo-grid'); if (!grid) return;
    var cards = Array.prototype.slice.call(grid.querySelectorAll('.echo-card'));
    var key = s.dataset.sort;
    if (key === 'resolving') cards.sort(function (a, b) { return (+a.dataset.days || 999) - (+b.dataset.days || 999); });
    else if (key === 'opinions') cards.sort(function (a, b) { return (+b.dataset.opinions || 0) - (+a.dataset.opinions || 0); });
    else return; // editor's pick = original order; skip reflow
    cards.forEach(function (c) { grid.appendChild(c); });
  });

  /* ---------- markets page category tabs ---------- */
  document.addEventListener('click', function (e) {
    var t = e.target.closest('.filter-tab');
    if (!t) return;
    document.querySelectorAll('.filter-tab').forEach(function (x) { x.classList.remove('active'); });
    t.classList.add('active');
    var cat = t.dataset.cat;
    document.querySelectorAll('.market-card').forEach(function (c) {
      var cats = (c.dataset.cat || '').split(' ');
      c.style.display = (cat === 'all' || cats.indexOf(cat) >= 0) ? '' : 'none';
    });
  });

  /* ---------- waitlist ---------- */
  function wireWaitlist(form) {
    form.setAttribute('novalidate', ''); // waitlist path: JS validates the email; hidden required fields must not block a real click
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var input = form.querySelector('input[type="email"]') || form.querySelector('input[type="text"]');
      if (!input) return;
      var email = (input.value || '').trim();
      if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) { input.style.borderColor = '#8F2B21'; return; }
      var list = LS.get('hunch_waitlist', []);
      if (list.indexOf(email) === -1) list.push(email);
      LS.set('hunch_waitlist', list);
      if (WAITLIST_ENDPOINT) {
        try { fetch(WAITLIST_ENDPOINT, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email: email }) }); } catch (err) {}
      }
      var ok = document.createElement('p');
      ok.textContent = "You're on the list. First Echoes land before the 18 August beta.";
      ok.style.cssText = 'color:#216945;font-size:14px;margin-top:10px;font-weight:500;';
      form.parentNode.insertBefore(ok, form.nextSibling);
      form.style.display = 'none';
    });
  }
  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('form').forEach(function (f) {
      if (f.querySelector('input[type="email"]') || /news|signup|wait/i.test(f.className + ' ' + (f.id || ''))) wireWaitlist(f);
    });
  });
})();

// menu wiring (injected by build: burger works on every page)
(function(){
  var p=document.getElementById('menuPanel'), b=document.getElementById('menuBackdrop');
  if(!p||!b) return;
  function open(){p.classList.add('open');b.classList.add('open');}
  function close(){p.classList.remove('open');b.classList.remove('open');}
  document.addEventListener('click',function(e){
    if(e.target.closest('[data-menu-open]')){e.preventDefault();open();}
    else if(e.target.closest('[data-menu-close]')||e.target===b){e.preventDefault();close();}
  });
  document.addEventListener('keydown',function(e){if(e.key==='Escape')close();});
})();
// markets live (28 Aug 2026): every prediction control carries a bet payload and
// a selected state. A server-rendered data-forecast always wins; controls without one
// synthesise theirs from the DOM, so the whole prototype is clickable.
(function(){
  var SEL='.opt.yes,.opt.no,.mopt,.mc-vote,.p-yes,.p-no,.my,.mn,.md-vote-opt';
  var QSEL='.mq,.mc-title,.mr-q,.md-title,.mkt-q,.ec-title,.pat-h,h1,h2,h3';
  var GRP='.bins,.multi,.mc-poll-binary,.ec-poll,.mr-poll,.poll,.mkt-poll,.md-vote-options';
  function t(n){return n?(n.textContent||'').replace(/\s+/g,' ').trim():'';}
  function pct(el){var p=el.querySelector('.op,.mc-vote-pct,.md-vote-pct');var v=parseInt(t(p),10);return isNaN(v)?null:v;}
  function slug(){var f=(location.pathname.split('/').pop()||'').replace(/\.html$/,'');return f.replace(/^hunch-echo-/,'').replace(/-dark$/,'')||'market';}
  function question(g){
    var n=g,h=0;
    while(n&&n.nodeType===1&&h++<7){
      var q=n.querySelector?n.querySelector(QSEL):null;
      if(q&&t(q))return t(q);
      n=n.parentNode;
    }
    return 'Market';
  }
  function isYes(el){return /(^|\s)(yes|p-yes|my|mc-vote-yes)(\s|$)/.test(el.className||'');}
  function yesPct(g){
    var y=g.querySelector('.opt.yes,.mc-vote-yes,.p-yes,.my');
    var v=y?pct(y):null;
    if(v!=null)return v;
    var n=g.parentNode,h=0;
    while(n&&n.nodeType===1&&h++<3){
      var p=n.querySelector?n.querySelector('.pct'):null;
      var k=p?parseInt(t(p),10):NaN;
      if(!isNaN(k))return k;
      n=n.parentNode;
    }
    return 50;
  }
  function stamp(el,mi){
    if(el.getAttribute('data-forecast'))return;
    var g=el.closest(GRP)||el.parentNode; if(!g)return;
    var multi=/(^|\s)(mopt|md-vote-opt)(\s|$)/.test(el.className||'');
    var p;
    if(multi){
      var list=[].slice.call(g.querySelectorAll('.mopt,.md-vote-opt'));
      p={slug:slug(),mi:mi,q:question(g),type:'multi',
         options:list.map(function(o){return {name:t(o.querySelector('.on,.nm,.md-vote-text'))||t(o),pct:pct(o)||0};}),
         pick:t(el.querySelector('.on,.nm,.md-vote-text'))||t(el)};
    }else{
      p={slug:slug(),mi:mi,q:question(g),type:'binary',yes:yesPct(g),side:isYes(el)?'yes':'no'};
    }
    el.setAttribute('data-forecast',JSON.stringify(p));
    if((' '+el.className+' ').indexOf(' fcbtn ')<0)el.className+=' fcbtn';
  }
  function wire(){
    var groups=[].slice.call(document.querySelectorAll(GRP));
    [].forEach.call(document.querySelectorAll(SEL),function(el){
      if(el.closest('.theme-toggle'))return;
      var g=el.closest(GRP);
      stamp(el,g?Math.max(0,groups.indexOf(g)):0);
    });
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',wire);
  else wire();
  document.addEventListener('click',function(e){
    var el=e.target.closest?e.target.closest(SEL):null;
    if(!el||el.closest('.theme-toggle'))return;
    var g=el.closest(GRP)||el.parentNode;
    if(g)[].forEach.call(g.querySelectorAll(SEL),function(o){o.classList.remove('selected');});
    el.classList.add('selected');
  },true);
})();

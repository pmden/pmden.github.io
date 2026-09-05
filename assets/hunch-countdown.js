/* Живий відлік до резолюції.
   Проблема: у прототипі 2670 рядків «N days left» зашиті в HTML на момент
   генерації сторінки і застигають наступного дня. Жоден скрипт їх не рахував.
   Рішення: після завантаження знаходимо пару «Resolves <дата> · N days left»
   і перераховуємо N від сьогодні. Дата лишається як є, вона факт.
   Минула дата дає «awaiting result», сьогодні дає «ends today». */
(function () {
  var MON = { jan:0, feb:1, mar:2, apr:3, may:4, jun:5,
              jul:6, aug:7, sep:8, oct:9, nov:10, dec:11 };

  function parse(txt) {
    var m = /(\d{1,2})\s+([A-Za-z]{3})[a-z]*\s+(\d{4})/.exec(txt);
    if (!m) return null;
    var mon = MON[m[2].toLowerCase()];
    if (mon === undefined) return null;
    return new Date(+m[3], mon, +m[1]);
  }

  function refresh() {
    var now = new Date();
    now = new Date(now.getFullYear(), now.getMonth(), now.getDate());

    var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null);
    var nodes = [], n;
    while ((n = walker.nextNode())) {
      if (/\bdays? left\b|\bends today\b|\bawaiting result\b/.test(n.nodeValue)) nodes.push(n);
    }

    nodes.forEach(function (node) {
      // дату шукаємо в цьому ж рядку, а якщо її нема — у батьківському блоці
      var host = node.parentElement;
      var when = parse(node.nodeValue) ||
                 (host ? parse(host.textContent) : null) ||
                 (host && host.parentElement ? parse(host.parentElement.textContent) : null);
      if (!when) return;

      var days = Math.round((when - now) / 86400000);
      var label = days > 1 ? days + ' days left'
                : days === 1 ? '1 day left'
                : days === 0 ? 'ends today'
                : 'awaiting result';

      node.nodeValue = node.nodeValue.replace(/\d+\s+days? left|ends today|awaiting result/, label);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', refresh);
  } else {
    refresh();
  }
})();

/* Дата в мастхеді. Була зашита при генерації сторінки: на 418 сторінках стояло
   «FRI, 21 AUG 2026». Тепер пишемо сьогоднішню, у тому самому форматі. */
(function () {
  function stamp() {
    var d = new Date();
    var wd = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'][d.getDay()];
    var mo = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][d.getMonth()];
    var txt = wd + ', ' + d.getDate() + ' ' + mo + ' ' + d.getFullYear();
    document.querySelectorAll('.row1 .date, .date').forEach(function (el) {
      // en-GB дає «Sept» для вересня, тому місяць тут три або чотири літери:
      // інакше дата на лендингу і в бібліотеці лишалась у своєму форматі
      if (/^\s*(Mon|Tue|Wed|Thu|Fri|Sat|Sun),\s*\d{1,2}\s+[A-Za-z]{3,4}\s+\d{4}\s*$/.test(el.textContent)) {
        el.textContent = txt;
      }
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', stamp);
  else stamp();
})();

/* Лічильники відкритих ринків. Були зняті вручну в різні дні і розійшлись:
   на сторінці ринків «79 open», у таб-барі «51» і «79» на різних сторінках.
   Рахуємо з розмітки, а не з памʼяті. Картки зі статусом pending (дата минула,
   підтвердженого джерела ще нема) відкритими НЕ вважаються. */
(function () {
  function counts() {
    var cards = document.querySelectorAll('.market-card[data-status]');
    if (!cards.length) return null;
    var live = 0, all = cards.length;
    cards.forEach(function (c) { if (c.dataset.status === 'live') live++; });
    return { live: live, all: all };
  }
  function apply() {
    var c = counts();
    if (!c) return;
    document.querySelectorAll('.v9-cat-meta, .cnt').forEach(function (el) {
      if (el.classList.contains('cnt')) { el.textContent = c.live; return; }
      el.innerHTML = el.innerHTML
        .replace(/\d+\s*markets/, c.all + ' markets')
        .replace(/\d+\s*(?:open|live)/, c.live + ' live');
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', apply);
  else apply();
})();

/* Лічильники беруться з одного джерела. Раніше кожна сторінка рахувала свої
   картки, тому MARKETS показував 51 на головній, 68 на ринках і 6 у категорії.
   Тепер число одне: воно порахуване з даних і зашите тут (QA, 2 Sep). */
(function () {
  function apply() {
    var C = { live: 0, resolved: 0, total: 0 };
    try { C = JSON.parse(document.getElementById('hunch-counts').textContent); } catch (e) { return; }
    if (!C.total) return;
    document.querySelectorAll('.m-tabbar .cnt').forEach(function (el) { el.textContent = C.live; });
    // рядок «364 markets · 68 open» правимо ТІЛЬКИ на сторінці ринків:
    // у категорій там свої, менші числа (QA, 2 Sep)
    if (!/hunch-markets/.test(location.pathname)) return;
    document.querySelectorAll('.v9-cat-meta').forEach(function (el) {
      el.innerHTML = el.innerHTML
        .replace(/\d+\s*markets/, C.total + ' markets')
        .replace(/\d+\s*(?:open|live)/, C.live + ' live')
        .replace(/\d+\s*resolved/, C.resolved + ' resolved');
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', apply);
  else apply();
})();

/* Фільтр статусу на телефоні. Обробник у сторінці навішений тільки на .v9-chip,
   а на 393px чипи приховані і видно лише нативний select, тому фільтр не
   реагував на дотик. Не дублюємо логіку, а натискаємо відповідний прихований
   чип: тоді працює і фільтрація, і посторінковий показ по 60 (QA, 2 Sep). */
(function () {
  function wire() {
    var sel = document.querySelector('.m-status-sel');
    if (!sel) return;
    sel.addEventListener('change', function () {
      var grp = sel.closest('.grp');
      if (grp) grp.setAttribute('data-label', sel.options[sel.selectedIndex].text);
      var chip = document.querySelector('.grp[data-grp="status"] .v9-chip[data-v="' + sel.value + '"]');
      if (chip) chip.click();
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', wire);
  else wire();
})();

/* Смуга розподілу над кнопками на телефоні (Pavlo, 2 Sep).
   Будується з наявного відсотка Yes, тому не потребує правок у 80+ файлах.
   Ставиться і в Echo (.bins), і на картках ринків (.mc-poll-binary). */
(function () {
  function pct(row) {
    var y = row.querySelector('.opt.yes .op, .mc-vote-yes .mc-vote-pct');
    if (!y) return null;
    var m = /(\d+(?:\.\d+)?)\s*%/.exec(y.textContent);
    return m ? parseFloat(m[1]) : null;
  }
  function build() {
    if (window.innerWidth > 560) return;
    document.querySelectorAll('.bins, .mc-poll-binary').forEach(function (row) {
      if (row.previousElementSibling && row.previousElementSibling.classList.contains('hb-split')) return;
      var v = pct(row);
      if (v === null) return;
      var bar = document.createElement('div');
      bar.className = 'hb-split';
      bar.innerHTML = '<i style="width:' + v + '%"></i>';
      bar.setAttribute('aria-hidden', 'true');
      row.parentNode.insertBefore(bar, row);
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', build);
  else build();
})();

/* Відсотки виносяться з кнопок і стають підписами обабіч смуги розподілу
   (Pavlo, 3 Sep). Зелений відсоток стоїть перед смугою, кларетовий після неї,
   смуга від того трохи коротша. На кнопках лишається тільки Yes і No.
   Розмітку сторінок не чіпаємо: числа вже є в кнопках, звідти й беремо. */
(function () {
  function num(el) {
    if (!el) return null;
    var m = /(\d+(?:\.\d+)?)\s*%/.exec(el.textContent);
    return m ? Math.round(parseFloat(m[1])) : null;
  }
  function label(cls, val) {
    var b = document.createElement('b');
    b.className = 'hb-num ' + cls;
    b.textContent = val + '%';
    return b;
  }
  function row(y, n) {
    var r = document.createElement('div');
    r.className = 'hb-row';
    var track = document.createElement('span');
    track.className = 'hb-track';
    track.innerHTML = '<i style="width:' + y + '%"></i>';
    r.appendChild(label('y', y));
    r.appendChild(track);
    r.appendChild(label('n', n));
    r.setAttribute('aria-hidden', 'true');
    return r;
  }
  function build() {
    // Echo: пара кнопок без власної смуги
    document.querySelectorAll('.bins').forEach(function (bins) {
      if (bins.previousElementSibling &&
          bins.previousElementSibling.classList.contains('hb-row')) return;
      var y = num(bins.querySelector('.opt.yes .op'));
      if (y === null) return;
      var n = num(bins.querySelector('.opt.no .op'));
      if (n === null) n = 100 - y;
      bins.parentNode.insertBefore(row(y, n), bins);
    });
    // Картки ринків: смуга вже в розмітці, підписуємо її з двох боків
    document.querySelectorAll('.mc-bar').forEach(function (bar) {
      if (bar.dataset.hbDone) return;
      var poll = bar.nextElementSibling;
      var y = num(poll && poll.querySelector('.mc-vote-yes .mc-vote-pct'));
      if (y === null) {
        var yw = bar.querySelector('.y');
        y = yw ? Math.round(parseFloat(yw.style.width) || 0) : null;
      }
      if (y === null) return;
      bar.dataset.hbDone = '1';
      var r = row(y, 100 - y);
      bar.parentNode.replaceChild(r, bar);
    });
    // застарілий варіант смуги без підписів більше не потрібен
    document.querySelectorAll('.hb-split').forEach(function (el) { el.remove(); });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', build);
  else build();
})();

/* Числа в меню беруть те саме джерело, що й решта сторінки. Раніше в макеті
   стояли зняті руками «68 live» і «290 resolved», які застигали (3 Sep). */
(function () {
  function apply() {
    var C;
    try { C = JSON.parse(document.getElementById('hunch-counts').textContent); } catch (e) { return; }
    document.querySelectorAll('.menu-row .n[data-cnt]').forEach(function (el) {
      var k = el.dataset.cnt;
      if (C[k] == null) { el.remove(); return; }
      el.textContent = C[k] + ' ' + k;
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', apply);
  else apply();
})();

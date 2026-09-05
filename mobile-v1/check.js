(()=>{
 const V=innerWidth, out=[];
 const push=(t,d)=>out.push({t,d:String(d).slice(0,80)});

 // 1. будь-який елемент, що виходить за екран
 document.querySelectorAll('body *').forEach(e=>{
   const r=e.getBoundingClientRect();
   if(e.closest('[class*=tw]')&&/auto|scroll/.test(getComputedStyle(e.closest('.tw')||e).overflowX)) return;
   if(r.width>0 && r.right>V+1) push('overflow', e.tagName+'.'+(e.className||'').toString().split(' ')[0]+' right='+Math.round(r.right));
 });
 // 2. хром, що протік у контент (дублі шапки всередині main)
 const m=document.querySelector('main');
 if(m){
   ['.row1','.row2','.menu-panel','.menu-backdrop','.footer-full','.m-tabbar','.bar','.cats'].forEach(s=>{
     if(m.querySelector(s)) push('chrome-leak', s);
   });
   const t=m.innerText||'';
   if(!/sitemap/.test(location.pathname)){
     [/Sat,\s*\d+\s+\w+\s+2026\s*Hunch/, /Hunch\s*Sign in\s*This week/].forEach((re,i)=>{
       if(re.test(t)) push('chrome-text','pattern '+i);
     });
   }
 }
 // 3. видима екранована розмітка
 if((document.body.innerText||'').match(/<a\s+href=|<\/a>|<strong>|<em>/)) push('escaped-html','видно теги текстом');
 // 4. нестилізовані посилання (дефолтний синій)
 document.querySelectorAll('a').forEach(a=>{
   const c=getComputedStyle(a).color;
   if(c==='rgb(0, 0, 238)'||c==='rgb(85, 26, 139)') push('unstyled-link', a.textContent.trim().slice(0,40));
 });
 // 5. кнопки без будь-якої поведінки
 document.querySelectorAll('button').forEach(b=>{
   if(b.disabled) return;
   const has=b.onclick||b.getAttribute('onclick')||b.closest('a')||b.form||b.type==='submit';
   if(!has) push('dead-button', b.textContent.trim().slice(0,30));
 });
 // 6. порожні або зламані посилання
 document.querySelectorAll('a[href]').forEach(a=>{
   const h=a.getAttribute('href');
   if(h==='#'||h===''||h==='javascript:void(0)') push('dead-link', a.textContent.trim().slice(0,30));
 });
 // 7. таблиці ширші за екран без прокрутки
 document.querySelectorAll('table').forEach(t=>{
   const r=t.getBoundingClientRect();
   const p=t.parentElement, ov=p?getComputedStyle(p).overflowX:'';
   if(r.width>V-20 && ov!=='auto' && ov!=='scroll') push('table-overflow', Math.round(r.width)+'px');
 });
 // 8. текст, що вилазить із контейнера по горизонталі
 document.querySelectorAll('h1,h2,h3,p,td,th,li').forEach(e=>{
   if(e.scrollWidth>e.clientWidth+2 && e.clientWidth>0) push('text-clip', e.tagName+' '+e.textContent.trim().slice(0,26));
 });
 const agg={};
 out.forEach(o=>{(agg[o.t]=agg[o.t]||[]).push(o.d)});
 const res={};
 Object.keys(agg).forEach(k=>{res[k]={n:agg[k].length, ex:[...new Set(agg[k])].slice(0,3)}});
 return JSON.stringify(res);
})()

(function(){
  var l=document.querySelector('.mh-l'),b=l&&l.querySelector('.mh-s');if(!l||!b)return;
  var logo=document.querySelector('.mh-b'),href=((logo&&logo.getAttribute('href'))||'index.html');
  var flat=/index\.html$/.test(href)||href===''||/-dark\.html$/.test(href);
  var dark=/(^|\/)dark\/$/.test(href)||/-dark\.html$/.test(href);
  var rel=href.replace(/index\.html$/,'').replace(/index-dark\.html$/,'').replace(/(^|\/)dark\/$/,'$1');
  var archive=flat?('archive'+(dark?'-dark':'')+'.html'):(rel+'archive/'+(dark?'dark/':''));
  var f=document.createElement('form');f.className='mh-q';f.setAttribute('role','search');
  var i=document.createElement('input');i.type='search';i.placeholder='Search Echoes and markets';i.setAttribute('aria-label','Search');i.autocomplete='off';
  f.appendChild(i);l.appendChild(f);
  function open(){l.classList.add('open');setTimeout(function(){i.focus()},0)}
  function close(){l.classList.remove('open')}
  b.addEventListener('click',function(e){e.preventDefault();if(l.classList.contains('open')&&!i.value.trim())close();else open()});
  f.addEventListener('submit',function(e){e.preventDefault();var q=i.value.trim();if(!q)return;location.href=archive+'?q='+encodeURIComponent(q)});
  i.addEventListener('keydown',function(e){if(e.key==='Escape'){i.value='';close()}});
  // клік назовні більше не ховає пошук (Pavlo, 11 Sep): закриває тільки лупа або Escape
  var q=new URLSearchParams(location.search).get('q');
  if(location.hash==='#search')open();
  if(q){i.value=q;open();filter(q)}
  function filter(q){
    var feeds=document.querySelectorAll('main .feed');if(!feeds.length)return;
    var words=(q||'').toLowerCase().split(/\s+/).filter(Boolean),n=0;
    feeds.forEach(function(fd){var vis=0;fd.querySelectorAll('article').forEach(function(a){var ok=words.every(function(w){return a.textContent.toLowerCase().indexOf(w)>-1});a.style.display=ok?'':'none';if(ok){vis++;n++}});
      var hd=fd.previousElementSibling;if(hd&&hd.classList.contains('sep-hd'))hd.style.display=vis?'':'none';fd.style.display=vis?'':'none'});
    var old=document.querySelector('main .tb-res');if(old)old.remove();
    if(!words.length)return;
    var hd=document.querySelector('main .pg-row')||document.querySelector('main h1');if(hd){var p=document.createElement('p');p.className='tb-res';
      p.textContent=n?(n+(n===1?' Echo matches “':' Echoes match “')+q+'”'):'No Echoes match “'+q+'”';hd.insertAdjacentElement('afterend',p)}
  }
  window.hunchFilter=filter;
})();

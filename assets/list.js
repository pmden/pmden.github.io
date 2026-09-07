(function(){
  var tb=document.querySelector('.tb[data-list]');if(!tb)return;
  var sel=tb.querySelector('select'),btn=tb.querySelector('.tb-s'),form=tb.querySelector('.tb-q'),inp=form&&form.querySelector('input');
  var MON={jan:0,feb:1,mar:2,apr:3,may:4,jun:5,jul:6,aug:7,sep:8,oct:9,nov:10,dec:11};
  var main=document.querySelector('main');
  function filter(q){
    var feeds=main.querySelectorAll('.feed');var words=(q||'').toLowerCase().split(/\s+/).filter(Boolean),n=0;
    feeds.forEach(function(fd){var vis=0;fd.querySelectorAll('article').forEach(function(a){var ok=words.every(function(w){return a.textContent.toLowerCase().indexOf(w)>-1});a.style.display=ok?'':'none';if(ok){vis++;n++}});
      var hd=fd.previousElementSibling;if(hd&&hd.classList.contains('sep-hd'))hd.style.display=vis?'':'none';fd.style.display=vis?'':'none'});
    var old=main.querySelector('.tb-res');if(old)old.remove();
    if(!words.length)return;
    var hd=main.querySelector('.pg-row')||main.querySelector('h1');if(hd){var p=document.createElement('p');p.className='tb-res';
      p.textContent=n?(n+(n===1?' Echo matches “':' Echoes match “')+q+'”'):'No Echoes match “'+q+'”';hd.insertAdjacentElement('afterend',p)}
  }
  var groups=[];main.querySelectorAll('.feed').forEach(function(fd){
    var hd=fd.previousElementSibling;if(!(hd&&hd.classList.contains('sep-hd')))hd=null;
    var mk=hd?hd.querySelector('.kick').textContent.trim():'';var mm=/^([A-Za-z]{3})[a-z]*\s+(\d{4})$/.exec(mk);
    var items=[];fd.querySelectorAll('article').forEach(function(a){
      var d=a.querySelector('.item-top .date'),dd=/(\d{1,2})\s+([A-Za-z]{3})/.exec(d?d.textContent:'');
      var y=mm?+mm[2]:new Date().getFullYear(),m=dd?MON[dd[2].toLowerCase()]:(mm?MON[mm[1].toLowerCase()]:0),day=dd?+dd[1]:1;
      var t=a.querySelector('.item-h');var k=a.querySelector('.item-top .kick');
      items.push({el:a,date:new Date(y,m,day).getTime(),title:(t?t.textContent:'').trim().toLowerCase(),kick:(k?k.textContent:'').trim().toLowerCase()});
    });
    groups.push({hd:hd,fd:fd,items:items,date:mm?new Date(+mm[2],MON[mm[1].toLowerCase()],1).getTime():(items[0]?items[0].date:0)});
  });
  if(!groups.length)return;
  var first=groups[0].fd;
  function render(mode){
    if(mode==='az'||mode==='topic'){
      var all=[];groups.forEach(function(g){all=all.concat(g.items)});
      all.sort(mode==='az'?function(a,b){return a.title<b.title?-1:a.title>b.title?1:0}:function(a,b){return a.kick<b.kick?-1:a.kick>b.kick?1:(b.date-a.date)});
      groups.forEach(function(g,i){if(g.hd)g.hd.style.display='none';g.fd.style.display=i?'none':''});
      all.forEach(function(it){first.appendChild(it.el)});
    }else{
      var desc=(mode!=='oldest');var parent=groups[0].hd?groups[0].hd.parentNode:first.parentNode;
      groups.slice().sort(function(a,b){return desc?b.date-a.date:a.date-b.date}).forEach(function(g){
        if(g.hd){g.hd.style.display='';parent.appendChild(g.hd)}g.fd.style.display='';parent.appendChild(g.fd);
        g.items.slice().sort(function(a,b){return desc?b.date-a.date:a.date-b.date}).forEach(function(it){g.fd.appendChild(it.el)});
      });
    }
    if(inp&&inp.value.trim())filter(inp.value.trim());
  }
  var q=new URLSearchParams(location.search);
  if(sel){sel.addEventListener('change',function(){render(sel.value)});if(q.get('sort')){sel.value=q.get('sort');render(sel.value)}}
  if(btn&&inp){
    btn.addEventListener('click',function(){tb.classList.toggle('open');if(tb.classList.contains('open'))inp.focus();else{inp.value='';filter('')}});
    inp.addEventListener('input',function(){filter(inp.value.trim())});
    inp.addEventListener('keydown',function(e){if(e.key==='Escape'){inp.value='';tb.classList.remove('open');filter('')}});
    form.addEventListener('submit',function(e){e.preventDefault()});
    if(q.get('find')){tb.classList.add('open');inp.value=q.get('find');filter(inp.value)}
  }
})();

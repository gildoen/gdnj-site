// 길된교회 — shared interactions
(function(){
  // mobile menu
  var hb=document.getElementById('hamburger'), mm=document.getElementById('mobileMenu');
  if(hb&&mm){hb.addEventListener('click',function(){var o=mm.classList.toggle('open');hb.setAttribute('aria-expanded',o)});}

  // scroll reveal
  if('IntersectionObserver' in window){
    var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target)}})},{threshold:.1,rootMargin:'0px 0px -40px 0px'});
    document.querySelectorAll('.reveal').forEach(function(el,i){el.style.transitionDelay=(i%4)*70+'ms';io.observe(el)});
  }else{document.querySelectorAll('.reveal').forEach(function(el){el.classList.add('in')})}

  // sub-nav: highlight the section currently in view
  var links=[].slice.call(document.querySelectorAll('.subnav a[href^="#"]'));
  if(links.length){
    var map={};links.forEach(function(a){map[a.getAttribute('href').slice(1)]=a});
    var secs=links.map(function(a){return document.getElementById(a.getAttribute('href').slice(1))}).filter(Boolean);
    var bar=document.querySelector('.subnav .wrap');
    function onScroll(){
      var y=window.scrollY+140, cur=secs[0];
      secs.forEach(function(s){if(s.offsetTop<=y)cur=s});
      links.forEach(function(a){a.classList.remove('on')});
      if(cur&&map[cur.id]){map[cur.id].classList.add('on');
        var a=map[cur.id]; if(bar&&(a.offsetLeft<bar.scrollLeft||a.offsetLeft+a.offsetWidth>bar.scrollLeft+bar.clientWidth)){bar.scrollTo({left:a.offsetLeft-60,behavior:'smooth'})}}
    }
    window.addEventListener('scroll',onScroll,{passive:true});onScroll();
  }

  // copy buttons
  document.querySelectorAll('[data-copy]').forEach(function(b){
    b.addEventListener('click',function(){
      var t=b.getAttribute('data-copy');
      (navigator.clipboard?navigator.clipboard.writeText(t):Promise.reject()).then(function(){var o=b.textContent;b.textContent='복사됨';setTimeout(function(){b.textContent=o},1400)}).catch(function(){});
    });
  });
})();

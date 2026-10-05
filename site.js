// 강의 사이트 동작: 메뉴, 펼치기/접기(?open=02 · #s02), 복사, 영상 누르면 재생
(function () {
  // 모바일 메뉴
  var nav = document.querySelector('.primary-nav');
  var toggle = document.querySelector('.nav-toggle');
  if (toggle && nav) {
    toggle.addEventListener('click', function () { nav.classList.toggle('open'); });
    nav.querySelectorAll('.nav-links a').forEach(function (a) {
      a.addEventListener('click', function () { nav.classList.remove('open'); });
    });
  }

  // 펼치기 / 접기
  function setOpen(section, open, instant) {
    var btn = section.querySelector('.lecture-toggle');
    var detail = section.querySelector('.lecture-detail');
    if (!btn || !detail) return;
    if (open === section.classList.contains('open')) return;
    if (open) {
      section.classList.add('open');
      detail.style.maxHeight = instant ? 'none' : detail.scrollHeight + 'px';
    } else {
      detail.style.maxHeight = detail.scrollHeight + 'px';
      requestAnimationFrame(function () {
        section.classList.remove('open');
        detail.style.maxHeight = '0px';
      });
    }
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
  }
  var sections = Array.prototype.slice.call(document.querySelectorAll('section.lecture'));
  sections.forEach(function (section) {
    var btn = section.querySelector('.lecture-toggle');
    var detail = section.querySelector('.lecture-detail');
    detail.addEventListener('transitionend', function (e) {
      if (e.propertyName === 'max-height' && section.classList.contains('open')) detail.style.maxHeight = 'none';
    });
    btn.addEventListener('click', function () { setOpen(section, !section.classList.contains('open')); });
  });

  function openById(id, scroll) {
    var s = document.getElementById(id);
    if (!s || !s.classList.contains('lecture')) return;
    setOpen(s, true, true);
    if (scroll) s.scrollIntoView();
  }
  // 주소로 펼치기: ?open=02 · ?open=02,05 · ?open=all · #s02
  // ?solo=02 : 그 실습 하나만 펼쳐서 보여 주기(링크 공유·화면 캡처용)
  var params = new URLSearchParams(location.search);
  var q = params.get('open');
  var solo = params.get('solo');
  function sid(n) { n = n.trim(); return n === '10' || n === 'end' ? 's10' : 's' + ('0' + n).slice(-2); }
  if (solo) {
    var keep = document.getElementById(sid(solo));
    if (keep) {
      document.body.classList.add('solo');
      keep.classList.add('solo-keep');
      var back = document.createElement('p');
      back.className = 'solo-back solo-keep';
      back.innerHTML = '<a class="btn btn-secondary btn-sm" href="' + location.pathname + '#' + keep.id + '">← 전체 페이지 보기</a>';
      keep.parentNode.insertBefore(back, keep);
      setOpen(keep, true, true);
    }
  }
  if (q) {
    if (q === 'all') sections.forEach(function (s) { setOpen(s, true, true); });
    else q.split(',').forEach(function (n) { openById(sid(n), false); });
  }
  if (location.hash) openById(location.hash.slice(1), true);
  window.addEventListener('hashchange', function () { openById(location.hash.slice(1), true); });
  document.querySelectorAll('a[href^="#s"]').forEach(function (a) {
    a.addEventListener('click', function () { openById(a.getAttribute('href').slice(1), false); });
  });
  var all = document.getElementById('openAll');
  if (all) all.addEventListener('click', function () {
    var anyClosed = sections.some(function (s) { return !s.classList.contains('open'); });
    sections.forEach(function (s) { setOpen(s, anyClosed, true); });
    all.textContent = anyClosed ? '모두 접기' : '모두 펼치기';
  });

  // 복사 (클립보드 API → 안 되면 textarea)
  var toast = document.getElementById('toast');
  function say(m) {
    if (!toast) return;
    toast.textContent = m; toast.classList.add('on');
    clearTimeout(say.t); say.t = setTimeout(function () { toast.classList.remove('on'); }, 1600);
  }
  function fallback(text) {
    var ta = document.createElement('textarea');
    ta.value = text; ta.setAttribute('readonly', '');
    ta.style.position = 'fixed'; ta.style.top = '0'; ta.style.opacity = '0';
    document.body.appendChild(ta); ta.select();
    var ok = false;
    try { ok = document.execCommand('copy'); } catch (e) {}
    document.body.removeChild(ta);
    return ok;
  }
  function copy(text, btn) {
    function done() {
      var prev = btn.getAttribute('data-label') || btn.textContent;
      btn.setAttribute('data-label', prev);
      btn.classList.add('copied'); btn.textContent = '복사됨';
      say('복사했어요! 입력창에 Ctrl+V');
      setTimeout(function () { btn.classList.remove('copied'); btn.textContent = prev; }, 1400);
    }
    function fail() { if (fallback(text)) done(); else say('복사가 막혔어요. 글을 끌어 선택해 Ctrl+C'); }
    if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(text).then(done, fail);
    else fail();
  }
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('.prompt-copy, [data-copy]');
    if (!btn) return;
    var text = btn.getAttribute('data-copy');
    if (!text) {
      var row = btn.closest('.prompt-row');
      text = row ? row.querySelector('.ptext').textContent.trim() : '';
    }
    if (text) copy(text, btn);
  });

  // 영상: 누르면 그 자리에서 재생
  document.querySelectorAll('.yt-lazy').forEach(function (b) {
    b.addEventListener('click', function () {
      var f = document.createElement('iframe');
      f.src = b.getAttribute('data-src');
      f.title = b.getAttribute('aria-label') || '영상';
      f.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';
      f.referrerPolicy = 'strict-origin-when-cross-origin';
      f.allowFullscreen = true;
      var box = document.createElement('div');
      box.className = b.className.replace('yt-lazy', '').trim();
      box.appendChild(f);
      b.parentNode.replaceChild(box, b);
    });
  });
})();

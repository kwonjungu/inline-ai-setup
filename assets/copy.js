/* 강의안 슬라이드마다 발표자 노트 속 '프롬프트 원문'을 찾아 [①번 복사] 버튼을 띄운다 */
(function () {
  var qs = new URLSearchParams(location.search);
  if (qs.get('print') === '1') return;

  var css = document.createElement('style');
  css.textContent =
    '.cpbar{position:absolute;left:56px;bottom:22px;display:flex;flex-wrap:wrap;gap:8px;z-index:30;max-width:70%}' +
    '.cpbtn{font:700 18px/1 Pretendard,system-ui,sans-serif;border:2px solid #111;background:#fff;color:#111;border-radius:999px;padding:11px 20px;cursor:pointer;box-shadow:0 4px 14px rgba(0,0,0,.12)}' +
    '.cpbtn:hover{background:#111;color:#fff}.cpbtn.ok{background:#ED1AA0;border-color:#ED1AA0;color:#fff}' +
    '.slide.dark .cpbtn{background:#111;color:#fff;border-color:#fff}' +
    '.cptoast{position:fixed;left:50%;bottom:36px;transform:translateX(-50%);background:#111;color:#fff;font:600 15px Pretendard,sans-serif;padding:10px 18px;border-radius:999px;opacity:0;transition:opacity .2s;z-index:9999;pointer-events:none}' +
    '.cptoast.on{opacity:1}' +
    '.cplink{position:fixed;top:16px;left:16px;z-index:60;font:600 13px Pretendard,sans-serif;background:#ED1AA0;color:#fff;border-radius:999px;padding:7px 14px;text-decoration:none}';
  document.head.appendChild(css);

  var toast = document.createElement('div');
  toast.className = 'cptoast';
  document.body.appendChild(toast);
  function say(msg) {
    toast.textContent = msg;
    toast.classList.add('on');
    clearTimeout(say.t);
    say.t = setTimeout(function () { toast.classList.remove('on'); }, 1600);
  }

  function copy(text, btn) {
    function done() {
      say('복사했어요! inline AI 입력창에 Ctrl+V');
      btn.classList.add('ok');
      setTimeout(function () { btn.classList.remove('ok'); }, 1500);
    }
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(done, function () { fallback(text) ? done() : say('복사가 막혔어요. 프롬프트 페이지를 써 주세요'); });
    } else {
      fallback(text) ? done() : say('복사가 막혔어요. 프롬프트 페이지를 써 주세요');
    }
  }
  function fallback(text) {
    var ta = document.createElement('textarea');
    ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
    document.body.appendChild(ta); ta.select();
    var ok = false;
    try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
    document.body.removeChild(ta);
    return ok;
  }

  // 노트의 blockquote 안: '프롬프트 원문(01-①, …):' 또는 '붙여 넣을 내용(…):' 다음 '> ' 줄들
  function parse(bq) {
    var lines = bq.innerHTML.split(/<br\s*\/?>/i).map(function (h) {
      var d = document.createElement('div'); d.innerHTML = h; return d.textContent;
    });
    var out = [], cur = null;
    lines.forEach(function (l) {
      var m = l.match(/^(?:프롬프트 원문|붙여 넣을 내용)\(([^,)]*)/);
      if (m) { cur = { label: m[1].trim(), lines: [] }; out.push(cur); return; }
      if (cur && /^\s*>\s?/.test(l)) cur.lines.push(l.replace(/^\s*>\s?/, ''));
    });
    return out.filter(function (p) { return p.lines.length; });
  }

  function label(raw) {
    var m = raw.match(/^(\d{2})-(.+)$/);
    if (m) return m[2] + '번 복사';
    if (/짧은판|메타/.test(raw)) return '지시사항 복사';
    return '복사';
  }

  document.querySelectorAll('.frame').forEach(function (fr) {
    var tpl = fr.querySelector('template.notes');
    var slide = fr.querySelector('section.slide');
    if (!tpl || !slide) return;
    var prompts = [];
    tpl.content.querySelectorAll('blockquote').forEach(function (bq) { prompts = prompts.concat(parse(bq)); });
    if (!prompts.length) return;
    var bar = document.createElement('div');
    bar.className = 'cpbar';
    prompts.forEach(function (p) {
      var b = document.createElement('button');
      b.type = 'button'; b.className = 'cpbtn';
      b.textContent = '📋 ' + label(p.label);
      b.title = p.lines.join('\n');
      b.addEventListener('click', function (e) { e.stopPropagation(); copy(p.lines.join('\n'), b); });
      bar.appendChild(b);
    });
    slide.appendChild(bar);
  });

  var a = document.createElement('a');
  a.className = 'cplink'; a.href = 'prompts.html'; a.target = '_blank'; a.rel = 'noopener';
  a.textContent = '프롬프트 모음';
  document.body.appendChild(a);
})();

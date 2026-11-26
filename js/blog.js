/* United Athila guides: menu, reading progress, contents highlight, search and filter */
document.addEventListener('DOMContentLoaded', function () {
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var tg = $('#navToggle'), mn = $('#mainNav');
  if (tg && mn) tg.addEventListener('click', function () { tg.setAttribute('aria-expanded', mn.classList.toggle('open') ? 'true' : 'false'); });
  var rp = $('#rp'), top = $('#toTop');
  function onScroll() {
    var h = document.documentElement.scrollHeight - window.innerHeight;
    if (rp) rp.style.width = (h > 0 ? Math.min(100, window.scrollY / h * 100) : 0) + '%';
    if (top) top.classList.toggle('show', window.scrollY > 700);
  }
  window.addEventListener('scroll', onScroll, { passive: true }); onScroll();
  if (top) top.addEventListener('click', function () { window.scrollTo({ top: 0, behavior: 'smooth' }); });
  var toast = $('#toast'), tt;
  function say(m) { if (!toast) return; toast.textContent = m; toast.classList.add('show'); clearTimeout(tt); tt = setTimeout(function () { toast.classList.remove('show'); }, 2000); }
  $$('[data-copy]').forEach(function (b) {
    b.addEventListener('click', function () {
      var url = location.href.split('#')[0];
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(url).then(function () { say('Link copied'); }, function () { say('Copy failed'); });
      else { var t = document.createElement('input'); t.value = url; document.body.appendChild(t); t.select(); try { document.execCommand('copy'); say('Link copied'); } catch (e) { say('Copy failed'); } document.body.removeChild(t); }
    });
  });
  var toc = $('.toc'); if (toc && window.innerWidth > 960) toc.setAttribute('open', '');
  var links = $$('.toc a');
  if (links.length && 'IntersectionObserver' in window) {
    var map = {}; links.forEach(function (a) { map[a.getAttribute('href').slice(1)] = a; });
    var io = new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting) { links.forEach(function (a) { a.classList.remove('on'); }); var a = map[e.target.id]; if (a) a.classList.add('on'); } }); }, { rootMargin: '-90px 0px -65% 0px' });
    $$('.post-body h2[id]').forEach(function (h) { io.observe(h); });
  }
  var q = $('#q'), cards = $$('.gcard[data-title]'), chips = $$('.chips2 button'), empty = $('.empty'), count = $('.count');
  if (cards.length) {
    var cat = 'all';
    var apply = function () {
      var term = q ? q.value.trim().toLowerCase() : '', n = 0;
      cards.forEach(function (c) { var ok = (cat === 'all' || c.getAttribute('data-cat') === cat) && (!term || c.getAttribute('data-title').toLowerCase().indexOf(term) > -1); c.classList.toggle('hide', !ok); if (ok) n++; });
      if (empty) empty.classList.toggle('show', n === 0);
      if (count) count.textContent = n + (n === 1 ? ' guide' : ' guides');
    };
    if (q) q.addEventListener('input', apply);
    chips.forEach(function (c) { c.addEventListener('click', function () { chips.forEach(function (x) { x.classList.remove('on'); }); c.classList.add('on'); cat = c.getAttribute('data-cat'); apply(); }); });
    apply();
  }
});

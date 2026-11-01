/* United Landmarks LLP: small page extras not covered by app.js
   (floor-plan filter tabs, lazy Google map, back-to-top button). */
document.addEventListener('DOMContentLoaded', function () {
  /* Show project name and Relationship Manager from config.js on the enquiry forms */
  var cfg = window.SITE_CONFIG || {};
  document.querySelectorAll('[data-config-text]').forEach(function (el) {
    var v = cfg[el.getAttribute('data-config-text')];
    if (v) el.textContent = v;
  });

  /* Floor-plan filter tabs */
  var tabs = document.querySelectorAll('.tab'), plans = document.querySelectorAll('.plan');
  tabs.forEach(function (tab) {
    tab.addEventListener('click', function () {
      var f = tab.getAttribute('data-filter');
      tabs.forEach(function (t) { var on = t === tab; t.classList.toggle('active', on); t.setAttribute('aria-selected', on ? 'true' : 'false'); });
      plans.forEach(function (p) { p.classList.toggle('hide', f !== 'all' && p.getAttribute('data-cat') !== f); });
    });
  });

  /* Lazy Google map: loads on tap, or automatically on tablet/desktop when near view */
  var wrap = document.getElementById('mapWrap');
  function loadMap() {
    if (!wrap || wrap.getAttribute('data-loaded')) return;
    var f = document.createElement('iframe');
    f.src = wrap.getAttribute('data-src');
    f.title = 'Map of Dhanori, Pune: United Landmarks LLP project location';
    f.loading = 'lazy';
    f.referrerPolicy = 'no-referrer-when-downgrade';
    f.allowFullscreen = true;
    wrap.innerHTML = '';
    wrap.appendChild(f);
    wrap.setAttribute('data-loaded', '1');
  }
  if (wrap) {
    var btn = document.getElementById('loadMap');
    if (btn) btn.addEventListener('click', loadMap);
    if ('IntersectionObserver' in window && window.matchMedia('(min-width: 768px)').matches) {
      var mo = new IntersectionObserver(function (en) { if (en[0].isIntersecting) { loadMap(); mo.disconnect(); } }, { rootMargin: '200px' });
      mo.observe(wrap);
    }
  }

  /* Back to top */
  var top = document.getElementById('toTop');
  if (top) {
    window.addEventListener('scroll', function () { top.classList.toggle('show', window.scrollY > 600); }, { passive: true });
    top.addEventListener('click', function () { window.scrollTo({ top: 0, behavior: 'smooth' }); });
  }
});

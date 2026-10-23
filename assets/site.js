/* PromptMaster website — the only script. Everything works without it. */
(function () {
  'use strict';

  // Remember a language the visitor picks, so the root page sends them there next time.
  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[data-lang]');
    if (!a) return;
    try { localStorage.setItem('pm-lang', a.getAttribute('data-lang')); } catch (err) {}
  });

  // Language menu: close on outside click and on Escape.
  var menus = document.querySelectorAll('details.lang');
  document.addEventListener('click', function (e) {
    menus.forEach(function (d) { if (d.open && !d.contains(e.target)) d.open = false; });
  });
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    menus.forEach(function (d) {
      if (d.open) { d.open = false; d.querySelector('summary').focus(); }
    });
  });

  // Deep links to a question (support/#cancel-ios) open that answer.
  function openTarget() {
    var id = decodeURIComponent(location.hash.slice(1));
    if (!id) return;
    var el = document.getElementById(id);
    if (el && el.tagName === 'DETAILS') el.open = true;
  }
  openTarget();
  window.addEventListener('hashchange', openTarget);
})();

document.querySelectorAll('[data-page-back]').forEach(link => {
  link.addEventListener('click', event => {
    // Preserve normal link behavior for opening in another tab.
    if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    let previous;
    try { previous = new URL(document.referrer); } catch { return; }
    const current = new URL(window.location.href);
    // Direct/new-tab visits use the link fallback; never return to another site
    // or to the same form after a successful POST/redirect.
    if (window.history.length > 1 && previous.origin === current.origin
        && previous.pathname + previous.search !== current.pathname + current.search
        && !previous.pathname.startsWith('/accounts/')) {
      event.preventDefault();
      window.history.back();
    }
  });
});

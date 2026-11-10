if (new URLSearchParams(window.location.search).get('print') === '1') {
  // Remove the flag before printing so refresh/back does not reopen the dialog.
  const cleanUrl = new URL(window.location.href);
  cleanUrl.searchParams.delete('print');
  window.history.replaceState(window.history.state, '', cleanUrl);
  window.addEventListener('load', async () => {
    if (document.fonts?.ready) await document.fonts.ready;
    window.print();
  }, { once: true });
}

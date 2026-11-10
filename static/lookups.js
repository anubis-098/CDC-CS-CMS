(() => {
  const form = document.getElementById('claim-form');
  if (!form?.dataset.suggestionsUrl) return;
  const popup = document.createElement('div');
  popup.className = 'lookup-popup';
  popup.id = 'claim-suggestions';
  popup.hidden = true;
  const list = document.createElement('div');
  list.id = 'claim-suggestions-list';
  list.setAttribute('role', 'listbox');
  list.setAttribute('aria-label', 'ข้อมูลที่เคยบันทึก');
  const status = document.createElement('div');
  status.className = 'lookup-status';
  status.setAttribute('role', 'status');
  popup.append(list, status);
  document.body.append(popup);
  let active = null, results = [], selected = -1, timer, controller, version = 0;

  function close() {
    clearTimeout(timer);
    controller?.abort();
    version++;
    popup.hidden = true;
    if (active) {
      active.setAttribute('aria-expanded', 'false');
      active.removeAttribute('aria-activedescendant');
    }
    selected = -1;
  }

  function position() {
    if (!active || popup.hidden) return;
    const rect = active.getBoundingClientRect();
    const width = Math.min(Math.max(rect.width, 280), window.innerWidth - 16);
    popup.style.width = `${width}px`;
    popup.style.left = `${Math.max(8, Math.min(rect.left, window.innerWidth - width - 8))}px`;
    const below = window.innerHeight - rect.bottom - 12;
    const above = rect.top - 12;
    const useAbove = below < 180 && above > below;
    popup.style.maxHeight = `${Math.max(60, Math.min(280, useAbove ? above : below))}px`;
    popup.style.top = useAbove ? 'auto' : `${rect.bottom + 4}px`;
    popup.style.bottom = useAbove ? `${window.innerHeight - rect.top + 4}px` : 'auto';
  }

  function choose(index) {
    const result = results[index];
    if (!result || !active) return;
    const group = active.dataset.lookupGroup;
    const scope = active.closest('.item-row') || form;
    scope.querySelectorAll('[data-lookup-group]').forEach(input => {
      if (input.dataset.lookupGroup !== group) return;
      const key = input.dataset.lookupField;
      if (Object.hasOwn(result.values, key)) {
        input.value = result.values[key];
        input.dispatchEvent(new Event('change', { bubbles: true }));
      }
    });
    close();
    active.focus({ preventScroll: true });
  }

  function highlight(index) {
    selected = index;
    [...list.children].forEach((option, i) => option.setAttribute('aria-selected', String(i === index)));
    const option = list.children[index];
    if (option) {
      active.setAttribute('aria-activedescendant', option.id);
      option.scrollIntoView({ block: 'nearest' });
    }
  }

  function show(message) {
    list.replaceChildren();
    results.forEach((result, index) => {
      const option = document.createElement('div');
      option.id = `claim-suggestion-${index}`;
      option.className = 'lookup-option';
      option.setAttribute('role', 'option');
      option.setAttribute('aria-selected', 'false');
      option.textContent = result.label;
      option.addEventListener('mousedown', event => event.preventDefault());
      option.addEventListener('click', () => choose(index));
      list.append(option);
    });
    status.textContent = message;
    active.setAttribute('aria-controls', list.id);
    active.setAttribute('aria-expanded', 'true');
    active.removeAttribute('aria-activedescendant');
    selected = -1;
    popup.hidden = false;
    position();
  }

  function search(input) {
    close();
    active = input;
    results = [];
    const query = input.value.trim();
    if (query.length < 2) return;
    const requestVersion = version;
    timer = setTimeout(async () => {
      controller = new AbortController();
      const url = new URL(form.dataset.suggestionsUrl, window.location.origin);
      url.search = new URLSearchParams({ group: input.dataset.lookupGroup, field: input.dataset.lookupField, q: query });
      show('กำลังค้นหาข้อมูลที่เคยบันทึก…');
      try {
        const response = await fetch(url, { signal: controller.signal, headers: { Accept: 'application/json' } });
        if (!response.ok) throw new Error('Lookup failed');
        const data = await response.json();
        if (version !== requestVersion || active !== input || input.value.trim() !== query) return;
        results = data.results;
        show(results.length ? 'เลือกเพื่อเติมข้อมูลที่สัมพันธ์กัน · ↑ ↓ และ Enter หรือคลิก' : 'ไม่พบข้อมูลเดิม กรอกข้อมูลใหม่ได้ตามปกติ');
      } catch (error) {
        if (error.name !== 'AbortError' && version === requestVersion) show('ค้นหาไม่สำเร็จ สามารถกรอกข้อมูลเองได้');
      }
    }, 220);
  }

  form.addEventListener('input', event => {
    if (event.target.matches('[data-lookup-group]') && !event.isComposing) search(event.target);
  });
  form.addEventListener('compositionend', event => {
    if (event.target.matches('[data-lookup-group]')) search(event.target);
  });
  form.addEventListener('focusin', event => {
    if (event.target !== active) close();
  });
  form.addEventListener('keydown', event => {
    if (!event.target.matches('[data-lookup-group]')) return;
    if (event.key === 'Escape' || event.key === 'Tab') { close(); return; }
    if (popup.hidden) {
      if (event.key === 'ArrowDown') { event.preventDefault(); search(event.target); }
      return;
    }
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault();
      if (results.length) highlight((selected + (event.key === 'ArrowDown' ? 1 : -1) + results.length) % results.length);
    } else if (event.key === 'Enter' && selected >= 0) { event.preventDefault(); choose(selected); }
  });
  document.addEventListener('pointerdown', event => {
    if (!popup.contains(event.target) && event.target !== active) close();
  });
  // Position outside panels so compact forms never clip the suggestion list.
  window.addEventListener('resize', position);
  window.addEventListener('scroll', position, true);
  form.addEventListener('submit', close);
})();

(() => {
  const form = document.getElementById('claim-form');
  const input = document.getElementById('id_document_number');
  const button = document.getElementById('load-document');
  const status = document.getElementById('document-lookup-status');
  if (!form || !input || !button) return;
  let controller, version = 0, dirty = false;
  form.addEventListener('input', event => { if (event.target !== input) dirty = true; });
  form.addEventListener('change', event => { if (event.target !== input) dirty = true; });
  input.addEventListener('input', () => { controller?.abort(); version++; });
  async function load() {
    const number = input.value.trim();
    if (!number) { status.textContent = 'เว้นว่างไว้ ระบบจะสร้างเลขที่ให้เมื่อบันทึก'; return; }
    controller?.abort();
    controller = new AbortController();
    const current = ++version;
    status.textContent = 'กำลังค้นหาเลขที่เอกสาร…';
    const url = new URL(form.dataset.documentLookupUrl, location.origin);
    url.searchParams.set('number', number);
    try {
      const response = await fetch(url, { signal: controller.signal, headers: { Accept: 'application/json' } });
      if (!response.ok) throw new Error('Lookup failed');
      const data = await response.json();
      if (current !== version || number !== input.value.trim()) return;
      if (!data.found) { status.textContent = 'ยังไม่มีเลขที่นี้ กรอกข้อมูลแล้วบันทึกเพื่อสร้างเอกสารใหม่'; return; }
      if (dirty && !confirm('พบเอกสารเดิม ต้องการโหลดข้อมูลที่บันทึกไว้แทนข้อมูลที่ยังไม่ได้บันทึกในฟอร์มนี้หรือไม่?')) {
        status.textContent = 'ยังไม่ได้โหลดเอกสารเดิม กดโหลดเลขที่เอกสารเมื่อต้องการแก้ไข';
        return;
      }
      location.assign(data.url);
    } catch (error) {
      if (error.name !== 'AbortError' && current === version) status.textContent = 'โหลดไม่ได้ กรุณาตรวจสอบสิทธิ์หรือการเชื่อมต่อแล้วลองอีกครั้ง';
    }
  }
  input.addEventListener('change', load);
  input.addEventListener('keydown', event => { if (event.key === 'Enter') { event.preventDefault(); load(); } });
  button.addEventListener('click', load);
})();

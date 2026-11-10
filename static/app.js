document.getElementById('print')?.addEventListener('click', () => window.print());
const claimForm = document.getElementById('claim-form');
if (claimForm) {
  let dirty = false;
  claimForm.addEventListener('input', () => { dirty = true; });
  claimForm.addEventListener('change', () => { dirty = true; });
  document.querySelectorAll('.print-saved-document').forEach(link => {
    link.addEventListener('click', event => {
      if (dirty && !confirm('มีข้อมูลที่ยังไม่ได้บันทึก ต้องการออกจากหน้านี้เพื่อพิมพ์เอกสารที่บันทึกไว้หรือไม่?')) event.preventDefault();
    });
  });
}
const undoClear = document.getElementById('undo-clear');
const clearStatus = document.getElementById('clear-form-status');
let beforeClear = null;
document.getElementById('clear-form')?.addEventListener('click', () => {
  if (!claimForm) return;
  const fields = [...claimForm.querySelectorAll('input, textarea, select')].filter(field =>
    !field.disabled && !field.readOnly && field.name !== 'document_number'
    && !['hidden', 'checkbox', 'radio', 'submit', 'button'].includes(field.type));
  // Keep primary keys, formset counts, CSRF, document identity and deletion flags.
  beforeClear = fields.map(field => ({ field, value: field.value }));
  fields.forEach(field => {
    if (field.tagName === 'SELECT' && ![...field.options].some(option => option.value === '')) {
      const blank = new Option('— เลือก —', '');
      blank.dataset.clearPlaceholder = 'true';
      field.prepend(blank);
    }
    field.value = '';
    field.dispatchEvent(new Event('input', { bubbles: true }));
    field.dispatchEvent(new Event('change', { bubbles: true }));
  });
  undoClear.hidden = false;
  clearStatus.textContent = 'ล้างค่าในฟอร์มแล้ว ยังไม่ได้บันทึกลงฐานข้อมูล';
  fields[0]?.focus({ preventScroll: true });
});
undoClear?.addEventListener('click', () => {
  beforeClear?.forEach(({ field, value }) => {
    field.querySelectorAll('option[data-clear-placeholder]').forEach(option => option.remove());
    field.value = value;
    field.dispatchEvent(new Event('change', { bubbles: true }));
  });
  body?.querySelectorAll('.item-row').forEach(updateRow);
  beforeClear = null;
  undoClear.hidden = true;
  clearStatus.textContent = 'คืนค่าก่อนล้างแล้ว';
});
const body = document.getElementById('items-body');
function updateRow(row) {
  const load = row.querySelector('[name$="-load"]');
  const claim = row.querySelector('[name$="-st_claim"]');
  const deleted = row.querySelector('[name$="-DELETE"]');
  row.classList.toggle('deleted', Boolean(deleted?.checked));
  const output = row.querySelector('.diff');
  const complete = load.value !== '' && claim.value !== '' && Number.isFinite(Number(load.value)) && Number.isFinite(Number(claim.value));
  const difference = complete ? Math.round(Number(load.value) * 1000) - Math.round(Number(claim.value) * 1000) : null;
  output.textContent = complete ? (difference / 1000).toFixed(3) : '—';
  output.classList.toggle('diff-match', complete && difference === 0);
  output.classList.toggle('diff-mismatch', complete && difference !== 0);
  row.querySelectorAll('input, select').forEach(input => {
    if (deleted?.checked && input.required) { input.dataset.wasRequired = '1'; input.required = false; }
    else if (!deleted?.checked && input.dataset.wasRequired) { input.required = true; delete input.dataset.wasRequired; }
  });
}
body?.addEventListener('input', e => { const row = e.target.closest('.item-row'); if (row) updateRow(row); });
body?.querySelectorAll('.item-row').forEach(updateRow);
document.getElementById('add-item')?.addEventListener('click', () => {
  const total = document.getElementById('id_items-TOTAL_FORMS');
  if (Number(total.value) >= 200) { alert('รองรับสูงสุด 200 รายการต่อเอกสาร'); return; }
  body.insertAdjacentHTML('beforeend', document.getElementById('empty-item').innerHTML.replaceAll('__prefix__', total.value));
  total.value = Number(total.value) + 1;
  updateRow(body.lastElementChild);
  body.lastElementChild.querySelector('select').focus();
});

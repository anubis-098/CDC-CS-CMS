document.querySelectorAll('.claim-status-form').forEach(form => {
  const select = form.elements.status;
  const previous = form.elements.previous_status;
  const message = form.querySelector('.status-message');
  form.addEventListener('submit', event => event.preventDefault());
  select.addEventListener('change', async () => {
    const data = new FormData(form);
    select.disabled = true;
    message.textContent = 'กำลังบันทึก…';
    message.classList.remove('status-error');
    try {
      const response = await fetch(form.action, { method: 'POST', body: data, headers: { Accept: 'application/json' } });
      if (response.redirected) throw new Error('กรุณาเข้าสู่ระบบใหม่ แล้วลองอีกครั้ง');
      const result = response.headers.get('content-type')?.includes('application/json') ? await response.json() : {};
      if (!response.ok) throw new Error(result.error || 'บันทึกไม่สำเร็จ กรุณาตรวจสอบสิทธิ์หรือโหลดหน้าใหม่');
      previous.value = result.status;
      form.elements.version.value = result.version;
      select.value = result.status;
      select.className = `badge status-select ${result.status}`;
      message.textContent = 'บันทึกแล้ว';
      const filter = new URLSearchParams(location.search).get('status');
      if (filter && filter !== result.status) location.reload();
    } catch (error) {
      select.value = previous.value;
      message.textContent = error.message || 'เชื่อมต่อไม่สำเร็จ กรุณาโหลดหน้าใหม่เพื่อตรวจสอบสถานะ';
      message.classList.add('status-error');
    } finally {
      select.disabled = false;
    }
  });
});

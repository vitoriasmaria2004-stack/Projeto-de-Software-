document.addEventListener('DOMContentLoaded', () => {
  // close button
  document.querySelectorAll('.modal-close').forEach(btn => btn.addEventListener('click', () => {
    document.querySelector('.demo-backdrop').style.display = 'none';
  }));

  // upload area click
  const coverInput = document.getElementById('cover-input');
  document.querySelectorAll('.upload-area').forEach(area => {
    area.addEventListener('click', () => coverInput.click());
  });

  coverInput?.addEventListener('change', (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const img = new Image();
      img.src = reader.result;
      img.style.maxWidth = '100%';
      img.style.borderRadius = '8px';
      const area = document.querySelector('.upload-inner');
      if (area) area.innerHTML = '';
      area.appendChild(img);
    };
    reader.readAsDataURL(file);
  });

  // WYSIWYG toolbar (basic)
  const editor = document.getElementById('editor');
  document.querySelectorAll('.tb-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const cmd = btn.dataset.cmd;
      if (!cmd) return;
      document.execCommand(cmd, false, null);
      editor.focus();
    });
  });

  // font select
  const fontSelect = document.getElementById('font-select');
  fontSelect?.addEventListener('change', (e) => {
    editor.style.fontFamily = e.target.value;
    editor.focus();
  });

  // font size slider
  const fontSize = document.getElementById('font-size');
  fontSize?.addEventListener('input', (e) => {
    const size = e.target.value + 'px';
    editor.style.fontSize = size;
    editor.focus();
  });

  // Add / Finish chapter (demo only)
  document.getElementById('add-chapter')?.addEventListener('click', () => {
    const title = document.getElementById('chapter-title').value || 'Novo capítulo';
    const newNode = document.createElement('div');
    newNode.innerHTML = `<h4 style="margin:10px 0 6px">${escapeHtml(title)}</h4><p style="color:#9aa3b2">Capítulo criado (demo)</p>`;
    // small visual feedback
    newNode.style.borderTop = '1px dashed rgba(255,255,255,0.03)';
    newNode.style.paddingTop = '10px';
    document.querySelector('.right-col').appendChild(newNode);
  });

  document.getElementById('finish-chapter')?.addEventListener('click', () => {
    alert('Capítulo finalizado (demo)');
  });
});

function escapeHtml(s){return String(s||'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');}
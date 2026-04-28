// Integration glue: connect demo modal fields to existing handlers in app.js
document.addEventListener('DOMContentLoaded', () => {
  // open modal by existing writer add button
  document.querySelectorAll('.writer-add-book-card, .writer-add-book-card').forEach(btn => btn.addEventListener('click', (e) => {
    e.preventDefault();
    const modal = document.getElementById('writer-editor-modal');
    modal.classList.remove('hidden');
    modal.setAttribute('aria-hidden','false');
    const backdrop = document.getElementById('writer-editor-backdrop');
    if (backdrop) backdrop.classList.remove('hidden');
  }));

  // close
  document.getElementById('writer-editor-close')?.addEventListener('click', () => {
    const modal = document.getElementById('writer-editor-modal');
    modal.classList.add('hidden');
    modal.setAttribute('aria-hidden','true');
  });

  // forward the story-synopsis textarea into nova-historia-form before submit
  const novaForm = document.getElementById('nova-historia-form');
  novaForm?.addEventListener('submit', (e) => {
    // ensure synopse value is set
    const synopsis = document.getElementById('story-synopsis')?.value || '';
    let existing = novaForm.querySelector('textarea[name="sinopse"]');
    if (!existing) {
      const ta = document.createElement('textarea');
      ta.name = 'sinopse';
      ta.style.display='none';
      ta.value = synopsis;
      novaForm.appendChild(ta);
    } else {
      existing.value = synopsis;
    }
  });

  // wire finish-chapter to submit novo-capitulo-form
  document.getElementById('finish-chapter')?.addEventListener('click', () => {
    const capForm = document.getElementById('novo-capitulo-form');
    // copy editor content to textarea 'conteudo'
    const editorText = document.getElementById('editor-textarea')?.value || '';
    let conteudo = capForm.querySelector('textarea[name="conteudo"]');
    if (!conteudo) {
      const ta = document.createElement('textarea');
      ta.name = 'conteudo';
      ta.style.display='none';
      ta.value = editorText;
      capForm.appendChild(ta);
    } else {
      conteudo.value = editorText;
    }
    capForm.requestSubmit();
  });

  // basic toolbar actions mapped to textarea selection/format (execCommand limited)
  document.querySelectorAll('.toolbar .tb-btn').forEach(btn => btn.addEventListener('click', () => {
    const cmd = btn.dataset.cmd;
    const ta = document.getElementById('editor-textarea');
    if (!ta) return;
    // naive: wrap selection in markup for preview; for storage we keep plain textarea
    const start = ta.selectionStart;
    const end = ta.selectionEnd;
    const sel = ta.value.substring(start, end);
    let wrapped = sel;
    if (cmd === 'bold') wrapped = `**${sel}**`;
    if (cmd === 'italic') wrapped = `*${sel}*`;
    if (cmd === 'underline') wrapped = `_${sel}_`;
    if (cmd === 'insertUnorderedList') wrapped = sel.split('\n').map(l => `- ${l}`).join('\n');
    if (cmd === 'insertOrderedList') wrapped = sel.split('\n').map((l,i) => `${i+1}. ${l}`).join('\n');
    ta.setRangeText(wrapped, start, end, 'end');
    ta.focus();
  }));
});

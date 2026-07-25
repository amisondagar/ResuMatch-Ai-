/**
 * static/js/upload.js — Resume Upload Drag & Drop
 * ResumeMatch.ai
 */

document.addEventListener('DOMContentLoaded', () => {
  const zone     = document.getElementById('uploadZone');
  const input    = document.getElementById('resumeInput');
  const preview  = document.getElementById('filePreview');
  const countEl  = document.getElementById('fileCount');

  if (!zone || !input) return;

  // ── Drag & Drop ──────────────────────────────────────────────────────
  ['dragenter','dragover'].forEach(evt => {
    zone.addEventListener(evt, e => {
      e.preventDefault();
      zone.classList.add('drag-over');
    });
  });

  ['dragleave','drop'].forEach(evt => {
    zone.addEventListener(evt, e => {
      e.preventDefault();
      zone.classList.remove('drag-over');
    });
  });

  zone.addEventListener('drop', e => {
    const files = e.dataTransfer.files;
    input.files  = files;
    showPreviews(files);
  });

  input.addEventListener('change', () => showPreviews(input.files));

  function showPreviews(files) {
    if (!preview) return;
    preview.innerHTML = '';

    const valid = [];
    const invalid = [];

    Array.from(files).forEach(f => {
      const ext = f.name.split('.').pop().toLowerCase();
      if (['pdf','docx','doc'].includes(ext)) valid.push(f);
      else invalid.push(f);
    });

    if (countEl) countEl.textContent = valid.length + ' file(s) selected';

    valid.forEach(f => {
      const size = f.size < 1024*1024
        ? (f.size/1024).toFixed(1) + ' KB'
        : (f.size/1024/1024).toFixed(1) + ' MB';

      const icon = f.name.endsWith('.pdf') ? '📄' : '📝';
      const div  = document.createElement('div');
      div.className = 'file-item';
      div.innerHTML = `
        <span class="file-icon">${icon}</span>
        <div class="file-info">
          <div class="file-name">${f.name}</div>
          <div class="file-size">${size}</div>
        </div>
        <span class="badge badge-success">Ready</span>`;
      preview.appendChild(div);
    });

    invalid.forEach(f => {
      const div = document.createElement('div');
      div.className = 'file-item error';
      div.innerHTML = `
        <span class="file-icon">❌</span>
        <div class="file-info">
          <div class="file-name">${f.name}</div>
          <div class="file-size text-danger">Unsupported format</div>
        </div>
        <span class="badge badge-danger">Invalid</span>`;
      preview.appendChild(div);
    });
  }
});

document.addEventListener('DOMContentLoaded', function () {
  const input = document.getElementById('datasetFile');
  const zone = document.getElementById('dropZone');
  const output = document.getElementById('selectedFile');
  const form = document.getElementById('uploadForm');
  const button = document.getElementById('uploadButton');
  function showFile(file) { if (file) { output.textContent = 'Selected: ' + file.name + ' (' + (file.size / 1024 / 1024).toFixed(2) + ' MB)'; output.classList.remove('d-none'); } }
  input.addEventListener('change', () => showFile(input.files[0]));
  ['dragenter', 'dragover'].forEach(event => zone.addEventListener(event, e => { e.preventDefault(); zone.classList.add('drag'); }));
  ['dragleave', 'drop'].forEach(event => zone.addEventListener(event, e => { e.preventDefault(); zone.classList.remove('drag'); }));
  zone.addEventListener('drop', e => { input.files = e.dataTransfer.files; showFile(input.files[0]); });
  form.addEventListener('submit', () => { button.disabled = true; button.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Reading dataset...'; });
});

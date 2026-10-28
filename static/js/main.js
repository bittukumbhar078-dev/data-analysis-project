document.addEventListener('DOMContentLoaded', function () {
  const button = document.getElementById('menuButton');
  const sidebar = document.getElementById('sidebar');
  if (button && sidebar) button.addEventListener('click', () => sidebar.classList.toggle('show'));
});

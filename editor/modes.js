document.getElementById('mode-toggle').addEventListener('click', function() {
  document.body.classList.toggle('dark-mode');

  // Change button text based on the current mode
  if (document.body.classList.contains('dark-mode')) {
    this.textContent = 'Switch to Light Mode';
  } else {
    this.textContent = 'Switch to Dark Mode';
  }
});

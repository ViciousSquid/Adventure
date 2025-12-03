export function replaceSpacesWithUnderscores(string) {
  return string.replace(/\s/g, '_');
}

export function updateMode(isLightMode) {
  const body = document.body;
  const modeToggleCheckbox = document.getElementById('modeToggleCheckbox');
  if (!modeToggleCheckbox) return;
  
  const modeToggleText = modeToggleCheckbox.nextElementSibling;
  if (modeToggleText) {
    modeToggleText.textContent = isLightMode ? 'Dark Mode' : 'Light Mode';
  }

  body.classList.remove('light-mode');

  if (isLightMode) {
    body.classList.add('light-mode');
  }
}

export function replaceSpacesWithUnderscores(string) {
    return string.replace(/\s/g, '_');
  }
  
  export function updateMode(isLightMode) {
    const body = document.body;
    const modeToggleText = modeToggleCheckbox.nextElementSibling;
    modeToggleText.textContent = isLightMode ? 'Dark Mode' : 'Light Mode';
  
    // Remove the light-mode class from the body if it exists
    body.classList.remove('light-mode');
  
    // Add or remove the light-mode class based on the isLightMode value
    if (isLightMode) {
      body.classList.add('light-mode');
    }
  }
// main2.js
document.addEventListener('DOMContentLoaded', function() {
    const summaryInput = document.createElement('textarea');
    summaryInput.id = 'summary';
    summaryInput.name = 'summary';
    summaryInput.placeholder = 'Summary (max 250 characters)';
    summaryInput.maxLength = 250;
  
    const storyForm = document.getElementById('storyForm');
    storyForm.appendChild(summaryInput);
  });
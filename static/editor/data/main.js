import { addRoom, setupEventDelegation, showFlowchart, getStoryData } from './storyEditor.js';
import { saveStoryAsJsonFile, loadStoryFromZip } from './storyIO.js';

console.log("Editor > Init event listeners..");

document.addEventListener('DOMContentLoaded', function() {
  // Create summary textarea
  const summaryInput = document.createElement('textarea');
  summaryInput.id = 'summary';
  summaryInput.name = 'summary';
  summaryInput.placeholder = 'Summary (max 250 characters)';
  summaryInput.maxLength = 250;

  const storyForm = document.getElementById('storyForm');
  const roomsHeading = document.querySelector('h2');
  storyForm.insertBefore(summaryInput, roomsHeading);

  // Set up event delegation for dynamic room/exit buttons (call once!)
  setupEventDelegation();

  // Top bar button handlers - these are static, so simple addEventListener works
  document.getElementById('addRoomLink').addEventListener('click', function(event) {
    event.preventDefault();
    addRoom();
  });

  document.getElementById('loadStoryLink').addEventListener('click', function(event) {
    event.preventDefault();
    loadStoryFromZip();
  });

  document.getElementById('saveStoryLink').addEventListener('click', function(event) {
    event.preventDefault();
    const storyJson = getStoryData();
    saveStoryAsJsonFile(storyJson);
  });

  document.getElementById('flowchartLink').addEventListener('click', function(event) {
    event.preventDefault();
    showFlowchart();
  });

  document.getElementById('newStoryLink').addEventListener('click', function(event) {
    event.preventDefault();
    
    // Clear existing form fields
    document.getElementById('storyName').value = '';
    document.getElementById('buttonColor').value = '#000000';
    document.getElementById('startRoom').value = '';
    document.getElementById('roomsContainer').innerHTML = '';
    document.getElementById('summary').value = '';
    document.getElementById('cover-thumbnail').src = '';

    // Add a new room
    addRoom();
  });

  storyForm.addEventListener('submit', function(event) {
    event.preventDefault();
    // Add form submission logic here
  });
});

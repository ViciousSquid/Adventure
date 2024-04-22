import { addRoom, reattachEventHandlers } from './storyEditor.js';
import { saveStoryAsJsonFile, loadStoryFromZip } from './storyIO.js';
import { handleLoadStoryClick, handleSaveStoryClick, handleAddRoomClick, handleFormSubmit, handleNewStoryClick } from './eventHandlers.js';

console.log("Editor > Init event listeners..");
document.addEventListener('DOMContentLoaded', function() {
  const summaryInput = document.createElement('textarea');
  summaryInput.id = 'summary';
  summaryInput.name = 'summary';
  summaryInput.placeholder = 'Summary (max 250 characters)';
  summaryInput.maxLength = 250;

  const storyForm = document.getElementById('storyForm');
  const roomsHeading = document.querySelector('h2');
  storyForm.insertBefore(summaryInput, roomsHeading);

  const roomsContainer = document.getElementById('roomsContainer');
  const addRoomLink = document.getElementById('addRoomLink');
  addRoomLink.addEventListener('click', handleAddRoomClick);

  const loadStoryLink = document.getElementById('loadStoryLink');
  loadStoryLink.addEventListener('click', handleLoadStoryClick);

  const saveStoryLink = document.getElementById('saveStoryLink');
  saveStoryLink.addEventListener('click', handleSaveStoryClick);

  const newStoryLink = document.getElementById('newStoryLink');
  newStoryLink.addEventListener('click', handleNewStoryClick);

  storyForm.addEventListener('submit', handleFormSubmit);
});
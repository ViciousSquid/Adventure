import { addRoom, reattachEventHandlers, getStoryData, generateJsonFromEditorData } from './storyEditor.js';
import { saveStoryAsJsonFile, loadStoryFromZip } from './storyIO.js';

export function handleLoadStoryClick(event) {
  event.preventDefault();
  loadStoryFromZip();
  reattachEventHandlers();
}

export function handleSaveStoryClick(event) {
  event.preventDefault();
  const storyJson = getStoryData();
  saveStoryAsJsonFile(storyJson);
  reattachEventHandlers();
}

export function handleAddRoomClick(event) {
  event.preventDefault();
  addRoom();
}

export function handleFormSubmit(event) {
  event.preventDefault();
  // Add form submission logic here
}

export function handleNewStoryClick(event) {
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

  // Reattach event handlers for all buttons
  reattachEventHandlers();
}
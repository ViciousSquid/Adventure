const JSZip = window.JSZip;

document.getElementById('add-room').addEventListener('click', addRoom);
document.getElementById('save-story').addEventListener('click', saveStory);
document.getElementById('load-story-input').addEventListener('change', handleLoadStoryInputChange);
document.getElementById('load-story-button').addEventListener('click', handleLoadStoryButtonClick);
document.getElementById('load-story').addEventListener('click', loadStory);
document.getElementById('toggle-view').addEventListener('click', toggleView);
document.getElementById('new-story').addEventListener('click', createNewStory);

let roomCounter = 0;
let loadedStory = null;

function addRoom(event) {
  const roomContainer = document.getElementById('room-container');
  const roomDiv = document.createElement('div');
  roomDiv.classList.add('room');

  roomDiv.innerHTML = `
    <h3>Room ${roomCounter + 1}</h3>
    <label for="room-name-${roomCounter}">Room Name:</label>
    <input type="text" id="room-name-${roomCounter}" required>
<br>

    <label for="room-description-${roomCounter}">Description:</label>
<br>
    <textarea id="room-description-${roomCounter}" rows="10" cols="70" required></textarea>
<br>

    <label for="room-image-${roomCounter}">Room Image:</label>
    <input type="file" id="room-image-${roomCounter}" accept="image/*">

    <div class="room-thumbnail-container"></div>

    <div class="exits">
      <label for="exit-1-${roomCounter}">Exit 1:</label>
      <input class="exit-input" type="text" id="exit-1-${roomCounter}">
      <input class="exit-input" type="text" id="room-ref-1-${roomCounter}">
<br>
      <label for="exit-2-${roomCounter}">Exit 2:</label>
      <input class="exit-input" type="text" id="exit-2-${roomCounter}">
      <input class="exit-input" type="text" id="room-ref-2-${roomCounter}">
<br>
      <label for="exit-3-${roomCounter}">Exit 3:</label>
      <input class="exit-input" type="text" id="exit-3-${roomCounter}">
      <input class="exit-input" type="text" id="room-ref-3-${roomCounter}">
<br>
      <label for="exit-4-${roomCounter}">Exit 4:</label>
      <input class="exit-input" type="text" id="exit-4-${roomCounter}">
      <input class="exit-input" type="text" id="room-ref-4-${roomCounter}">
    </div>


    <button type="button" class="remove-room">Remove Room</button>
<br>
  `;

  roomContainer.appendChild(roomDiv);

  roomDiv.querySelector('.remove-room').addEventListener('click', removeRoom);

  roomCounter++;
}

function removeRoom(event) {
  const room = event.target.parentNode;
  room.parentNode.removeChild(room);
}

function saveStory() {
  console.log('saveStory function called');

  const storyName = document.getElementById('story-name').value;
  const startRoom = document.getElementById('start-room').value;
  const rooms = {};

  const roomContainer = document.getElementById('room-container');
  const roomElements = roomContainer.querySelectorAll('.room');

  roomElements.forEach((roomElement, index) => {
    const roomName = roomElement.querySelector(`#room-name-${index}`).value;
    const description = roomElement.querySelector(`#room-description-${index}`).value;
    const imageInput = roomElement.querySelector(`#room-image-${index}`);
    const exits = {};

    for (let i = 1; i <= 4; i++) {
      const exitName = roomElement.querySelector(`#exit-${i}-${index}`).value;
      const exitRef = roomElement.querySelector(`#room-ref-${i}-${index}`).value;

      if (exitName && exitRef) {
        exits[exitName] = exitRef;
      }
    }

    rooms[roomName] = {
      description,
      exits,
      image: imageInput.files[0] ? `room-${roomName}-image.${imageInput.files[0].name.split('.').pop()}` : null
    };
  });

  const story = {
    name: storyName,
    start_room: startRoom,
    rooms
  };

  console.log('Story object:', story);

  const formData = new FormData();
  formData.append('story', JSON.stringify(story));

  roomElements.forEach((roomElement, index) => {
    const imageInput = roomElement.querySelector(`#room-image-${index}`);
    if (imageInput.files[0]) {
      const roomName = roomElement.querySelector(`#room-name-${index}`).value;
      const imageFile = imageInput.files[0];
      formData.append(`room-${roomName}-image`, imageFile);
    }
  });

  fetch('/save_story', {
    method: 'POST',
    body: formData
  })
  .then(response => {
    if (response.ok) {
      // Story saved successfully, initiate the download
      return response.blob();
    } else {
      return response.json().then(data => {
        throw new Error(data.error || 'Error saving the story');
      });
    }
  })
  .then(blob => {
    // Create a temporary URL for the downloaded file
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${storyName}.zip`; // Set the download attribute
    document.body.appendChild(a); // Append to the document body
    a.click(); // Trigger the download
    document.body.removeChild(a); // Remove the anchor element
    window.URL.revokeObjectURL(url); // Revoke the temporary URL

    alert('Story was downloaded!');
    updateGraphView(story);
  })
  .catch(error => {
    console.error('Error:', error);
    alert(`An error occurred while saving the story: ${error.message}`);
  });
}

function handleLoadStoryInputChange(event) {
  document.getElementById('load-story').disabled = false;
}

function handleLoadStoryButtonClick(event) {
  document.getElementById('load-story-input').click();
}

function loadStory(event) {
  const input = document.getElementById('load-story-input');
  const file = input.files[0];

  if (!file) {
    return;
  }

  const reader = new FileReader();

  reader.onload = (e) => {
    const zip = new JSZip();
    const zipData = new Uint8Array(e.target.result);

    zip.loadAsync(zipData).then((loadedZip) => {
      loadedZip.file('story.json').async('string').then((jsonStory) => {
        const story = JSON.parse(jsonStory);
        loadStoryIntoEditor(story, loadedZip);
        loadedStory = story;
      });
    });
  };

  reader.readAsArrayBuffer(file);
}

function loadStoryIntoEditor(story, zip) {
  document.getElementById('story-name').value = story.name;
  document.getElementById('start-room').value = story.start_room;

  // Clear existing rooms
  const roomContainer = document.getElementById('room-container');
  roomContainer.innerHTML = '';
  roomCounter = 0;

  // Add rooms from the loaded story
  for (const roomName in story.rooms) {
    const room = story.rooms[roomName];
    addRoom();
    const roomElement = roomContainer.querySelector('.room:last-child');
    const roomIndex = roomCounter - 1;

    roomElement.querySelector(`#room-name-${roomIndex}`).value = roomName;
    roomElement.querySelector(`#room-description-${roomIndex}`).value = room.description;

    // Load the room image thumbnail
    const thumbnailContainer = roomElement.querySelector('.room-thumbnail-container');
    if (room.image) {
      zip.file(room.image).async('blob').then((imageBlob) => {
        const imageUrl = URL.createObjectURL(imageBlob);
        const thumbnailElement = document.createElement('img');
        thumbnailElement.src = imageUrl;
        thumbnailElement.classList.add('room-thumbnail');
        thumbnailContainer.appendChild(thumbnailElement);
      });
    }

    let exitIndex = 1;
    for (const exitName in room.exits) {
      const exitRef = room.exits[exitName];
      roomElement.querySelector(`#exit-${exitIndex}-${roomIndex}`).value = exitName;
      roomElement.querySelector(`#room-ref-${exitIndex}-${roomIndex}`).value = exitRef;
      exitIndex++;
    }
  }
}

function toggleView() {
  if (!loadedStory) {
    alert('Please load a story before opening the graph view.');
    return;
  }

  updateGraphView(loadedStory);
}

function createNewStory() {
  if (confirm('Are you sure you want to create a new story? All unsaved changes will be lost.')) {
    // Clear the form fields
    document.getElementById('story-name').value = '';
    document.getElementById('start-room').value = '';

    // Clear the room container
    const roomContainer = document.getElementById('room-container');
    roomContainer.innerHTML = '';

    // Reset the loaded story
    loadedStory = null;
    roomCounter = 0;
  }
}

function updateGraphView(story) {
  const storyData = {
    name: story.name,
    nodes: [],
    edges: []
  };

  for (const roomName in story.rooms) {
    storyData.nodes.push({ id: roomName, label: roomName });

    const room = story.rooms[roomName];
    for (const exitName in room.exits) {
      const exitRef = room.exits[exitName];
      storyData.edges.push({ from: roomName, to: exitRef, label: exitName });
    }
  }

  localStorage.setItem('storyData', JSON.stringify(storyData));
  window.open('graph.html', '_blank');
}
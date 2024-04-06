const JSZip = window.JSZip;

document.getElementById('story-name').addEventListener('input', function (event) {
  this.value = this.value.replace(/\s+/g, '_');
});

document.getElementById('add-room').addEventListener('click', addRoom);
document.getElementById('save-story').addEventListener('click', saveStory);
document.getElementById('load-story-input').addEventListener('change', handleLoadStoryInputChange);
document.getElementById('load-story-button').addEventListener('click', handleLoadStoryButtonClick);
document.getElementById('load-story').addEventListener('click', loadStory);
document.getElementById('toggle-view').addEventListener('click', toggleView);
document.getElementById('new-story').addEventListener('click', createNewStory);
document.getElementById('load-button').addEventListener('click', toggleLoadPopup);

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
    <button type="button" class="clear-image" data-room-index="${roomCounter}">Clear Image</button>

    <div class="room-thumbnail-container">
      <img id="room-thumbnail-${roomCounter}" class="room-thumbnail" src="" alt="" style="display: none; max-width: 128px; max-height: 128px;">
    </div>

    <div class="Choices">
      <label for="exit-1-${roomCounter}">Choice 1:</label>
      <input class="exit-input" type="text" id="exit-1-${roomCounter}">
      <input class="exit-input" type="text" id="room-ref-1-${roomCounter}" placeholder="Leads to">
<br>
      <label for="exit-2-${roomCounter}">Choice 2:</label>
      <input class="exit-input" type="text" id="exit-2-${roomCounter}">
      <input class="exit-input" type="text" id="room-ref-2-${roomCounter}" placeholder="Leads to">
<br>
      <label for="exit-3-${roomCounter}">Choice 3:</label>
      <input class="exit-input" type="text" id="exit-3-${roomCounter}">
      <input class="exit-input" type="text" id="room-ref-3-${roomCounter}" placeholder="Leads to">
<br>
      <label for="exit-4-${roomCounter}">Choice 4:</label>
      <input class="exit-input" type="text" id="exit-4-${roomCounter}">
      <input class="exit-input" type="text" id="room-ref-4-${roomCounter}" placeholder="Leads to">
    </div>


    <button type="button" class="remove-room">Remove Room</button>
<br>
  `;

  roomContainer.appendChild(roomDiv);

  roomDiv.querySelector(`#room-name-${roomCounter}`).addEventListener('input', function (event) {
    this.value = this.value.replace(/\s+/g, '_');
  });

  for (let i = 1; i <= 4; i++) {
    roomDiv.querySelector(`#exit-${i}-${roomCounter}`).addEventListener('input', function (event) {
      this.value = this.value.replace(/\s+/g, '_');
    });
  }

  roomDiv.querySelector('.remove-room').addEventListener('click', removeRoom);
  roomDiv.querySelector(`#room-image-${roomCounter}`).addEventListener('change', handleImageUpload);
  roomDiv.querySelector('.clear-image').addEventListener('click', handleClearImage);

  roomCounter++;

  updateGraphView(getStoryData());
}

function removeRoom(event) {
  const room = event.target.parentNode;
  room.parentNode.removeChild(room);

  updateGraphView(getStoryData());
}

function saveStory() {
  console.log('saveStory function called');

  const storyName = document.getElementById('story-name').value;
  const startRoom = document.getElementById('start-room').value;
  const roomContainer = document.getElementById('room-container');
  const roomElements = Array.from(roomContainer.querySelectorAll('.room')); // Convert NodeList to array

  if (storyName.trim() === '') {
    alert('SAVE ERROR: Story has no title');
    return;
  }

  if (roomElements.length === 0) {
    alert('SAVE ERROR: Story must have at least one room.');
    return;
  }

  const rooms = {};

  roomElements.forEach((roomElement, index) => {
    const roomName = roomElement.querySelector(`#room-name-${index}`).value.replace(/\s+/g, '_');
    const description = roomElement.querySelector(`#room-description-${index}`).value;
    const imageInput = roomElement.querySelector(`#room-image-${index}`);
    const exits = {};

    for (let i = 1; i <= 4; i++) {
      const exitName = roomElement.querySelector(`#exit-${i}-${index}`).value.replace(/\s+/g, '_');
      const exitRef = roomElement.querySelector(`#room-ref-${i}-${index}`).value;

      if (exitName && exitRef) {
        exits[exitName] = exitRef;
      }
    }

    let imageName = null;
    if (imageInput.files[0]) {
      const extension = imageInput.files[0].name.split('.').pop();
      imageName = `${generateRandomString()}.${extension}`;
    }

    rooms[roomName] = {
      description,
      exits,
      image: imageName
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

  const imageResizePromises = roomElements.map((roomElement, index) => {
    const imageInput = roomElement.querySelector(`#room-image-${index}`);
    if (imageInput.files[0]) {
      const roomName = roomElement.querySelector(`#room-name-${index}`).value.replace(/\s+/g, '_');
      const imageFile = imageInput.files[0];
      const imageName = rooms[roomName].image;

      return new Promise((resolve) => {
        const img = new Image();
        img.onload = function () {
          const canvas = document.createElement('canvas');
          const ctx = canvas.getContext('2d');

          let width = img.width;
          let height = img.height;

          if (width > 512 || height > 384) {
            const aspectRatio = width / height;
            if (width > 512) {
              width = 512;
              height = Math.round(width / aspectRatio);
            }
            if (height > 384) {
              height = 384;
              width = Math.round(height * aspectRatio);
            }
          }

          canvas.width = width;
          canvas.height = height;
          ctx.drawImage(img, 0, 0, width, height);

          canvas.toBlob((blob) => {
            const resizedImageFile = new File([blob], imageName, { type: imageFile.type });
            formData.append(`room-${imageName}`, resizedImageFile);
            resolve();
          }, imageFile.type);
        };
        img.src = URL.createObjectURL(imageFile);
      });
    } else {
      return Promise.resolve();
    }
  });

  Promise.all(imageResizePromises)
    .then(() => {
      return fetch('/save_story', {
        method: 'POST',
        body: formData
      });
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
    const thumbnailElement = roomElement.querySelector(`#room-thumbnail-${roomIndex}`);
    if (room.image) {
      zip.file(room.image).async('blob').then((imageBlob) => {
        const imageUrl = URL.createObjectURL(imageBlob);
        thumbnailElement.src = imageUrl;
        thumbnailElement.style.display = 'block';
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

  updateGraphView(story);
}

function toggleView() {
  if (!loadedStory) {
    alert('Flowchart requires a loaded story or at least one room to be created.');
    return;
  }

  // Open the graph view in a new window
  window.graphViewWindow = window.open('graph.html', '_blank');
  window.graphViewWindow.onload = function() {
    window.graphViewWindow.updateGraph(loadedStory);
  };
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

    updateGraphView(getStoryData());
  }
}

function getStoryData() {
  const storyName = document.getElementById('story-name').value;
  const startRoom = document.getElementById('start-room').value;
  const roomContainer = document.getElementById('room-container');
  const roomElements = Array.from(roomContainer.querySelectorAll('.room'));

  const rooms = {};

  roomElements.forEach((roomElement, index) => {
    const roomName = roomElement.querySelector(`#room-name-${index}`).value;
    const exits = {};

    for (let i = 1; i <= 4; i++) {
      const exitName = roomElement.querySelector(`#exit-${i}-${index}`).value;
      const exitRef = roomElement.querySelector(`#room-ref-${i}-${index}`).value;

      if (exitName && exitRef) {
        exits[exitName] = exitRef;
      }
    }

    rooms[roomName] = { exits };
  });

  return {
    name: storyName,
    start_room: startRoom,
    rooms
  };
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

  // Check if the graph view window is already open
  if (window.graphViewWindow && !window.graphViewWindow.closed) {
    window.graphViewWindow.updateGraph(storyData);
  }
}

function toggleLoadPopup() {
  const loadPopup = document.getElementById('load-popup');
  const loadButton = document.getElementById('load-button');

  if (loadPopup.style.display === 'none') {
    loadPopup.style.display = 'block';
    loadButton.textContent = 'Load ↑';
  } else {
    loadPopup.style.display = 'none';
    loadButton.textContent = 'Load ↓';
  }
}

function handleImageUpload(event) {
  const roomIndex = event.target.id.split('-')[2];
  const thumbnailElement = document.querySelector(`#room-thumbnail-${roomIndex}`);
  const file = event.target.files[0];

  if (file) {
    const reader = new FileReader();
    reader.onload = function (e) {
      thumbnailElement.src = e.target.result;
      thumbnailElement.style.display = 'block';
    };
    reader.readAsDataURL(file);
  } else {
    thumbnailElement.src = '';
    thumbnailElement.style.display = 'none';
  }
}

function handleClearImage(event) {
  const roomIndex = event.target.getAttribute('data-room-index');
  const imageInput = document.querySelector(`#room-image-${roomIndex}`);
  const thumbnailElement = document.querySelector(`#room-thumbnail-${roomIndex}`);
 
  imageInput.value = '';
  thumbnailElement.src = '';
  thumbnailElement.style.display = 'none';
}

function generateRandomString(length = 8) {
  const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let result = '';
  for (let i = 0; i < length; i++) {
    result += characters.charAt(Math.floor(Math.random() * characters.length));
  }
  return result;
}
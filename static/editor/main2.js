const storyForm = document.getElementById('storyForm');
const roomsContainer = document.getElementById('roomsContainer');

function addRoom() {
  const roomContainer = document.createElement('div');
  roomContainer.classList.add('room-container');

  const roomSidebar = document.createElement('div');
  roomSidebar.classList.add('room-sidebar');
  roomSidebar.textContent = 'Room';
  roomContainer.appendChild(roomSidebar);

  const roomContent = document.createElement('div');
  roomContent.classList.add('room-content');
  roomContainer.appendChild(roomContent);

  const roomNameInput = document.createElement('input');
  roomNameInput.type = 'text';
  roomNameInput.name = 'roomName[]';
  roomNameInput.placeholder = 'Room Name';
  roomContent.appendChild(roomNameInput);

  const roomDescriptionInput = document.createElement('textarea');
  roomDescriptionInput.name = 'roomDescription[]';
  roomDescriptionInput.placeholder = 'Room Description';
  roomContent.appendChild(roomDescriptionInput);

  const roomImageInput = document.createElement('input');
  roomImageInput.type = 'file';
  roomImageInput.name = 'roomImage[]';
  roomImageInput.accept = 'image/*';
  roomContent.appendChild(roomImageInput);

  const roomImagePreviewContainer = document.createElement('div');
  roomImagePreviewContainer.classList.add('room-image-preview');
  roomContent.appendChild(roomImagePreviewContainer);

  const roomButtons = document.createElement('div');
  roomButtons.classList.add('room-buttons');
  roomContent.appendChild(roomButtons);

  const exitContainer = document.createElement('div');
  exitContainer.classList.add('exit-container');

  const addExitButton = document.createElement('button');
  addExitButton.type = 'button';
  addExitButton.textContent = 'Add Exit';
  addExitButton.classList.add('add-exit');
  addExitButton.addEventListener('click', () => {
    const exitContainer = document.createElement('div');
    exitContainer.classList.add('exit-container');

    const exitNameInput = document.createElement('input');
    exitNameInput.type = 'text';
    exitNameInput.name = 'exitName[]';
    exitNameInput.placeholder = 'Exit Name';
    exitContainer.appendChild(exitNameInput);

    const exitDestinationInput = document.createElement('input');
    exitDestinationInput.type = 'text';
    exitDestinationInput.name = 'exitDestination[]';
    exitDestinationInput.placeholder = 'Exit Destination';
    exitContainer.appendChild(exitDestinationInput);

    const addSkillCheckButton = document.createElement('button');
    addSkillCheckButton.type = 'button';
    addSkillCheckButton.textContent = 'Add Skill Check';
    addSkillCheckButton.addEventListener('click', () => {
      const skillCheckContainer = document.createElement('div');
      skillCheckContainer.classList.add('skill-check-container');

      const skillCheckDiceTypeInput = document.createElement('input');
      skillCheckDiceTypeInput.type = 'text';
      skillCheckDiceTypeInput.name = 'skillCheckDiceType[]';
      skillCheckDiceTypeInput.placeholder = 'Skill Check Dice Type';
      skillCheckContainer.appendChild(skillCheckDiceTypeInput);

      const skillCheckTargetInput = document.createElement('input');
      skillCheckTargetInput.type = 'number';
      skillCheckTargetInput.name = 'skillCheckTarget[]';
      skillCheckTargetInput.placeholder = 'Skill Check Target';
      skillCheckContainer.appendChild(skillCheckTargetInput);

      const successDescriptionInput = document.createElement('textarea');
      successDescriptionInput.name = 'successDescription[]';
      successDescriptionInput.placeholder = 'Success Description';
      skillCheckContainer.appendChild(successDescriptionInput);

      const successRoomInput = document.createElement('input');
      successRoomInput.type = 'text';
      successRoomInput.name = 'successRoom[]';
      successRoomInput.placeholder = 'Success Room';
      skillCheckContainer.appendChild(successRoomInput);

      const failureDescriptionInput = document.createElement('textarea');
      failureDescriptionInput.name = 'failureDescription[]';
      failureDescriptionInput.placeholder = 'Failure Description';
      skillCheckContainer.appendChild(failureDescriptionInput);

      const failureRoomInput = document.createElement('input');
      failureRoomInput.type = 'text';
      failureRoomInput.name = 'failureRoom[]';
      failureRoomInput.placeholder = 'Failure Room';
      skillCheckContainer.appendChild(failureRoomInput);

      exitContainer.appendChild(skillCheckContainer);
    });

    exitContainer.appendChild(addSkillCheckButton);

    const removeExitButton = document.createElement('button');
    removeExitButton.type = 'button';
    removeExitButton.textContent = 'Remove Exit';
    removeExitButton.classList.add('remove-exit');
    removeExitButton.addEventListener('click', () => {
      const confirmRemove = window.confirm('Are you sure you want to remove this exit?');
      if (confirmRemove) {
        exitContainer.remove();
      }
    });

    exitContainer.appendChild(removeExitButton);
    exitsContainer.appendChild(exitContainer);
  });

  const removeRoomButton = document.createElement('button');
  removeRoomButton.type = 'button';
  removeRoomButton.textContent = 'Remove Room';
  removeRoomButton.classList.add('remove-room');
  removeRoomButton.addEventListener('click', () => {
    const confirmRemove = window.confirm('Are you sure you want to remove this room?');
    if (confirmRemove) {
      roomContainer.remove();
    }
  });
  roomButtons.appendChild(removeRoomButton);

  const exitsContainer = document.createElement('div');
  exitsContainer.classList.add('exits-container');
  exitsContainer.appendChild(exitContainer);
  roomContent.appendChild(exitsContainer);

  roomsContainer.appendChild(roomContainer);
}

// Add event listener to the form submission
storyForm.addEventListener('submit', (event) => {
  event.preventDefault();

  // Get the editor data
  const editorData = getStoryData();

  // Generate the JSON structure
  const storyJson = generateJsonFromEditorData(editorData);

  // Save the story as a JSON file
  saveStoryAsJsonFile(storyJson);
});

// Function to save the story as a JSON file
function saveStoryAsJsonFile(storyJson) {
  const storyName = document.getElementById('storyName').value || 'untitled_story';
  const storyFileName = `${storyName.replace(/\s+/g, '_')}.zip`;
  const summaryText = document.getElementById('summary').value;

  const zip = new JSZip();
  const jsonString = JSON.stringify(storyJson, null, 2);
  zip.file('story.json', jsonString);

  const roomContainers = document.querySelectorAll('.room-container');
  const imagePromises = Array.from(roomContainers).map((roomContainer, index) => {
    const roomImageInput = roomContainer.querySelector('input[name="roomImage[]"]');
    const roomImageFile = roomImageInput.files[0];
    if (roomImageFile) {
      const imageFileName = `room_${index + 1}.${roomImageFile.name.split('.').pop()}`;
      return zip.file(imageFileName, roomImageFile);
    }
    return Promise.resolve();
  });

  // Add the summary.txt file to the ZIP
  zip.file('summary.txt', summaryText);

  Promise.all(imagePromises)
    .then(() => zip.generateAsync({ type: 'blob' }))
    .then((blob) => {
      const downloadLink = document.createElement('a');
      downloadLink.href = URL.createObjectURL(blob);
      downloadLink.download = storyFileName;
      downloadLink.click();
      URL.revokeObjectURL(downloadLink.href);
    })
    .catch((error) => {
      console.error('Error saving story:', error);
    });
}

function populateEditorFields(storyData) {
  // Clear existing fields
  roomsContainer.innerHTML = '';

  // Populate top-level fields
  document.getElementById('storyName').value = storyData.name || '';
  document.getElementById('buttonColor').value = storyData.button_color || '#000000';
  document.getElementById('startRoom').value = storyData.start_room || '';

  // Populate rooms
  for (const [roomName, roomData] of Object.entries(storyData.rooms)) {
    addRoom();
    const roomContainer = roomsContainer.lastElementChild;
    roomContainer.querySelector('input[name="roomName[]"]').value = roomName;
    const roomSidebar = roomContainer.querySelector('.room-sidebar');
    roomSidebar.textContent = roomName.replace(/_/g, ' ');
    roomContainer.querySelector('textarea[name="roomDescription[]"]').value = roomData.description || '';

    // Display thumbnail if room has an image
    if (roomData.image) {
      const roomImagePreviewContainer = roomContainer.querySelector('.room-image-preview');
      const thumbnailElement = document.createElement('img');
      thumbnailElement.src = `data:image/jpeg;base64,${roomData.image}`;
      thumbnailElement.alt = 'Room Thumbnail';
      thumbnailElement.classList.add('room-thumbnail');
      roomImagePreviewContainer.innerHTML = '';
      roomImagePreviewContainer.appendChild(thumbnailElement);
    }

    // Populate exits
    for (const [exitName, exitData] of Object.entries(roomData.exits)) {
      const addExitButton = roomContainer.querySelector('.add-exit');
      addExitButton.click();
      const exitContainers = roomContainer.querySelectorAll('.exit-container');
      const exitContainer = exitContainers[exitContainers.length - 1];
      exitContainer.querySelector('input[name="exitName[]"]').value = exitName;

      if (typeof exitData === 'string') {
        exitContainer.querySelector('input[name="exitDestination[]"]').value = exitData;
      } else if (typeof exitData === 'object' && exitData.skill_check) {
        const addSkillCheckButton = exitContainer.querySelector('button');
        addSkillCheckButton.click();
        const skillCheckContainers = exitContainer.querySelectorAll('.skill-check-container');
        const skillCheckContainer = skillCheckContainers[skillCheckContainers.length - 1];
        skillCheckContainer.querySelector('input[name="skillCheckDiceType[]"]').value = exitData.skill_check.dice_type || '';
        skillCheckContainer.querySelector('input[name="skillCheckTarget[]"]').value = exitData.skill_check.target || '';
        skillCheckContainer.querySelector('textarea[name="successDescription[]"]').value = exitData.skill_check.success.description || '';
        skillCheckContainer.querySelector('input[name="successRoom[]"]').value = exitData.skill_check.success.room || '';
        skillCheckContainer.querySelector('textarea[name="failureDescription[]"]').value = exitData.skill_check.failure.description || '';
        skillCheckContainer.querySelector('input[name="failureRoom[]"]').value = exitData.skill_check.failure.room || '';
      }
    }
  }
}

// Function to load story from ZIP file
function loadStoryFromZip() {
  const fileInput = document.createElement('input');
  fileInput.type = 'file';
  fileInput.accept = '.zip';
  fileInput.addEventListener('change', (event) => {
    const file = event.target.files[0];
    if (file) {
      JSZip.loadAsync(file)
        .then((zip) => {
          return Promise.all([
            zip.file('story.json').async('string'),
            Promise.all(
              Object.keys(zip.files)
                .filter((fileName) => fileName !== 'story.json')
                .map((fileName) => zip.file(fileName).async('base64'))
            ),
            zip.file('summary.txt')?.async('string') || Promise.resolve(null), // Load summary.txt if it exists
          ]);
        })
        .then(([jsonString, imageData, summaryText]) => {
          const storyData = JSON.parse(jsonString);
          Object.entries(storyData.rooms).forEach(([roomName, roomData], index) => {
            if (roomData.image) {
              const imageFileName = `room_${index + 1}.${roomData.image.split('.').pop()}`;
              const imageIndex = Object.keys(zip.files).indexOf(imageFileName);
              if (imageIndex !== -1) {
                roomData.image = imageData[imageIndex];
              }
            }
          });
          populateEditorFields(storyData);

          // Set the summary field value
          const summaryInput = document.getElementById('summary');
          if (summaryInput) {
            summaryInput.value = summaryText || '';
          }

          // Reattach event listener for save button
          const saveStoryButton = document.getElementById('saveStoryButton');
          saveStoryButton.addEventListener('click', () => {
            const editorData = getStoryData();
            const storyJson = generateJsonFromEditorData(editorData);
            saveStoryAsJsonFile(storyJson);
          });
        })
        .catch((error) => {
          console.error('Error loading story:', error);
        });
    }
  });
  fileInput.click();
}

// Utility functions
function replaceSpacesWithUnderscores(string) {
  return string.replace(/\s/g, '_');
}

function getStoryData() {
  const storyName = document.getElementById('storyName').value;
  const buttonColor = document.getElementById('buttonColor').value;
  const startRoom = document.getElementById('startRoom').value;
  const roomContainers = Array.from(document.querySelectorAll('.room-container'));

  const rooms = {};

  roomContainers.forEach((roomContainer) => {
    const roomNameInput = roomContainer.querySelector('input[name="roomName[]"]');
    const roomName = roomNameInput ? roomNameInput.value : '';

    const roomDescriptionInput = roomContainer.querySelector('textarea[name="roomDescription[]"]');
    const roomDescription = roomDescriptionInput ? roomDescriptionInput.value : '';

    const roomImageInput = roomContainer.querySelector('input[name="roomImage[]"]');
    const roomImageFile = roomImageInput && roomImageInput.files[0] ? roomImageInput.files[0] : null;

    const exits = {};

    const exitContainers = roomContainer.querySelectorAll('.exit-container');
    exitContainers.forEach((exitContainer) => {
      const exitNameInput = exitContainer.querySelector('input[name="exitName[]"]');
      const exitName = exitNameInput ? exitNameInput.value : '';

      const exitDestinationInput = exitContainer.querySelector('input[name="exitDestination[]"]');
      const exitDestination = exitDestinationInput ? exitDestinationInput.value : '';

      const skillCheckContainer = exitContainer.querySelector('.skill-check-container');
      if (skillCheckContainer) {
        const skillCheckDiceTypeInput = skillCheckContainer.querySelector('input[name="skillCheckDiceType[]"]');
        const diceType = skillCheckDiceTypeInput ? skillCheckDiceTypeInput.value : '';

        const skillCheckTargetInput = skillCheckContainer.querySelector('input[name="skillCheckTarget[]"]');
        const target = skillCheckTargetInput ? parseInt(skillCheckTargetInput.value) : 0;

        const successDescriptionInput = skillCheckContainer.querySelector('textarea[name="successDescription[]"]');
        const successDescription = successDescriptionInput ? successDescriptionInput.value : '';

        const successRoomInput = skillCheckContainer.querySelector('input[name="successRoom[]"]');
        const successRoom = successRoomInput ? successRoomInput.value : '';

        const failureDescriptionInput = skillCheckContainer.querySelector('textarea[name="failureDescription[]"]');
        const failureDescription = failureDescriptionInput ? failureDescriptionInput.value : '';

        const failureRoomInput = skillCheckContainer.querySelector('input[name="failureRoom[]"]');
        const failureRoom = failureRoomInput ? failureRoomInput.value : '';

        const skillCheckData = {
          dice_type: diceType,
          target: target,
          success: {
            description: successDescription,
            room: successRoom
          },
          failure: {
            description: failureDescription,
            room: failureRoom
          }
        };
        exits[exitName] = { skill_check: skillCheckData };
      } else if (exitDestination) {
        exits[exitName] = exitDestination;
      } else {
        exits[exitName] = null;
      }
    });

    rooms[roomName] = {
      description: roomDescription,
      exits: exits,
      image: roomImageFile ? roomImageFile.name : null
    };
  });

  return {
    name: storyName,
    button_color: buttonColor,
    start_room: startRoom,
    rooms: rooms
  };
}

function generateJsonFromEditorData(editorData) {
  const jsonData = {};

  // Add top-level keys
  for (const key of ["name", "button_color", "start_room"]) {
    if (key in editorData) {
      jsonData[key] = editorData[key];
    } else {
      jsonData[key] = "";
    }
  }

  // Add rooms
  jsonData["rooms"] = {};
  if ("rooms" in editorData) {
    for (const [roomName, roomData] of Object.entries(editorData["rooms"])) {
      const roomJson = {};

      // Add room description
      if ("description" in roomData) {
        roomJson["description"] = roomData["description"];
      } else {
        roomJson["description"] = "";
      }

      // Add room exits
      roomJson["exits"] = {};
      if ("exits" in roomData) {
        for (const [exitName, exitData] of Object.entries(roomData["exits"])) {
          if (typeof exitData === "string") {
            roomJson["exits"][exitName] = exitData;
          } else {
            roomJson["exits"][exitName] = {
              "skill_check": {
                "dice_type": exitData["skill_check"]["dice_type"],
                "target": exitData["skill_check"]["target"],
                "success": {
                  "description": exitData["skill_check"]["success"]["description"],
                  "room": exitData["skill_check"]["success"]["room"]
                },
                "failure": {
                  "description": exitData["skill_check"]["failure"]["description"],
                  "room": exitData["skill_check"]["failure"]["room"]
                }
              }
            };
          }
        }
      }

      jsonData["rooms"][roomName] = roomJson;
    }
  }

  return jsonData;
}

function updateMode(isLightMode) {
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

document.addEventListener('DOMContentLoaded', function() {
  const summaryInput = document.createElement('textarea');
  summaryInput.id = 'summary';
  summaryInput.name = 'summary';
  summaryInput.placeholder = 'Summary (max 250 characters)';
  summaryInput.maxLength = 250;

  const storyForm = document.getElementById('storyForm');
  const roomsHeading = document.querySelector('h2'); // Select the first <h2> element
  storyForm.insertBefore(summaryInput, roomsHeading); // Insert the summary input before the <h2> element

  // Add event listener to the "Flowchart" button
  const flowchartButton = document.getElementById('flowchartButton');
  flowchartButton.addEventListener('click', showFlowchart);

  function showFlowchart() {
    const storyData = getStoryData();
    const flowchartHTML = generateFlowchartHTML(storyData);
    const encodedFlowchartHTML = encodeURIComponent(flowchartHTML);
    const flowchartUrl = `flowchart.html#${encodedFlowchartHTML}`;
    window.open(flowchartUrl, 'Flowchart', 'width=800,height=600');
  }

  function generateFlowchartHTML(storyData) {
    let flowchartHTML = '';

    for (const [roomName, roomData] of Object.entries(storyData.rooms)) {
      flowchartHTML += `<div class="node">${roomName}</div>`;

      for (const [exitName, exitData] of Object.entries(roomData.exits)) {
        if (typeof exitData === 'string') {
          flowchartHTML += `<div class="node">${exitData}</div>`;
          flowchartHTML += `<svg><path class="edge" d="M0,0 L100,0" /></svg>`;
        } else if (typeof exitData === 'object' && exitData.skill_check) {
          const skillCheckData = exitData.skill_check;
          flowchartHTML += `<div class="node skill-check">${exitName}<br>${skillCheckData.dice_type} vs ${skillCheckData.target}</div>`;
          flowchartHTML += `<div class="node">${skillCheckData.success.room}</div>`;
          flowchartHTML += `<div class="node">${skillCheckData.failure.room}</div>`;
          flowchartHTML += `<svg><path class="edge" d="M0,0 L100,0" /><path class="edge" d="M0,0 L100,50" /><path class="edge" d="M0,0 L100,-50" /></svg>`;
        }
      }
    }

    return flowchartHTML;
  }
});

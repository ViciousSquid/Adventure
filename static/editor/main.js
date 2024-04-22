const storyForm = document.getElementById('storyForm');
const roomsContainer = document.getElementById('roomsContainer');
const addRoomLink = document.getElementById('addRoomLink');
const loadStoryLink = document.getElementById('loadStoryLink');
const saveStoryLink = document.getElementById('saveStoryLink');

// Add event listener to the add room link
addRoomLink.addEventListener('click', function (event) {
  event.preventDefault();
  addRoom();
});

// Add event listener to the load story link
loadStoryLink.addEventListener('click', function (event) {
  event.preventDefault();
  loadStoryFromZip();
});

// Add event listener to the save story link
saveStoryLink.addEventListener('click', function (event) {
  event.preventDefault();
  const editorData = getStoryData();
  const storyJson = generateJsonFromEditorData(editorData);
  saveStoryAsJsonFile(storyJson);
});

function addRoom() {
  const roomContainer = document.createElement('div');
  roomContainer.classList.add('room-container');

  const roomSidebar = document.createElement('div');
  roomSidebar.classList.add('room-sidebar');
  roomContainer.appendChild(roomSidebar);

  const roomContent = document.createElement('div');
  roomContent.classList.add('room-content');
  roomContainer.appendChild(roomContent);

  const roomNameInput = document.createElement('input');
  roomNameInput.type = 'text';
  roomNameInput.name = 'roomName[]';
  roomNameInput.placeholder = 'Room Name';
  roomNameInput.maxLength = 25;
  roomNameInput.addEventListener('input', function () {
    const roomIndex = Array.from(roomsContainer.children).indexOf(roomContainer) + 1;
    roomNameInput.value = replaceSpacesWithUnderscores(roomNameInput.value);
    const roomNameWithSpaces = roomNameInput.value.replace(/_/g, ' ');
    roomSidebar.textContent = roomNameWithSpaces ? roomNameWithSpaces : `Room ${roomIndex}`;

    const lineHeight = parseInt(window.getComputedStyle(roomSidebar).lineHeight);
    const numLines = Math.ceil(roomSidebar.textContent.length / 14);
    const newHeight = numLines * lineHeight + 20; // Add 20px for padding

    roomSidebar.style.height = `${newHeight}px`;
    roomContainer.style.minHeight = `${newHeight}px`;
  });
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

  roomImageInput.addEventListener('change', function (event) {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = function () {
        const imagePreview = new Image();
        imagePreview.onload = function () {
          const canvas = document.createElement('canvas');
          const ctx = canvas.getContext('2d');

          // Calculate the aspect ratio of the original image
          const aspectRatio = imagePreview.width / imagePreview.height;

          // Calculate the dimensions of the thumbnail while maintaining the aspect ratio
          let thumbnailWidth, thumbnailHeight;
          if (aspectRatio > 1) {
            thumbnailWidth = 100;
            thumbnailHeight = 100 / aspectRatio;
          } else {
            thumbnailWidth = 100 * aspectRatio;
            thumbnailHeight = 100;
          }

          // Set the canvas dimensions to the thumbnail size
          canvas.width = 100;
          canvas.height = 100;

          // Draw the resized image on the canvas
          ctx.drawImage(
            imagePreview,
            0,
            0,
            imagePreview.width,
            imagePreview.height,
            0,
            0,
            thumbnailWidth,
            thumbnailHeight
          );

          // Create a new image element and set its source to the thumbnail data URL
          const thumbnailImage = new Image();
          thumbnailImage.src = canvas.toDataURL();

          // Add the thumbnail image to the preview container
          roomImagePreviewContainer.innerHTML = '';
          roomImagePreviewContainer.appendChild(thumbnailImage);
        };
        imagePreview.src = reader.result;
      };
      reader.readAsDataURL(file);
    } else {
      roomImagePreviewContainer.innerHTML = '';
    }
  });

  const roomButtons = document.createElement('div');
  roomButtons.classList.add('room-buttons');
  roomContent.appendChild(roomButtons);

  const clearImageLink = document.createElement('a');
  clearImageLink.href = '#';
  clearImageLink.textContent = 'Clear Image';
  clearImageLink.classList.add('button', 'clear-image');
  clearImageLink.addEventListener('click', function (event) {
    event.preventDefault();
    roomImageInput.value = '';
    roomImagePreviewContainer.innerHTML = '';
  });
  roomButtons.appendChild(clearImageLink);

  const addExitLink = document.createElement('a');
  addExitLink.href = '#';
  addExitLink.textContent = 'Add Exit';
  addExitLink.classList.add('button', 'add-exit');
  roomButtons.appendChild(addExitLink);
  addExitLink.addEventListener('click', handleAddExitClick);

  const removeRoomLink = document.createElement('a');
  removeRoomLink.href = '#';
  removeRoomLink.textContent = 'Remove Room';
  removeRoomLink.classList.add('button', 'remove-room');
  roomButtons.appendChild(removeRoomLink);
  removeRoomLink.addEventListener('click', handleRemoveRoomClick);

  roomsContainer.appendChild(roomContainer);
}

function handleAddExitClick(event) {
  event.preventDefault();
  const roomContainer = event.target.closest('.room-container');
  addExit(roomContainer);
}

function handleRemoveRoomClick(event) {
  event.preventDefault();
  const roomContainer = event.target.closest('.room-container');
  const confirmRemove = window.confirm('Are you sure you want to remove this room?');
  if (confirmRemove) {
    roomContainer.remove();
  }
}

function handleAddSkillCheckClick(event) {
  event.preventDefault();
  const exitContainer = event.target.closest('.exit-container');
  addSkillCheck(exitContainer);
}

function handleRemoveExitClick(event) {
  event.preventDefault();
  const exitContainer = event.target.closest('.exit-container');
  const confirmRemove = window.confirm('Are you sure you want to remove this exit?');
  if (confirmRemove) {
    exitContainer.remove();
  }
}

function addExit(roomContainer) {
  const exitContainer = document.createElement('div');
  exitContainer.classList.add('exit-container');

  const exitNameInput = document.createElement('input');
  exitNameInput.type = 'text';
  exitNameInput.name = 'exitName[]';
  exitNameInput.placeholder = 'Exit Name';
  exitNameInput.maxLength = 20;
  exitNameInput.addEventListener('input', function () {
    exitNameInput.value = replaceSpacesWithUnderscores(exitNameInput.value);
  });
  exitContainer.appendChild(exitNameInput);

  const exitDestinationInput = document.createElement('input');
  exitDestinationInput.type = 'text';
  exitDestinationInput.name = 'exitDestination[]';
  exitDestinationInput.placeholder = 'Exit Destination';
  exitDestinationInput.maxLength = 20;
  exitDestinationInput.addEventListener('input', function () {
    exitDestinationInput.value = replaceSpacesWithUnderscores(exitDestinationInput.value);
  });
  exitContainer.appendChild(exitDestinationInput);

  const addSkillCheckLink = document.createElement('a');
  addSkillCheckLink.href = '#';
  addSkillCheckLink.textContent = 'Add Skill Check';
  addSkillCheckLink.classList.add('button', 'add-skill-check');
  addSkillCheckLink.addEventListener('click', handleAddSkillCheckClick);
  exitContainer.appendChild(addSkillCheckLink);

  const exitsContainer = document.createElement('div');
  exitsContainer.classList.add('exits-container');
  exitsContainer.appendChild(exitContainer);
  roomContainer.querySelector('.room-content').appendChild(exitsContainer);
}

function addSkillCheck(exitContainer) {
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

  const removeExitLink = document.createElement('a');
  removeExitLink.href = '#';
  removeExitLink.textContent = 'Remove Exit';
  removeExitLink.classList.add('button', 'remove-exit');
  removeExitLink.addEventListener('click', handleRemoveExitClick);
  skillCheckContainer.appendChild(removeExitLink);

  exitContainer.appendChild(skillCheckContainer);
}

// Function to save the story as a JSON file
function saveStoryAsJsonFile(storyJson) {
  const storyName = document.getElementById('storyName').value || 'untitled_story';
  const storyFileName = `${storyName.replace(/\s+/g, '_')}.zip`;
  const summaryText = document.getElementById('summary').value;

  const zip = new JSZip();
  const jsonString = JSON.stringify(storyJson, null, 2);
  zip.file('story.json', jsonString);

  
  const roomContainers = document.querySelectorAll('.room-container');
  const imagePromises = Array.from(roomContainers).map(function (roomContainer, index) {
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
    .then(function () {
      return zip.generateAsync({ type: 'blob' });
    })
    .then(function (blob) {
      const downloadLink = document.createElement('a');
      downloadLink.href = URL.createObjectURL(blob);
      downloadLink.download = storyFileName;
      downloadLink.click();
      URL.revokeObjectURL(downloadLink.href);
    })
    .catch(function (error) {
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
      addExit(roomContainer);
      const exitContainers = roomContainer.querySelectorAll('.exit-container');
      const exitContainer = exitContainers[exitContainers.length - 1];
      exitContainer.querySelector('input[name="exitName[]"]').value = exitName;

      if (typeof exitData === 'string') {
        exitContainer.querySelector('input[name="exitDestination[]"]').value = exitData;
      } else if (typeof exitData === 'object' && exitData.skill_check) {
        addSkillCheck(exitContainer);
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

  // Reattach event listeners after populating the fields
  const addExitLinks = document.querySelectorAll('.add-exit');
  addExitLinks.forEach(function (link) {
    link.addEventListener('click', handleAddExitClick);
  });

  const removeRoomLinks = document.querySelectorAll('.remove-room');
  removeRoomLinks.forEach(function (link) {
    link.addEventListener('click', handleRemoveRoomClick);
  });

  const addSkillCheckLinks = document.querySelectorAll('.add-skill-check');
  addSkillCheckLinks.forEach(function (link) {
    link.addEventListener('click', handleAddSkillCheckClick);
  });

  const removeExitLinks = document.querySelectorAll('.remove-exit');
  removeExitLinks.forEach(function (link) {
    link.addEventListener('click', handleRemoveExitClick);
  });

  // Reattach event listener for the "Add Room" button
  addRoomLink.addEventListener('click', function (event) {
    event.preventDefault();
    addRoom();
  });

  // Reattach event listener for the "Load Story" button
  loadStoryLink.addEventListener('click', function (event) {
    event.preventDefault();
    loadStoryFromZip();
  });

  // Reattach event listener for the "Save Story" button
  saveStoryLink.addEventListener('click', function (event) {
    event.preventDefault();
    const editorData = getStoryData();
    const storyJson = generateJsonFromEditorData(editorData);
    saveStoryAsJsonFile(storyJson);
  });

  // Enable the save link after populating the fields
  saveStoryLink.classList.remove('disabled');

  // Set the summary field value
  const summaryInput = document.getElementById('summary');
  if (summaryInput) {
    summaryInput.value = storyData.summary || '';
  }
}

// Function to load story from ZIP file
function loadStoryFromZip() {
  const fileInput = document.createElement('input');
  fileInput.type = 'file';
  fileInput.accept = '.zip';
  fileInput.addEventListener('change', async function (event) {
    const file = event.target.files[0];
    if (file) {
      JSZip.loadAsync(file)
        .then(function (zip) {
          return Promise.all([
            zip.file('story.json').async('string'),
            Promise.all(
              Object.keys(zip.files)
                .filter(function (fileName) {
                  return fileName !== 'story.json';
                })
                .map(function (fileName) {
                  return zip.file(fileName).async('base64');
                })
            ),
            zip.file('summary.txt') ? zip.file('summary.txt').async('string') : Promise.resolve(null),
          ]);
        })
        .then(async function (results) {
          const jsonString = results[0];
          const imageData = results[1];
          const summaryText = results[2];
          const storyData = JSON.parse(jsonString);

          const coverImageFile = zip.file('cover.jpg');
          if (coverImageFile) {
            const coverImageData = await coverImageFile.async('base64');
            const coverImageSrc = `data:image/jpeg;base64,${coverImageData}`;
            const coverThumbnailImg = document.getElementById('cover-thumbnail');
            coverThumbnailImg.src = coverImageSrc;
          }

          Object.entries(storyData.rooms).forEach(function (entry, index) {
            const roomName = entry[0];
            const roomData = entry[1];
            if (roomData.image) {
              const imageFileName = `room_${index + 1}.${roomData.image.split('.').pop()}`;
              const imageIndex = Object.keys(zip.files).indexOf(imageFileName);
              if (imageIndex !== -1) {
                roomData.image = imageData[imageIndex];
              }
            }
          });
          storyData.summary = summaryText;
          populateEditorFields(storyData);
        })
        .catch(function (error) {
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
  const summary = document.getElementById('summary').value;

  const rooms = {};

  roomContainers.forEach(function (roomContainer) {
    const roomNameInput = roomContainer.querySelector('input[name="roomName[]"]');
    const roomName = roomNameInput ? roomNameInput.value : '';

    const roomDescriptionInput = roomContainer.querySelector('textarea[name="roomDescription[]"]');
    const roomDescription = roomDescriptionInput ? roomDescriptionInput.value : '';

    const roomImageInput = roomContainer.querySelector('input[name="roomImage[]"]');
    const roomImageFile = roomImageInput && roomImageInput.files[0] ? roomImageInput.files[0] : null;

    const exits = {};

    const exitContainers = roomContainer.querySelectorAll('.exit-container');
    exitContainers.forEach(function (exitContainer) {
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
    rooms: rooms,
    summary: summary
  };
}

function generateJsonFromEditorData(editorData) {
  const jsonData = {};

  // Add top-level keys
  for (const key of ["name", "button_color", "start_room", "summary"]) {
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

// const thumbnailContainer = document.createElement('div');
// thumbnailContainer.classList.add('cover-thumbnail-container');
// storyForm.appendChild(thumbnailContainer);

const coverThumbnailImg = document.getElementById('cover-thumbnail');
const coverImageSrc = coverThumbnailImg.src;

if (coverImageSrc && coverImageSrc !== 'NoImage.jpg' && coverImageSrc.startsWith('data:image/jpeg;base64,')) {
  const coverImageFile = coverImageSrc.split(',')[1];
  const coverImageBuffer = Buffer.from(coverImageFile, 'base64');
  zip.file('cover.jpg', coverImageBuffer);
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

  
});
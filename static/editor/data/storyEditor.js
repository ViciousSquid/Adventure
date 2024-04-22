export function addRoom() {
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

export function handleAddExitClick(event) {
  event.preventDefault();
  const roomContainer = event.target.closest('.room-container');
  addExit(roomContainer);
}

export function handleRemoveRoomClick(event) {
  event.preventDefault();
  const roomContainer = event.target.closest('.room-container');
  const confirmRemove = window.confirm('Are you sure you want to remove this room?');
  if (confirmRemove) {
    roomContainer.remove();
  }
}

export function handleAddSkillCheckClick(event) {
  event.preventDefault();
  const exitContainer = event.target.closest('.exit-container');
  addSkillCheck(exitContainer);
}

export function handleRemoveExitClick(event) {
  event.preventDefault();
  const exitContainer = event.target.closest('.exit-container');
  const confirmRemove = window.confirm('Are you sure you want to remove this exit?');
  if (confirmRemove) {
    exitContainer.remove();
  }
}

export function addExit(roomContainer) {
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

export function addSkillCheck(exitContainer) {
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

export function reattachEventHandlers() {
  const addRoomLinkElement = document.getElementById('addRoomLink');
  const loadStoryLinkElement = document.getElementById('loadStoryLink');
  const saveStoryLinkElement = document.getElementById('saveStoryLink');
  const flowchartLinkElement = document.getElementById('flowchartLink');
  const newStoryLinkElement = document.getElementById('newStoryLink');

  // Remove existing event listeners for all buttons
  addRoomLinkElement.removeEventListener('click', handleAddRoomClick);
  loadStoryLinkElement.removeEventListener('click', handleLoadStoryClick);
  saveStoryLinkElement.removeEventListener('click', handleSaveStoryClick);
  flowchartLinkElement.removeEventListener('click', showFlowchart);
  newStoryLinkElement.removeEventListener('click', handleNewStoryClick);

  // Reattach event handlers for all buttons
  addRoomLinkElement.addEventListener('click', handleAddRoomClick);
  loadStoryLinkElement.addEventListener('click', handleLoadStoryClick);
  saveStoryLinkElement.addEventListener('click', handleSaveStoryClick);
  flowchartLinkElement.addEventListener('click', showFlowchart);
  newStoryLinkElement.addEventListener('click', handleNewStoryClick);

  // Reattach event handlers for other buttons
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
}

export function getStoryData() {
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
        
        export function generateJsonFromEditorData(editorData) {
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
import { addRoom, addExit, addSkillCheck, reattachEventHandlers } from './storyEditor.js';

export function saveStoryAsJsonFile(storyJson) {
  const storyName = document.getElementById('storyName').value || 'untitled_story';
  const storyFileName = `${storyName.replace(/\s+/g, '_')}.zip`;
  const summaryText = document.getElementById('summary').value;
  const coverImageInput = document.getElementById('coverimageUpload');
  const coverImageFile = coverImageInput.files[0];

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

  // Add the cover image file to the ZIP
  if (coverImageFile) {
    zip.file('cover.jpg', coverImageFile);
  }

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
    .then(function () {
      reattachEventHandlers();
    })
    .catch(function (error) {
      console.error('Error saving story:', error);
    });
}

export function loadStoryFromZip() {
  const fileInput = document.createElement('input');
  fileInput.type = 'file';
  fileInput.accept = '.zip';
  fileInput.addEventListener('change', function (event) {
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
            zip.file('cover.jpg') ? zip.file('cover.jpg').async('base64') : Promise.resolve(null),
          ]);
        })
        .then(function (results) {
          const jsonString = results[0];
          const imageData = results[1];
          const summaryText = results[2];
          const coverImageData = results[3];
          const storyData = JSON.parse(jsonString);

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
          storyData.cover_thumbnail = coverImageData;
          populateEditorFields(storyData);
          reattachEventHandlers();
        })
        .catch(function (error) {
          console.error('Error loading story:', error);
        });
    }
  });
  fileInput.click();
}

export function populateEditorFields(storyData) {
  console.log("Attempting to extract and populate data from JSON", storyData);
  // Walk the story.json tree and populate the editor fields with the data

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
    const roomNameInput = roomContainer.querySelector('input[name="roomName[]"]');
    roomNameInput.value = roomName;

    // Trigger the 'input' event to update the sidebar text
    roomNameInput.dispatchEvent(new Event('input'));

    roomContainer.querySelector('textarea[name="roomDescription[]"]').value = roomData.description || '';

    // Display thumbnail if room has an image
    if (roomData.image) {
      const roomImagePreviewContainer = roomContainer.querySelector('.room-image-preview');
      const thumbnailElement = document.createElement('img');
      thumbnailElement.src = roomData.image;
      thumbnailElement.alt = 'Room Thumbnail';
      thumbnailElement.classList.add('room-thumbnail');
      roomImagePreviewContainer.innerHTML = '';
      roomImagePreviewContainer.appendChild(thumbnailElement);
    }

    // Populate exits
    for (const [exitName, exitData] of Object.entries(roomData.exits)) {
      addExit(roomContainer);
      const exitContainer = roomContainer.querySelector('.exit-container:last-child');
      exitContainer.querySelector('input[name="exitName[]"]').value = exitName;

      if (typeof exitData === 'string') {
        exitContainer.querySelector('input[name="exitDestination[]"]').value = exitData;
      } else if (typeof exitData === 'object' && exitData.skill_check) {
        addSkillCheck(exitContainer);
        const skillCheckContainer = exitContainer.querySelector('.skill-check-container:last-child');
        skillCheckContainer.querySelector('input[name="skillCheckDiceType[]"]').value = exitData.skill_check.dice_type || '';
        skillCheckContainer.querySelector('input[name="skillCheckTarget[]"]').value = exitData.skill_check.target || '';
        skillCheckContainer.querySelector('textarea[name="successDescription[]"]').value = exitData.skill_check.success.description || '';
        skillCheckContainer.querySelector('input[name="successRoom[]"]').value = exitData.skill_check.success.room || '';
        skillCheckContainer.querySelector('textarea[name="failureDescription[]"]').value = exitData.skill_check.failure.description || '';
        skillCheckContainer.querySelector('input[name="failureRoom[]"]').value = exitData.skill_check.failure.room || '';
      }
    }
  }

  // Display cover thumbnail if it exists
  if (storyData.cover_thumbnail) {
    const coverThumbnailImg = document.getElementById('cover-thumbnail');
    coverThumbnailImg.src = `data:image/jpeg;base64,${storyData.cover_thumbnail}`;
  }

  // Reattach event listeners after populating the fields
  reattachEventHandlers();
}
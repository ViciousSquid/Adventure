export function generateThumbnail(file, callback) {
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
  
          // Call the callback function with the thumbnail image
          callback(thumbnailImage);
        };
        imagePreview.src = reader.result;
      };
      reader.readAsDataURL(file);
    } else {
      callback(null);
    }
  }
  
  export function displayThumbnail(thumbnailImage, container) {
    container.innerHTML = '';
    container.appendChild(thumbnailImage);
  }
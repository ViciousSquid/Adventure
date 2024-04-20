// main2.js
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
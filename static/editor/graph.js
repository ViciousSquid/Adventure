let cy = null;
let actionStack = [];
let redoStack = [];

window.addEventListener('DOMContentLoaded', () => {
  console.log('Graph view loaded');
  const storyData = JSON.parse(localStorage.getItem('storyData'));
  console.log('Story data:', storyData);
  if (storyData) {
    displayGraphView(storyData);
  } else {
    alert('No story data found. Please load a story in the editor window.');
    window.close();
  }
});

function displayGraphView(storyData) {
  console.log('Displaying graph view');
  if (cy) {
    cy.destroy();
  }

  cy = cytoscape({
    container: document.getElementById('cy'),
    elements: {
      nodes: storyData.nodes.map(node => ({
        data: {
          id: node.id,
          label: node.label
        }
      })),
      edges: storyData.edges.map(edge => ({
        data: {
          source: edge.from,
          target: edge.to,
          label: edge.label
        }
      }))
    },
    layout: {
      name: 'breadthfirst'
    },
    style: [
      {
        selector: 'node',
        style: {
          'background-color': '#666',
          'label': 'data(label)'
        }
      },
      {
        selector: 'edge',
        style: {
          'curve-style': 'bezier',
          'target-arrow-shape': 'triangle',
          'label': 'data(label)'
        }
      }
    ]
  });

  // Add event listeners for undo and redo
  document.addEventListener('keydown', (event) => {
    if (event.ctrlKey && event.key === 'z') {
      undo();
    } else if (event.ctrlKey && event.key === 'y') {
      redo();
    }
  });

  function undo() {
    if (actionStack.length > 0) {
      const lastAction = actionStack.pop();
      if (lastAction.action === 'add') {
        lastAction.elements.forEach(element => cy.remove(element));
      } else if (lastAction.action === 'remove') {
        lastAction.elements.forEach(element => cy.add(element));
      }
      redoStack.push(lastAction);
      updateActionList();
    }
  }

  function redo() {
    if (redoStack.length > 0) {
      const lastAction = redoStack.pop();
      if (lastAction.action === 'add') {
        lastAction.elements.forEach(element => cy.add(element));
      } else if (lastAction.action === 'remove') {
        lastAction.elements.forEach(element => cy.remove(element));
      }
      actionStack.push(lastAction);
      updateActionList();
    }
  }

  function updateActionList() {
    const actionList = document.getElementById('action-list');
    actionList.innerHTML = '';

    actionStack.forEach((action, index) => {
      const listItem = document.createElement('li');
      listItem.textContent = `${action.action} ${action.elements.length} element(s)`;
      actionList.appendChild(listItem);
    });
  }
}
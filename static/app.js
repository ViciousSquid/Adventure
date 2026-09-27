import {GraphEditor} from "/editor-graph.js";

const $ = (id) => document.getElementById(id);

let currentWorld = null;
let currentState = null;
let currentPackage = null;
let graphEditor = null;

async function api(url, options = {}) {
  const response = await fetch(url, {
    headers: {"Content-Type": "application/json", ...(options.headers || {})},
    ...options,
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Request failed");
  return data;
}

function pretty(value) {
  return JSON.stringify(value, null, 2);
}

async function loadStories() {
  const data = await api("/api/stories");
  for (const select of [$("worldSelect"), $("editWorldSelect")]) {
    select.innerHTML = "";
    for (const story of data.stories) {
      const option = document.createElement("option");
      option.value = story.id;
      option.textContent = story.id + " (" + story.source_format + ")";
      select.appendChild(option);
    }
  }
}

async function startGame() {
  const world = $("worldSelect").value;
  if (!world) return;
  const data = await api("/api/game/new", {
    method: "POST",
    body: JSON.stringify({world}),
  });
  currentWorld = world;
  currentState = data.state;
  currentPackage = await api("/api/world/" + encodeURIComponent(world));
  renderGame(data.result);
}

async function step(action) {
  const data = await api("/api/game/step", {
    method: "POST",
    body: JSON.stringify({
      world: currentWorld,
      state: currentState,
      action,
    }),
  });
  currentState = data.state;
  renderGame(data.result);
}

async function roll() {
  const data = await api("/api/game/roll", {
    method: "POST",
    body: JSON.stringify({
      world: currentWorld,
      state: currentState,
    }),
  });
  currentState = data.state;
  renderGame(data.result);
}

function assetUrl(world, name) {
  const encoded = name.split("/").map(encodeURIComponent).join("/");
  return "/api/world/" + encodeURIComponent(world) + "/asset/" + encoded;
}

function renderGame(result) {
  const root = $("game");
  const room = currentPackage.story.rooms[currentState.current_room];
  root.innerHTML = "";

  const card = document.createElement("div");
  card.className = "card";

  const title = document.createElement("h2");
  title.textContent = room.name || currentState.current_room;
  card.appendChild(title);

  if (room.image) {
    const image = document.createElement("img");
    image.src = assetUrl(currentWorld, room.image);
    image.alt = "";
    image.style.maxWidth = "100%";
    image.style.maxHeight = "360px";
    card.appendChild(image);
  }

  const text = document.createElement("p");
  text.textContent = result.text;
  card.appendChild(text);

  if (result.awaiting_roll) {
    const rollButton = document.createElement("button");
    rollButton.textContent = "Roll dice";
    rollButton.onclick = roll;
    card.appendChild(rollButton);
  } else {
    const actions = document.createElement("div");
    actions.className = "actions";
    for (const choice of result.choices) {
      const button = document.createElement("button");
      button.className = "action";
      button.textContent = choice.label;
      button.onclick = () => step(choice.id);
      actions.appendChild(button);
    }
    card.appendChild(actions);
  }

  const items = currentPackage.inventory.room_items[currentState.current_room] || [];
  if (items.length) {
    const itemSection = document.createElement("div");
    itemSection.className = "card";
    itemSection.innerHTML = "<h3>Items here</h3>";
    const actions = document.createElement("div");
    actions.className = "inventory";
    for (const itemId of items) {
      if (currentState.collected_items.includes(itemId)) continue;
      const button = document.createElement("button");
      button.textContent =
        currentPackage.inventory.items[itemId]?.name || itemId;
      button.onclick = () => step("acquire:" + itemId);
      actions.appendChild(button);
    }
    itemSection.appendChild(actions);
    card.appendChild(itemSection);
  }

  const inventory = document.createElement("div");
  inventory.className = "card";
  inventory.innerHTML = "<h3>Inventory</h3>";
  const inventoryActions = document.createElement("div");
  inventoryActions.className = "inventory";
  for (const itemId of currentState.inventory) {
    const button = document.createElement("button");
    button.textContent =
      "Use " + (currentPackage.inventory.items[itemId]?.name || itemId);
    button.onclick = () => step("use:" + itemId);
    inventoryActions.appendChild(button);
  }
  inventory.appendChild(inventoryActions);
  card.appendChild(inventory);

  const history = document.createElement("pre");
  history.textContent =
    "Room: " +
    currentState.current_room +
    "\nHistory: " +
    JSON.stringify(currentState.action_history, null, 2);
  card.appendChild(history);

  root.appendChild(card);
}

function syncEditorText(packageData) {
  $("storyJson").value = pretty(packageData.story);
  $("checksJson").value = pretty(packageData.skill_checks);
  $("inventoryJson").value = pretty(packageData.inventory);
}

function showEditorStatus(message) {
  $("editStatus").textContent = message;
}

function ensureGraphEditor() {
  if (graphEditor) return graphEditor;
  if (!currentPackage) return null;
  graphEditor = new GraphEditor({
    mount: $("graphEditor"),
    packageData: currentPackage,
    onChange: (packageData) => {
      currentPackage = packageData;
      syncEditorText(packageData);
    },
    onStatus: showEditorStatus,
  });
  return graphEditor;
}

async function loadEditorWorld() {
  const world = $("editWorldSelect").value;
  if (!world) return;
  const data = await api("/api/world/" + encodeURIComponent(world));
  currentPackage = data;
  syncEditorText(data);
  if (graphEditor) graphEditor.setPackage(data);
  else ensureGraphEditor();
  showEditorStatus(
    "Loaded " +
      world +
      " (" +
      data.source_format +
      "). Saving creates or updates " +
      world +
      ".canonical.zip without modifying the legacy source."
  );
}

function newWorld() {
  const packageData = {
    world: "New_World",
    source_format: "canonical",
    story: {
      schema_version: 3,
      name: "New_World",
      start_room: "start",
      rooms: {
        start: {
          description: "A new world.",
          show_map: true,
        },
      },
      connections: {},
      revisits: {},
      metadata: {},
    },
    skill_checks: {
      schema_version: 1,
      skill_checks: {},
    },
    inventory: {
      schema_version: 1,
      items: {},
      room_items: {},
      room_requirements: {},
    },
  };
  currentPackage = packageData;
  syncEditorText(packageData);
  if (graphEditor) graphEditor.setPackage(packageData);
  else ensureGraphEditor();
  setEditorView(true);
  showEditorStatus("New canonical world.");
}

function parseEditor() {
  try {
    return {
      story: JSON.parse($("storyJson").value),
      skill_checks: JSON.parse($("checksJson").value),
      inventory: JSON.parse($("inventoryJson").value),
    };
  } catch (error) {
    throw new Error("Invalid editor JSON: " + error.message);
  }
}

function syncGraphFromData() {
  const parsed = parseEditor();
  currentPackage = {
    ...(currentPackage || {}),
    ...parsed,
  };
  if (graphEditor) graphEditor.setPackage(currentPackage);
  else ensureGraphEditor();
  showEditorStatus("Graph rebuilt from the Data view.");
}

function setEditorView(graph) {
  $("graphView").hidden = !graph;
  $("dataView").hidden = graph;
  $("graphViewTab").classList.toggle("active", graph);
  $("dataViewTab").classList.toggle("active", !graph);
  if (graph) {
    try {
      syncGraphFromData();
    } catch (error) {
      showEditorStatus(error.message);
      $("graphView").hidden = true;
      $("dataView").hidden = false;
      $("graphViewTab").classList.remove("active");
      $("dataViewTab").classList.add("active");
    }
  }
}

async function validateEditor() {
  const payload = parseEditor();
  const result = await api("/api/editor/validate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  showEditorStatus(result.valid ? "Canonical world is valid." : "Invalid.");
}

async function saveEditor() {
  const payload = parseEditor();
  const result = await api("/api/editor/save", {
    method: "POST",
    body: JSON.stringify({
      ...payload,
      preserve_from: currentPackage?.world || null,
    }),
  });
  currentPackage = {
    ...(currentPackage || {}),
    ...payload,
    world: payload.story.name,
    source_format: "canonical",
  };
  syncEditorText(currentPackage);
  if (graphEditor) graphEditor.setPackage(currentPackage);
  showEditorStatus(
    "Saved " +
      result.path +
      ". Legacy sources remain unchanged; canonical output is now authoritative."
  );
  await loadStories();
  $("editWorldSelect").value = payload.story.name;
}

function setTab(editing) {
  $("playPanel").hidden = editing;
  $("editPanel").hidden = !editing;
  $("playTab").classList.toggle("active", !editing);
  $("editTab").classList.toggle("active", editing);
  if (editing && currentPackage) {
    ensureGraphEditor();
  }
}

$("playTab").onclick = () => setTab(false);
$("editTab").onclick = () => setTab(true);
$("graphViewTab").onclick = () => setEditorView(true);
$("dataViewTab").onclick = () => setEditorView(false);
$("newGame").onclick = () => startGame().catch(showError);
$("newWorld").onclick = newWorld;
$("loadWorld").onclick = () => loadEditorWorld().catch(showError);
$("validateWorld").onclick = () => validateEditor().catch(showError);
$("saveWorld").onclick = () => saveEditor().catch(showError);

function showError(error) {
  const message = error instanceof Error ? error.message : String(error);
  showEditorStatus(message);
  $("game").textContent = message;
}

loadStories()
  .then(() => {
    if ($("worldSelect").options.length) startGame().catch(showError);
    else newWorld();
  })
  .catch(showError);

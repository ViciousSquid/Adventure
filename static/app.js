import {GraphEditor} from "/editor-graph.js";
import {sanitizeRichHtml} from "/rich-text-editor.js";

const $ = (id) => document.getElementById(id);

let currentWorld = null;
let currentState = null;
let currentPackage = null;
let graphEditor = null;
let editorAssets = {};

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

function pendingAssetPayload() {
  const result = {};
  for (const [name, record] of Object.entries(editorAssets)) {
    if (!record?.dataUrl) continue;
    const comma = record.dataUrl.indexOf(",");
    if (comma < 0) continue;
    result[name] = record.dataUrl.slice(comma + 1);
  }
  return result;
}

function resolveDescriptionHtml(html, world) {
  return sanitizeRichHtml(
    html,
    (asset) => assetUrl(world, asset)
  );
}

function roomNarrative(room) {
  if (room.description_html) {
    return resolveDescriptionHtml(room.description_html, currentWorld);
  }
  const article = document.createElement("p");
  article.textContent = room.description || "You are here.";
  return article.outerHTML;
}

function appendSectionTitle(parent, kicker, title) {
  const kickerEl = document.createElement("div");
  kickerEl.className = "section-kicker";
  kickerEl.textContent = kicker;
  parent.appendChild(kickerEl);

  const titleEl = document.createElement("h3");
  titleEl.textContent = title;
  parent.appendChild(titleEl);
}

function renderDiceResult(result) {
  const dice = result.dice_results?.[result.dice_results.length - 1];
  if (!dice) return null;

  const card = document.createElement("section");
  card.className = "skill-roll-card";

  const header = document.createElement("div");
  header.className = "skill-roll-header";

  const left = document.createElement("div");
  const kicker = document.createElement("div");
  kicker.className = "section-kicker";
  kicker.textContent = "SKILL CHECK";
  left.appendChild(kicker);

  const target = document.createElement("div");
  target.className = "skill-roll-target";
  target.textContent = dice.expression + (dice.target != null ? " · target " + dice.target : "");
  left.appendChild(target);
  header.appendChild(left);

  const resultTotal = document.createElement("div");
  resultTotal.className =
    "dice-total " + (dice.success ? "success" : "failure");
  resultTotal.textContent = String(dice.total);
  header.appendChild(resultTotal);
  card.appendChild(header);

  const stage = document.createElement("div");
  stage.className = "dice-stage";
  (dice.individual_rolls || []).forEach((value, index) => {
    const die = document.createElement("span");
    die.className = "die";
    die.style.animationDelay = (index * 45) + "ms";
    die.textContent = String(value);
    stage.appendChild(die);
  });

  if (dice.modifier) {
    const modifier = document.createElement("span");
    modifier.className = "choice-tag";
    modifier.textContent = (dice.modifier > 0 ? "+" : "") + dice.modifier + " modifier";
    stage.appendChild(modifier);
  }

  card.appendChild(stage);
  return card;
}

function renderInventory(parent) {
  const card = document.createElement("aside");
  card.className = "utility-card";

  appendSectionTitle(
    card,
    "INVENTORY",
    "What you carry"
  );

  const slots = document.createElement("div");
  slots.className = "slot-grid";

  const held = currentState.inventory || [];
  const slotCount = Math.max(8, held.length);
  for (let index = 0; index < slotCount; index += 1) {
    const slot = document.createElement("div");
    slot.className = "inventory-slot" + (held[index] ? " filled" : "");

    const number = document.createElement("span");
    number.className = "slot-index";
    number.textContent = String(index + 1).padStart(2, "0");
    slot.appendChild(number);

    if (held[index]) {
      const itemId = held[index];
      const item = currentPackage.inventory.items[itemId] || {};
      const button = document.createElement("button");
      button.type = "button";
      button.title = "Use " + (item.name || itemId);
      button.textContent = item.name || itemId;
      button.onclick = () => step("use:" + itemId).catch(showError);
      slot.appendChild(button);
    } else {
      const empty = document.createElement("span");
      empty.className = "utility-note";
      empty.textContent = "empty";
      slot.appendChild(empty);
    }

    slots.appendChild(slot);
  }

  card.appendChild(slots);

  const count = document.createElement("p");
  count.className = "utility-note";
  count.textContent = held.length + " item" + (held.length === 1 ? "" : "s") +
    " carried · click an item to use it";
  card.appendChild(count);

  const pending = currentState.pending_check;
  if (pending) {
    const check = currentPackage.skill_checks?.skill_checks?.[pending.skill_check_id];
    if (check) {
      const checkCard = document.createElement("section");
      checkCard.className = "skill-roll-card";
      checkCard.style.margin = "1rem 0 0";
      appendSectionTitle(checkCard, "PENDING CHECK", check.description || "Make the check");
      const target = document.createElement("p");
      target.className = "utility-note";
      target.textContent =
        (check.dice_type || "1d20") + " against " + (check.target ?? 10);
      checkCard.appendChild(target);

      const rollButton = document.createElement("button");
      rollButton.className = "roll-button";
      rollButton.type = "button";
      rollButton.textContent = "Roll " + (check.dice_type || "1d20");
      rollButton.onclick = () => roll().catch(showError);
      checkCard.appendChild(rollButton);
      card.appendChild(checkCard);
    }
  }

  return card;
}

function renderChoices(result) {
  const choiceArea = document.createElement("section");
  choiceArea.className = "choice-area";

  const heading = document.createElement("div");
  heading.className = "choice-heading";
  appendSectionTitle(choiceArea, "CHOOSE", "What do you do?");
  choiceArea.appendChild(heading);

  const list = document.createElement("div");
  list.className = "choice-list";

  for (const [index, choice] of result.choices.entries()) {
    const hasSkill = !!choice.skill_check;
    const requiredId = choice.requires_item;
    const required = requiredId
      ? currentPackage.inventory.items[requiredId]
      : null;
    const locked = !!requiredId && !(currentState.inventory || []).includes(requiredId);

    const button = document.createElement("button");
    button.type = "button";
    button.className =
      "choice-button" +
      (hasSkill ? " skill" : "") +
      (locked ? " locked" : "");
    button.title = locked
      ? "Requires " + (required?.name || requiredId)
      : hasSkill
        ? "Roll " + choice.skill_check.dice_type + " against " + choice.skill_check.target
        : "Choose this path";

    const mark = document.createElement("span");
    mark.className = "choice-mark";
    mark.textContent = hasSkill ? "✦" : String.fromCharCode(65 + (index % 26));
    button.appendChild(mark);

    const label = document.createElement("span");
    label.textContent = choice.label;
    button.appendChild(label);

    const meta = document.createElement("span");
    meta.className = "choice-meta";

    if (hasSkill) {
      const tag = document.createElement("span");
      tag.className = "choice-tag skill";
      tag.textContent =
        choice.skill_check.dice_type + " ≥ " + choice.skill_check.target;
      meta.appendChild(tag);
    }

    if (requiredId) {
      const tag = document.createElement("span");
      tag.className = "choice-tag locked";
      tag.textContent = locked
        ? "Needs " + (required?.name || requiredId)
        : "Uses " + (required?.name || requiredId);
      meta.appendChild(tag);
    }

    button.appendChild(meta);

    if (locked) {
      button.disabled = true;
    } else {
      button.onclick = () => step(choice.id).catch(showError);
    }
    list.appendChild(button);
  }

  if (!result.choices.length) {
    const end = document.createElement("p");
    end.className = "utility-note";
    end.textContent = "The story ends here.";
    list.appendChild(end);
  }

  choiceArea.appendChild(list);
  return choiceArea;
}

function renderGame(result) {
  const root = $("game");
  const room = currentPackage.story.rooms[currentState.current_room];
  root.innerHTML = "";

  const shell = document.createElement("div");
  shell.className = "game-shell";

  const column = document.createElement("div");
  column.className = "story-column";

  const storyCard = document.createElement("article");
  storyCard.className = "story-card";

  const hero = document.createElement("div");
  hero.className = "story-hero" + (room.image ? " has-image" : "");

  if (room.image) {
    const image = document.createElement("img");
    image.src = assetUrl(currentWorld, room.image);
    image.alt = "";
    image.loading = "eager";
    hero.appendChild(image);
  }

  const overlay = document.createElement("div");
  overlay.className = "story-hero-overlay";

  const kicker = document.createElement("div");
  kicker.className = "story-kicker";
  kicker.textContent = "ROOM";
  overlay.appendChild(kicker);

  const title = document.createElement("h2");
  title.className = "story-title";
  title.textContent = room.name || currentState.current_room;
  overlay.appendChild(title);

  hero.appendChild(overlay);
  storyCard.appendChild(hero);

  const body = document.createElement("div");
  body.className = "story-body";
  body.innerHTML = roomNarrative(room);
  storyCard.appendChild(body);

  const hadDice = Array.isArray(result.dice_results) && result.dice_results.length > 0;
  const isRoomText =
    !hadDice &&
    result.text &&
    result.text === (room.description || "");

  if (result.text && !isRoomText && !result.awaiting_roll) {
    const event = document.createElement("section");
    const dice = result.dice_results?.[0];
    event.className =
      "story-event " +
      (dice?.success === true ? "success" : dice?.success === false ? "failure" : "");

    const kicker = document.createElement("div");
    kicker.className = "section-kicker";
    kicker.textContent = dice
      ? (dice.success ? "CHECK PASSED" : "CHECK FAILED")
      : "STORY";
    event.appendChild(kicker);

    const text = document.createElement("p");
    text.textContent = result.text;
    event.appendChild(text);
    storyCard.appendChild(event);
  }

  if (result.awaiting_roll) {
    const pending = currentState.pending_check;
    const check = currentPackage.skill_checks?.skill_checks?.[pending?.skill_check_id];
    const card = document.createElement("section");
    card.className = "skill-roll-card";
    const heading = document.createElement("div");
    heading.className = "skill-roll-header";

    const copy = document.createElement("div");
    const kicker = document.createElement("div");
    kicker.className = "section-kicker";
    kicker.textContent = "SKILL CHECK";
    copy.appendChild(kicker);

    const title = document.createElement("strong");
    title.textContent = check?.description || "The path demands a roll.";
    copy.appendChild(title);
    heading.appendChild(copy);

    const meta = document.createElement("div");
    meta.className = "skill-roll-target";
    meta.textContent =
      (check?.dice_type || "1d20") + " ≥ " + (check?.target ?? 10);
    heading.appendChild(meta);
    card.appendChild(heading);

    const rollButton = document.createElement("button");
    rollButton.className = "roll-button";
    rollButton.type = "button";
    rollButton.textContent = "Roll dice";
    rollButton.onclick = () => roll().catch(showError);
    card.appendChild(rollButton);

    storyCard.appendChild(card);
  } else if (hadDice) {
    const diceCard = renderDiceResult(result);
    if (diceCard) storyCard.appendChild(diceCard);
  }

  storyCard.appendChild(renderChoices(result));
  column.appendChild(storyCard);

  const itemsHere = currentPackage.inventory.room_items[currentState.current_room] || [];
  const available = itemsHere.filter((itemId) =>
    !currentState.collected_items.includes(itemId) &&
    !currentState.inventory.includes(itemId)
  );

  if (available.length) {
    const findCard = document.createElement("section");
    findCard.className = "item-find-card";

    appendSectionTitle(findCard, "FOUND HERE", "Things you can take");

    const list = document.createElement("div");
    list.className = "item-find-list";

    available.forEach((itemId) => {
      const item = currentPackage.inventory.items[itemId] || {};
      const button = document.createElement("button");
      button.type = "button";
      button.className = "item-find";
      button.textContent = "＋ " + (item.name || itemId);
      button.onclick = () => step("acquire:" + itemId).catch(showError);
      list.appendChild(button);
    });

    findCard.appendChild(list);
    column.appendChild(findCard);
  }

  shell.appendChild(column);
  shell.appendChild(renderInventory(shell));
  root.appendChild(shell);
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
    assets: editorAssets,
    assetUrl: (name) => assetUrl(
      currentPackage?.world || currentPackage?.story?.name || "",
      name
    ),
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
  editorAssets = {};
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
  editorAssets = {};
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
      assets: pendingAssetPayload(),
      preserve_from: currentPackage?.world || null,
    }),
  });
  currentPackage = {
    ...(currentPackage || {}),
    ...payload,
    world: payload.story.name,
    source_format: "canonical",
  };
  editorAssets = {};
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

function updateFullscreenLabel() {
  const button = $("fullscreenEditor");
  if (!button) return;
  button.textContent =
    document.fullscreenElement === $("editPanel")
      ? "Exit Fullscreen"
      : "Fullscreen";
}

async function toggleFullscreen() {
  const panel = $("editPanel");
  if (document.fullscreenElement) {
    await document.exitFullscreen();
    updateFullscreenLabel();
    return;
  }
  if (!panel.requestFullscreen) {
    showEditorStatus("Fullscreen is not available in this browser.");
    return;
  }
  await panel.requestFullscreen();
  updateFullscreenLabel();
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
$("fullscreenEditor").onclick = () => toggleFullscreen().catch(showError);
document.addEventListener("fullscreenchange", updateFullscreenLabel);

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

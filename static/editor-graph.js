const esc = (value) => String(value ?? "")
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;");

const text = (value, fallback = "") =>
  value === undefined || value === null ? fallback : String(value);

const clone = (value) => JSON.parse(JSON.stringify(value));

export class GraphEditor {
  constructor({mount, packageData, onChange, onStatus}) {
    this.mount = mount;
    this.pkg = packageData;
    this.onChange = onChange;
    this.onStatus = onStatus;
    this.selected = "world";
    this.scale = 1;
    this.panX = 24;
    this.panY = 24;
    this.drag = null;
    this.pan = null;
    this.positions = this._positions();
    this._buildShell();
    this._bind();
    this.render();
  }

  setPackage(packageData) {
    this.pkg = packageData;
    this.positions = this._positions();
    if (!this._nodeExists(this.selected)) this.selected = "world";
    this.render();
  }

  _positions() {
    const metadata = this.pkg?.story?.metadata;
    const graph = metadata && typeof metadata === "object"
      ? metadata.__editor_graph
      : null;
    const nodes = graph && typeof graph.nodes === "object" ? graph.nodes : {};
    return clone(nodes);
  }

  _ensureMetadata() {
    if (!this.pkg.story.metadata || typeof this.pkg.story.metadata !== "object") {
      this.pkg.story.metadata = {};
    }
    if (
      !this.pkg.story.metadata.__editor_graph ||
      typeof this.pkg.story.metadata.__editor_graph !== "object"
    ) {
      this.pkg.story.metadata.__editor_graph = {nodes: {}};
    }
    if (
      !this.pkg.story.metadata.__editor_graph.nodes ||
      typeof this.pkg.story.metadata.__editor_graph.nodes !== "object"
    ) {
      this.pkg.story.metadata.__editor_graph.nodes = {};
    }
    this.pkg.story.metadata.__editor_graph.nodes = this.positions;
  }

  _buildShell() {
    this.mount.innerHTML = \`
      <div class="graph-toolbar">
        <button data-graph-action="add-room">+ Room</button>
        <button data-graph-action="add-skill">+ Skill Check</button>
        <button data-graph-action="add-item">+ Item</button>
        <button data-graph-action="add-revisit">+ Revisit</button>
        <span class="graph-toolbar-spacer"></span>
        <button data-graph-action="auto-layout">Auto Layout</button>
        <button data-graph-action="fit">Fit</button>
        <button data-graph-action="zoom-out">−</button>
        <button data-graph-action="zoom-reset">100%</button>
        <button data-graph-action="zoom-in">+</button>
      </div>
      <div class="graph-main">
        <div class="graph-stage" tabindex="0">
          <svg class="graph-edges" aria-hidden="true"></svg>
          <div class="graph-node-layer"></div>
          <div class="graph-help">
            Drag nodes. Drag empty space to pan. Use the wheel to zoom.
            Select a node to edit it. Delete removes the selected node.
          </div>
        </div>
        <aside class="graph-inspector"></aside>
      </div>
    \`;
    this.stage = this.mount.querySelector(".graph-stage");
    this.edges = this.mount.querySelector(".graph-edges");
    this.nodeLayer = this.mount.querySelector(".graph-node-layer");
    this.inspector = this.mount.querySelector(".graph-inspector");
  }

  _bind() {
    this.mount.addEventListener("click", (event) => {
      const action = event.target.closest("[data-graph-action]")?.dataset.graphAction;
      if (!action) return;
      this._action(action);
    });

    this.inspector.addEventListener("click", (event) => {
      const button = event.target.closest("[data-inspector-action]");
      if (!button) return;
      this._inspectorAction(button.dataset.inspectorAction, button.dataset);
    });

    this.inspector.addEventListener("change", (event) => {
      const field = event.target.closest("[data-field]");
      if (!field) return;
      this._fieldChanged(field);
    });

    this.stage.addEventListener("pointerdown", (event) => {
      if (event.target.closest(".graph-node")) return;
      this.pan = {
        pointerId: event.pointerId,
        x: event.clientX,
        y: event.clientY,
        panX: this.panX,
        panY: this.panY,
      };
      this.stage.setPointerCapture(event.pointerId);
      this.stage.classList.add("panning");
    });

    this.stage.addEventListener("pointermove", (event) => {
      if (!this.pan || event.pointerId !== this.pan.pointerId) return;
      this.panX = this.pan.panX + event.clientX - this.pan.x;
      this.panY = this.pan.panY + event.clientY - this.pan.y;
      this._applyViewport();
    });

    const endPan = (event) => {
      if (!this.pan || event.pointerId !== this.pan.pointerId) return;
      this.pan = null;
      this.stage.classList.remove("panning");
      this._persistPositions();
    };
    this.stage.addEventListener("pointerup", endPan);
    this.stage.addEventListener("pointercancel", endPan);

    this.stage.addEventListener(
      "wheel",
      (event) => {
        event.preventDefault();
        const rect = this.stage.getBoundingClientRect();
        const sx = event.clientX - rect.left;
        const sy = event.clientY - rect.top;
        const wx = (sx - this.panX) / this.scale;
        const wy = (sy - this.panY) / this.scale;
        const next = Math.max(
          0.35,
          Math.min(2.25, this.scale * (event.deltaY < 0 ? 1.1 : 0.9))
        );
        this.panX = sx - wx * next;
        this.panY = sy - wy * next;
        this.scale = next;
        this._applyViewport();
      },
      {passive: false}
    );

    window.addEventListener("keydown", (event) => {
      if (!this.mount.isConnected) return;
      const active = document.activeElement;
      if (
        active &&
        (active.tagName === "INPUT" ||
          active.tagName === "TEXTAREA" ||
          active.tagName === "SELECT")
      ) {
        return;
      }
      if (event.key === "Delete" && this.selected !== "world") {
        event.preventDefault();
        this._deleteSelected();
      }
      if (event.key === "0") this._fit();
    });

    window.addEventListener("resize", () => {
      if (this.mount.isConnected) this._renderEdges();
    });
  }

  render() {
    this._ensureMetadata();
    this._renderNodes();
    this._renderInspector();
    this._renderEdges();
    this._applyViewport();
  }

  _nodeExists(key) {
    if (key === "world") return true;
    const [type, id, extra] = key.split("::");
    if (type === "room") return !!this.pkg.story.rooms[id];
    if (type === "skill") return !!this.pkg.skill_checks.skill_checks[id];
    if (type === "item") return !!this.pkg.inventory.items[id];
    if (type === "revisit") {
      const index = Number(extra);
      return Array.isArray(this.pkg.story.revisits?.[id]?.entries)
        && !!this.pkg.story.revisits[id].entries[index];
    }
    return false;
  }

  _nodeData() {
    const nodes = [{
      key: "world",
      type: "world",
      title: this.pkg.story.name || "World",
      subtitle: "Narrative VM program",
    }];

    const rooms = this.pkg.story.rooms || {};
    for (const [id, room] of Object.entries(rooms)) {
      const label = room.name || id;
      const badges = [];
      if (id === this.pkg.story.start_room) badges.push("START");
      if (room.image) badges.push("IMAGE");
      if (this.pkg.inventory.room_items?.[id]?.length) badges.push("ITEMS");
      if (this.pkg.story.revisits?.[id]?.entries?.length) badges.push("REVISIT");
      nodes.push({
        key: \`room::\${id}\`,
        type: "room",
        id,
        title: label,
        subtitle: id,
        body: text(room.description, "No description").slice(0, 140),
        badges,
      });
    }

    for (const [id, check] of Object.entries(this.pkg.skill_checks.skill_checks || {})) {
      nodes.push({
        key: \`skill::\${id}\`,
        type: "skill",
        id,
        title: id,
        subtitle: \`\${check.dice_type || "1d20"} ≥ \${check.target ?? 10}\`,
        body: text(check.description || "Skill check").slice(0, 120),
      });
    }

    for (const [id, item] of Object.entries(this.pkg.inventory.items || {})) {
      const placed = Object.entries(this.pkg.inventory.room_items || {})
        .filter(([, ids]) => Array.isArray(ids) && ids.includes(id))
        .map(([room]) => room);
      const required = Object.entries(this.pkg.inventory.room_requirements || {})
        .filter(([, itemId]) => itemId === id)
        .map(([room]) => room);
      nodes.push({
        key: \`item::\${id}\`,
        type: "item",
        id,
        title: item.name || id,
        subtitle: id,
        body: [
          placed.length ? \`Found in: \${placed.join(", ")}\` : "",
          required.length ? \`Required by: \${required.join(", ")}\` : "",
        ].filter(Boolean).join(" · "),
      });
    }

    for (const [roomId, revisit] of Object.entries(this.pkg.story.revisits || {})) {
      const entries = Array.isArray(revisit.entries) ? revisit.entries : [];
      entries.forEach((entry, index) => {
        nodes.push({
          key: \`revisit::\${roomId}::\${index}\`,
          type: "revisit",
          id: roomId,
          index,
          title: \`Revisit \${entry.count ?? 0}+\`,
          subtitle: roomId,
          body: text(entry.content, "").slice(0, 120),
        });
      });
    }

    return nodes;
  }

  _positionFor(node, index) {
    let pos = this.positions[node.key];
    if (
      !pos ||
      !Number.isFinite(pos.x) ||
      !Number.isFinite(pos.y)
    ) {
      const columns = 4;
      const col = index % columns;
      const row = Math.floor(index / columns);
      const base = {
        world: {x: 60, y: 60},
        room: {x: 60, y: 230},
        skill: {x: 390, y: 230},
        item: {x: 720, y: 230},
        revisit: {x: 1050, y: 230},
      }[node.type] || {x: 60, y: 230};
      pos = {
        x: base.x + col * 250,
        y: base.y + row * 175,
      };
      this.positions[node.key] = pos;
    }
    return pos;
  }

  _renderNodes() {
    this.nodeLayer.innerHTML = "";
    const nodes = this._nodeData();
    nodes.forEach((node, index) => {
      const pos = this._positionFor(node, index);
      const el = document.createElement("article");
      el.className = \`graph-node node-\${node.type}\${node.key === this.selected ? " selected" : ""}\`;
      el.dataset.nodeKey = node.key;
      el.style.left = \`\${pos.x}px\`;
      el.style.top = \`\${pos.y}px\`;
      el.innerHTML = \`
        <div class="graph-node-header">
          <span class="node-kind">\${esc(node.type)}</span>
          <strong>\${esc(node.title)}</strong>
        </div>
        <div class="graph-node-subtitle">\${esc(node.subtitle)}</div>
        \${node.body ? \`<div class="graph-node-body">\${esc(node.body)}</div>\` : ""}
        \${node.badges?.length ? \`
          <div class="graph-badges">
            \${node.badges.map((badge) => \`<span>\${esc(badge)}</span>\`).join("")}
          </div>
        \` : ""}
      \`;
      el.addEventListener("click", (event) => {
        event.stopPropagation();
        this.selected = node.key;
        this._renderNodes();
        this._renderInspector();
        this._renderEdges();
      });
      el.addEventListener("pointerdown", (event) => {
        event.stopPropagation();
        if (event.button !== 0) return;
        const current = this.positions[node.key];
        this.drag = {
          pointerId: event.pointerId,
          key: node.key,
          x: event.clientX,
          y: event.clientY,
          startX: current.x,
          startY: current.y,
        };
        el.setPointerCapture(event.pointerId);
        el.classList.add("dragging");
      });
      el.addEventListener("pointermove", (event) => {
        if (!this.drag || event.pointerId !== this.drag.pointerId) return;
        const dx = (event.clientX - this.drag.x) / this.scale;
        const dy = (event.clientY - this.drag.y) / this.scale;
        this.positions[this.drag.key] = {
          x: Math.max(0, this.drag.startX + dx),
          y: Math.max(0, this.drag.startY + dy),
        };
        el.style.left = \`\${this.positions[this.drag.key].x}px\`;
        el.style.top = \`\${this.positions[this.drag.key].y}px\`;
        this._renderEdges();
      });
      const endDrag = (event) => {
        if (!this.drag || event.pointerId !== this.drag.pointerId) return;
        this.drag = null;
        el.classList.remove("dragging");
        this._persistPositions();
      };
      el.addEventListener("pointerup", endDrag);
      el.addEventListener("pointercancel", endDrag);
      this.nodeLayer.appendChild(el);
    });
  }

  _applyViewport() {
    const transform = \`translate(\${this.panX}px, \${this.panY}px) scale(\${this.scale})\`;
    this.nodeLayer.style.transform = transform;
    this.edges.style.transform = transform;
    const zoomButton = this.mount.querySelector('[data-graph-action="zoom-reset"]');
    if (zoomButton) zoomButton.textContent = \`\${Math.round(this.scale * 100)}%\`;
    this._renderEdges();
  }

  _renderEdges() {
    if (!this.edges) return;
    const width = this.stage.clientWidth;
    const height = this.stage.clientHeight;
    this.edges.setAttribute("width", width);
    this.edges.setAttribute("height", height);
    this.edges.setAttribute("viewBox", \`0 0 \${Math.max(width, 1)} \${Math.max(height, 1)}\`);
    const ns = "http://www.w3.org/2000/svg";
    this.edges.innerHTML = \`
      <defs>
        <marker id="graph-arrow" markerWidth="10" markerHeight="10"
          refX="9" refY="5" orient="auto" markerUnits="strokeWidth">
          <path d="M0,0 L10,5 L0,10 z"></path>
        </marker>
      </defs>
    \`;

    const nodeMap = new Map(
      [...this.nodeLayer.children].map((el) => [el.dataset.nodeKey, el])
    );
    const edgeList = this._edgeData();
    for (const edge of edgeList) {
      const sourceEl = nodeMap.get(edge.from);
      const targetEl = nodeMap.get(edge.to);
      if (!sourceEl || !targetEl) continue;

      const a = this._anchor(sourceEl, "out");
      const b = this._anchor(targetEl, "in");
      const same = edge.from === edge.to;
      let pathData;
      if (same) {
        pathData = \`M \${a.x} \${a.y} C \${a.x + 90} \${a.y - 85}, \${b.x + 90} \${b.y - 85}, \${b.x} \${b.y}\`;
      } else {
        const bend = Math.max(70, Math.abs(b.x - a.x) * 0.45);
        pathData = \`M \${a.x} \${a.y} C \${a.x + bend} \${a.y}, \${b.x - bend} \${b.y}, \${b.x} \${b.y}\`;
      }
      const path = document.createElementNS(ns, "path");
      path.setAttribute("d", pathData);
      path.setAttribute("class", \`graph-edge graph-edge-\${edge.kind}\`);
      if (edge.selected) path.classList.add("selected");
      path.setAttribute("marker-end", "url(#graph-arrow)");
      this.edges.appendChild(path);

      if (edge.label) {
        const label = document.createElementNS(ns, "text");
        const lx = (a.x + b.x) / 2;
        const ly = (a.y + b.y) / 2 - 7;
        label.setAttribute("x", lx);
        label.setAttribute("y", ly);
        label.setAttribute("class", "graph-edge-label");
        label.textContent = edge.label;
        this.edges.appendChild(label);
      }
    }
  }

  _anchor(el, side) {
    const pos = this.positions[el.dataset.nodeKey] || {x: 0, y: 0};
    const width = el.offsetWidth || 220;
    const height = el.offsetHeight || 100;
    return {
      x: pos.x + (side === "out" ? width : 0),
      y: pos.y + height / 2,
    };
  }

  _edgeData() {
    const edges = [];
    const selected = this.selected;
    const rooms = this.pkg.story.rooms || {};
    for (const [connectionId, connection] of Object.entries(this.pkg.story.connections || {})) {
      const from = \`room::\${connection.from}\`;
      const requirement = connection.requires_item
        ? \` · needs \${this.pkg.inventory.items?.[connection.requires_item]?.name || connection.requires_item}\`
        : "";
      if (connection.skill_check) {
        const skill = \`skill::\${connection.skill_check}\`;
        edges.push({
          from,
          to: skill,
          kind: "skill-link",
          label: \`\${connection.label || connectionId}\${requirement}\`,
          selected: selected === from || selected === skill,
        });
      } else {
        edges.push({
          from,
          to: \`room::\${connection.to}\`,
          kind: "transition",
          label: \`\${connection.label || connectionId}\${requirement}\`,
          selected: selected === from || selected === \`room::\${connection.to}\`,
        });
      }
    }

    const skillUsers = {};
    for (const connection of Object.values(this.pkg.story.connections || {})) {
      if (!connection.skill_check) continue;
      (skillUsers[connection.skill_check] ||= []).push(connection);
    }

    for (const [skillId, check] of Object.entries(this.pkg.skill_checks.skill_checks || {})) {
      const users = skillUsers[skillId] || [];
      for (const connection of users) {
        for (const branch of ["success", "failure"]) {
          const outcome = check[branch] || {};
          const target = outcome.to || connection.to || connection.from;
          if (!rooms[target]) continue;
          edges.push({
            from: \`skill::\${skillId}\`,
            to: \`room::\${target}\`,
            kind: branch,
            label: users.length > 1
              ? \`\${branch} · \${connection.label || connection.from}\`
              : branch,
            selected:
              selected === \`skill::\${skillId}\` ||
              selected === \`room::\${target}\`,
          });
        }
      }
    }

    for (const [roomId, itemIds] of Object.entries(this.pkg.inventory.room_items || {})) {
      if (!Array.isArray(itemIds)) continue;
      for (const itemId of itemIds) {
        if (!this.pkg.inventory.items?.[itemId]) continue;
        edges.push({
          from: \`room::\${roomId}\`,
          to: \`item::\${itemId}\`,
          kind: "contains",
          label: "contains",
          selected:
            selected === \`room::\${roomId}\` ||
            selected === \`item::\${itemId}\`,
        });
      }
    }

    for (const [roomId, itemId] of Object.entries(
      this.pkg.inventory.room_requirements || {}
    )) {
      if (!this.pkg.inventory.items?.[itemId]) continue;
      edges.push({
        from: \`item::\${itemId}\`,
        to: \`room::\${roomId}\`,
        kind: "requirement",
        label: "required to enter",
        selected:
          selected === \`item::\${itemId}\` ||
          selected === \`room::\${roomId}\`,
      });
    }

    for (const [roomId, revisit] of Object.entries(this.pkg.story.revisits || {})) {
      const entries = Array.isArray(revisit.entries) ? revisit.entries : [];
      entries.forEach((_, index) => {
        edges.push({
          from: \`room::\${roomId}\`,
          to: \`revisit::\${roomId}::\${index}\`,
          kind: "revisit",
          label: revisit.show_all ? "revisit · all" : "revisit",
          selected:
            selected === \`room::\${roomId}\` ||
            selected === \`revisit::\${roomId}::\${index}\`,
        });
      });
    }

    for (const [roomId, room] of Object.entries(rooms)) {
      if (roomId === this.pkg.story.start_room) {
        edges.push({
          from: "world",
          to: \`room::\${roomId}\`,
          kind: "start",
          label: "start",
          selected: selected === \`room::\${roomId}\`,
        });
      }
    }
    return edges;
  }

  _renderInspector() {
    this.inspector.innerHTML = "";
    const title = document.createElement("div");
    title.className = "inspector-title";
    this.inspector.appendChild(title);

    if (this.selected === "world") {
      title.innerHTML = "<h2>World</h2><p>The graph is the world authoring surface.</p>";
      this._worldInspector();
      return;
    }

    const [type, id, extra] = this.selected.split("::");
    if (type === "room") {
      title.innerHTML = \`<h2>Room</h2><p>\${esc(id)}</p>\`;
      this._roomInspector(id);
    } else if (type === "skill") {
      title.innerHTML = \`<h2>Skill Check</h2><p>\${esc(id)}</p>\`;
      this._skillInspector(id);
    } else if (type === "item") {
      title.innerHTML = \`<h2>Item</h2><p>\${esc(id)}</p>\`;
      this._itemInspector(id);
    } else if (type === "revisit") {
      title.innerHTML = \`<h2>Revisit</h2><p>\${esc(id)} · entry \${esc(extra)}</p>\`;
      this._revisitInspector(id, Number(extra));
    }
  }

  _worldInspector() {
    const story = this.pkg.story;
    this.inspector.insertAdjacentHTML("beforeend", \`
      <section class="inspector-section">
        <label>World name<input data-field="world.name" value="\${esc(story.name)}"></label>
        <label>Start room
          <select data-field="world.start_room">
            \${Object.keys(story.rooms).map((id) =>
              \`<option value="\${esc(id)}" \${id === story.start_room ? "selected" : ""}>\${esc(id)}</option>\`
            ).join("")}
          </select>
        </label>
        <label>Metadata JSON
          <textarea class="inspector-code" data-field="world.metadata">\${esc(
            JSON.stringify(
              Object.fromEntries(
                Object.entries(story.metadata || {})
                  .filter(([key]) => key !== "__editor_graph")
              ),
              null,
              2
            )
          )}</textarea>
        </label>
        <p class="inspector-note">
          Graph layout is stored privately in story metadata and is not used by the VM.
        </p>
      </section>
      <button class="danger" data-inspector-action="delete-world" disabled>World cannot be deleted</button>
    \`);
  }

  _roomInspector(roomId) {
    const room = this.pkg.story.rooms[roomId];
    if (!room) return;
    const connections = Object.entries(this.pkg.story.connections || {})
      .filter(([, connection]) => connection.from === roomId);
    const items = Object.keys(this.pkg.inventory.items || {});
    const roomItems = this.pkg.inventory.room_items?.[roomId] || [];
    const required = this.pkg.inventory.room_requirements?.[roomId] || "";
    const revisits = this.pkg.story.revisits?.[roomId];
    const entries = Array.isArray(revisits?.entries) ? revisits.entries : [];
    const skillIds = Object.keys(this.pkg.skill_checks.skill_checks || {});

    this.inspector.insertAdjacentHTML("beforeend", \`
      <section class="inspector-section">
        <label>Room ID<input data-field="room.id" value="\${esc(roomId)}"></label>
        <button data-inspector-action="rename-room">Rename ID</button>
        <label>Display name<input data-field="room.name" value="\${esc(room.name || "")}"></label>
        <label>Description<textarea data-field="room.description">\${esc(room.description || "")}</textarea></label>
        <label>Image asset<input data-field="room.image" value="\${esc(room.image || "")}" placeholder="assets/example.png"></label>
        <label>Message<textarea data-field="room.message">\${esc(room.message || "")}</textarea></label>
        <label class="check-row"><input type="checkbox" data-field="room.show_map" \${room.show_map ? "checked" : ""}> Show map</label>
      </section>

      <section class="inspector-section">
        <h3>Exits</h3>
        \${connections.map(([connectionId, connection]) => \`
          <div class="inspector-card">
            <div class="row-between">
              <strong>\${esc(connectionId)}</strong>
              <button class="danger compact" data-inspector-action="delete-connection" data-connection-id="\${esc(connectionId)}">Delete</button>
            </div>
            <label>Label<input data-field="connection.label" data-connection-id="\${esc(connectionId)}" value="\${esc(connection.label || "")}"></label>
            <label>Target
              <select data-field="connection.to" data-connection-id="\${esc(connectionId)}">
                \${Object.keys(this.pkg.story.rooms).map((id) =>
                  \`<option value="\${esc(id)}" \${id === connection.to ? "selected" : ""}>\${esc(id)}</option>\`
                ).join("")}
              </select>
            </label>
            <label>Skill check
              <select data-field="connection.skill_check" data-connection-id="\${esc(connectionId)}">
                <option value="">None</option>
                \${skillIds.map((skillId) =>
                  \`<option value="\${esc(skillId)}" \${skillId === connection.skill_check ? "selected" : ""}>\${esc(skillId)}</option>\`
                ).join("")}
              </select>
            </label>
            <label>Required item
              <select data-field="connection.requires_item" data-connection-id="\${esc(connectionId)}">
                <option value="">None</option>
                \${items.map((itemId) =>
                  \`<option value="\${esc(itemId)}" \${itemId === connection.requires_item ? "selected" : ""}>\${esc(this.pkg.inventory.items[itemId]?.name || itemId)}</option>\`
                ).join("")}
              </select>
            </label>
          </div>
        \`).join("")}
        <button data-inspector-action="add-connection">+ Add exit</button>
      </section>

      <section class="inspector-section">
        <h3>Items here</h3>
        \${items.length ? items.map((itemId) => \`
          <label class="check-row">
            <input type="checkbox" data-item-placement="\${esc(itemId)}" \${roomItems.includes(itemId) ? "checked" : ""}>
            \${esc(this.pkg.inventory.items[itemId]?.name || itemId)}
          </label>
        \`).join("") : "<p class='inspector-note'>No items exist yet.</p>"}
      </section>

      <section class="inspector-section">
        <h3>Entry requirement</h3>
        <select data-field="room.required_item">
          <option value="">None</option>
          \${items.map((itemId) =>
            \`<option value="\${esc(itemId)}" \${itemId === required ? "selected" : ""}>\${esc(this.pkg.inventory.items[itemId]?.name || itemId)}</option>\`
          ).join("")}
        </select>
      </section>

      <section class="inspector-section">
        <h3>Revisits</h3>
        <label class="check-row">
          <input type="checkbox" data-field="room.revisit_show_all" \${revisits?.show_all ? "checked" : ""}>
          Show all eligible revisit entries
        </label>
        \${entries.map((entry, index) => \`
          <div class="inspector-card">
            <div class="row-between">
              <strong>Entry \${index}</strong>
              <button class="danger compact" data-inspector-action="delete-revisit" data-index="\${index}">Delete</button>
            </div>
            <label>Visit count<input type="number" min="0" step="1" data-field="revisit.count" data-index="\${index}" value="\${Number.isInteger(entry.count) ? entry.count : 0}"></label>
            <label>Content<textarea data-field="revisit.content" data-index="\${index}">\${esc(entry.content || "")}</textarea></label>
          </div>
        \`).join("")}
        <button data-inspector-action="add-revisit">+ Add revisit entry</button>
      </section>

      <button class="danger full-width" data-inspector-action="delete-room">Delete room</button>
    \`);

    this.inspector.querySelectorAll("[data-item-placement]").forEach((input) => {
      input.addEventListener("change", () => {
        const itemId = input.dataset.itemPlacement;
        const current = new Set(this.pkg.inventory.room_items?.[roomId] || []);
        if (input.checked) current.add(itemId);
        else current.delete(itemId);
        if (current.size) this.pkg.inventory.room_items[roomId] = [...current];
        else delete this.pkg.inventory.room_items[roomId];
        this._changed("Updated room item placement.");
      });
    });
  }

  _skillInspector(skillId) {
    const check = this.pkg.skill_checks.skill_checks[skillId];
    if (!check) return;
    const outcome = (branch) => check[branch] || {};
    this.inspector.insertAdjacentHTML("beforeend", \`
      <section class="inspector-section">
        <label>Skill ID<input data-field="skill.id" value="\${esc(skillId)}"></label>
        <button data-inspector-action="rename-skill">Rename ID</button>
        <label>Description<textarea data-field="skill.description">\${esc(check.description || "")}</textarea></label>
        <label>Dice expression<input data-field="skill.dice_type" value="\${esc(check.dice_type || "1d20")}"></label>
        <label>Target<input type="number" step="1" data-field="skill.target" value="\${Number.isInteger(check.target) ? check.target : 10}"></label>
      </section>
      \${["success", "failure"].map((branch) => \`
        <section class="inspector-section">
          <h3>\${branch[0].toUpperCase() + branch.slice(1)} outcome</h3>
          <label>Description<textarea data-field="skill.\${branch}.description">\${esc(outcome(branch).description || "")}</textarea></label>
          <label>Destination
            <select data-field="skill.\${branch}.to">
              <option value="">Use exit fallback</option>
              \${Object.keys(this.pkg.story.rooms).map((roomId) =>
                \`<option value="\${esc(roomId)}" \${roomId === outcome(branch).to ? "selected" : ""}>\${esc(roomId)}</option>\`
              ).join("")}
            </select>
          </label>
        </section>
      \`).join("")}
      <section class="inspector-section">
        <h3>Used by exits</h3>
        \${Object.entries(this.pkg.story.connections || {})
          .filter(([, connection]) => connection.skill_check === skillId)
          .map(([id, connection]) =>
            \`<button class="linkish" data-inspector-action="select-node" data-node-key="room::\${esc(connection.from)}">\${esc(connection.label || id)} · \${esc(connection.from)}</button>\`
          ).join("") || "<p class='inspector-note'>No exits reference this check.</p>"}
      </section>
      <button class="danger full-width" data-inspector-action="delete-skill">Delete skill check</button>
    \`);
  }

  _itemInspector(itemId) {
    const item = this.pkg.inventory.items[itemId];
    if (!item) return;
    const rooms = Object.keys(this.pkg.story.rooms);
    this.inspector.insertAdjacentHTML("beforeend", \`
      <section class="inspector-section">
        <label>Item ID<input data-field="item.id" value="\${esc(itemId)}"></label>
        <button data-inspector-action="rename-item">Rename ID</button>
        <label>Name<input data-field="item.name" value="\${esc(item.name || "")}"></label>
      </section>
      <section class="inspector-section">
        <h3>Placed in rooms</h3>
        \${rooms.map((roomId) => \`
          <label class="check-row">
            <input type="checkbox" data-item-room="\${esc(roomId)}" \${(this.pkg.inventory.room_items?.[roomId] || []).includes(itemId) ? "checked" : ""}>
            \${esc(this.pkg.story.rooms[roomId].name || roomId)}
          </label>
        \`).join("")}
      </section>
      <section class="inspector-section">
        <h3>Required to enter</h3>
        \${rooms.map((roomId) => \`
          <label class="check-row">
            <input type="checkbox" data-item-requirement-room="\${esc(roomId)}" \${this.pkg.inventory.room_requirements?.[roomId] === itemId ? "checked" : ""}>
            \${esc(this.pkg.story.rooms[roomId].name || roomId)}
          </label>
        \`).join("")}
      </section>
      <section class="inspector-section">
        <h3>Connections that require it</h3>
        \${Object.entries(this.pkg.story.connections || {})
          .filter(([, connection]) => connection.requires_item === itemId)
          .map(([id, connection]) =>
            \`<div class="inspector-note">\${esc(connection.from)} → \${esc(connection.to)} · \${esc(connection.label || id)}</div>\`
          ).join("") || "<p class='inspector-note'>None.</p>"}
      </section>
      <button class="danger full-width" data-inspector-action="delete-item">Delete item</button>
    \`);

    this.inspector.querySelectorAll("[data-item-room]").forEach((input) => {
      input.addEventListener("change", () => {
        const roomId = input.dataset.itemRoom;
        const current = new Set(this.pkg.inventory.room_items?.[roomId] || []);
        if (input.checked) current.add(itemId);
        else current.delete(itemId);
        if (current.size) this.pkg.inventory.room_items[roomId] = [...current];
        else delete this.pkg.inventory.room_items[roomId];
        this._changed("Updated item placement.");
      });
    });

    this.inspector.querySelectorAll("[data-item-requirement-room]").forEach((input) => {
      input.addEventListener("change", () => {
        const roomId = input.dataset.itemRequirementRoom;
        if (input.checked) this.pkg.inventory.room_requirements[roomId] = itemId;
        else if (this.pkg.inventory.room_requirements[roomId] === itemId) {
          delete this.pkg.inventory.room_requirements[roomId];
        }
        this._changed("Updated room requirement.");
      });
    });
  }

  _revisitInspector(roomId, index) {
    const data = this.pkg.story.revisits?.[roomId];
    const entry = data?.entries?.[index];
    if (!entry) return;
    this.inspector.insertAdjacentHTML("beforeend", \`
      <section class="inspector-section">
        <label>Visit count<input type="number" min="0" step="1" data-field="revisit.count" value="\${Number.isInteger(entry.count) ? entry.count : 0}"></label>
        <label>Content<textarea data-field="revisit.content">\${esc(entry.content || "")}</textarea></label>
        <label class="check-row"><input type="checkbox" data-field="revisit.show_all" \${data.show_all ? "checked" : ""}> Show all eligible entries for this room</label>
      </section>
      <button class="linkish" data-inspector-action="select-node" data-node-key="room::\${esc(roomId)}">Edit room</button>
      <button class="danger full-width" data-inspector-action="delete-revisit">Delete revisit entry</button>
    \`);
  }

  _fieldChanged(field) {
    const name = field.dataset.field;
    const value = field.type === "checkbox" ? field.checked : field.value;
    const [domain, ...parts] = name.split(".");

    try {
      if (domain === "world") {
        this._setWorldField(parts, value);
      } else if (domain === "room") {
        this._setRoomField(this._selectedId(), parts, value);
      } else if (domain === "connection") {
        this._setConnectionField(field.dataset.connectionId, parts, value);
      } else if (domain === "skill") {
        this._setSkillField(this._selectedId(), parts, value);
      } else if (domain === "item") {
        this._setItemField(this._selectedId(), parts, value);
      } else if (domain === "revisit") {
        this._setRevisitField(this._selectedId(), this._selectedRevisitIndex(), parts, value);
      }
      this._changed("Graph updated.");
    } catch (error) {
      this.onStatus(error instanceof Error ? error.message : String(error));
    }
  }

  _selectedId() {
    return this.selected.split("::")[1];
  }

  _selectedRevisitIndex() {
    return Number(this.selected.split("::")[2]);
  }

  _setWorldField(parts, value) {
    if (parts[0] === "name") this.pkg.story.name = String(value);
    if (parts[0] === "start_room") this.pkg.story.start_room = String(value);
    if (parts[0] === "metadata") {
      let parsed;
      try {
        parsed = JSON.parse(String(value) || "{}");
      } catch {
        throw new Error("Metadata must be valid JSON.");
      }
      const graph = this.pkg.story.metadata.__editor_graph;
      this.pkg.story.metadata = {...parsed, __editor_graph: graph};
    }
  }

  _setRoomField(roomId, parts, value) {
    const room = this.pkg.story.rooms[roomId];
    if (!room) return;
    if (parts[0] === "name") room.name = String(value);
    if (parts[0] === "description") room.description = String(value);
    if (parts[0] === "image") {
      if (String(value)) room.image = String(value);
      else delete room.image;
    }
    if (parts[0] === "message") {
      if (String(value)) room.message = String(value);
      else delete room.message;
    }
    if (parts[0] === "show_map") room.show_map = !!value;
    if (parts[0] === "required_item") {
      if (String(value)) this.pkg.inventory.room_requirements[roomId] = String(value);
      else delete this.pkg.inventory.room_requirements[roomId];
    }
    if (parts[0] === "revisit_show_all") {
      if (!this.pkg.story.revisits?.[roomId]) {
        this.pkg.story.revisits ||= {};
        this.pkg.story.revisits[roomId] = {show_all: !!value, entries: []};
      } else {
        this.pkg.story.revisits[roomId].show_all = !!value;
      }
    }
  }

  _setConnectionField(connectionId, parts, value) {
    const connection = this.pkg.story.connections[connectionId];
    if (!connection) return;
    if (parts[0] === "label") connection.label = String(value);
    if (parts[0] === "to") connection.to = String(value);
    if (parts[0] === "skill_check") {
      if (String(value)) connection.skill_check = String(value);
      else delete connection.skill_check;
    }
    if (parts[0] === "requires_item") {
      if (String(value)) connection.requires_item = String(value);
      else delete connection.requires_item;
    }
  }

  _setSkillField(skillId, parts, value) {
    const check = this.pkg.skill_checks.skill_checks[skillId];
    if (!check) return;
    if (parts[0] === "description") check.description = String(value);
    if (parts[0] === "dice_type") check.dice_type = String(value);
    if (parts[0] === "target") check.target = Number(value);
    if (parts[0] === "success" || parts[0] === "failure") {
      const branch = parts[0];
      check[branch] ||= {};
      if (parts[1] === "description") check[branch].description = String(value);
      if (parts[1] === "to") {
        if (String(value)) check[branch].to = String(value);
        else delete check[branch].to;
      }
    }
  }

  _setItemField(itemId, parts, value) {
    const item = this.pkg.inventory.items[itemId];
    if (!item) return;
    if (parts[0] === "name") item.name = String(value);
  }

  _setRevisitField(roomId, index, parts, value) {
    const data = this.pkg.story.revisits?.[roomId];
    const entry = data?.entries?.[index];
    if (!entry) return;
    if (parts[0] === "count") entry.count = Number(value);
    if (parts[0] === "content") entry.content = String(value);
    if (parts[0] === "show_all") data.show_all = !!value;
  }

  _inspectorAction(action, data) {
    try {
      if (action === "select-node") {
        this.selected = data.nodeKey;
        this._renderNodes();
        this._renderInspector();
        this._renderEdges();
        return;
      }
      if (action === "rename-room") this._renameRoom(this._selectedId());
      if (action === "rename-skill") this._renameSkill(this._selectedId());
      if (action === "rename-item") this._renameItem(this._selectedId());
      if (action === "delete-room") this._deleteRoom(this._selectedId());
      if (action === "delete-skill") this._deleteSkill(this._selectedId());
      if (action === "delete-item") this._deleteItem(this._selectedId());
      if (action === "delete-connection") this._deleteConnection(data.connectionId);
      if (action === "add-connection") this._addConnection(this._selectedId());
      if (action === "delete-revisit") {
        const index = data.index === undefined
          ? this._selectedRevisitIndex()
          : Number(data.index);
        this._deleteRevisit(this._selectedId(), index);
      }
      if (action === "add-revisit") this._addRevisit(this._selectedId());
    } catch (error) {
      this.onStatus(error instanceof Error ? error.message : String(error));
    }
  }

  _renameRoom(oldId) {
    const value = this.inspector.querySelector('[data-field="room.id"]')?.value.trim();
    if (!value || value === oldId) return;
    if (!/^[A-Za-z0-9_-]+$/.test(value)) throw new Error("Room IDs may use letters, numbers, '_' and '-'.");
    if (this.pkg.story.rooms[value]) throw new Error(\`Room "\${value}" already exists.\`);
    this.pkg.story.rooms[value] = this.pkg.story.rooms[oldId];
    delete this.pkg.story.rooms[oldId];
    if (this.pkg.story.start_room === oldId) this.pkg.story.start_room = value;
    for (const connection of Object.values(this.pkg.story.connections || {})) {
      if (connection.from === oldId) connection.from = value;
      if (connection.to === oldId) connection.to = value;
    }
    for (const check of Object.values(this.pkg.skill_checks.skill_checks || {})) {
      for (const branch of ["success", "failure"]) {
        if (check[branch]?.to === oldId) check[branch].to = value;
      }
    }
    if (this.pkg.story.revisits?.[oldId]) {
      this.pkg.story.revisits[value] = this.pkg.story.revisits[oldId];
      delete this.pkg.story.revisits[oldId];
    }
    if (this.pkg.inventory.room_items?.[oldId]) {
      this.pkg.inventory.room_items[value] = this.pkg.inventory.room_items[oldId];
      delete this.pkg.inventory.room_items[oldId];
    }
    if (this.pkg.inventory.room_requirements?.[oldId]) {
      this.pkg.inventory.room_requirements[value] = this.pkg.inventory.room_requirements[oldId];
      delete this.pkg.inventory.room_requirements[oldId];
    }
    this._moveKey(\`room::\${oldId}\`, \`room::\${value}\`);
    for (const key of Object.keys(this.positions)) {
      if (key.startsWith(\`revisit::\${oldId}::\`)) {
        const next = key.replace(\`revisit::\${oldId}::\`, \`revisit::\${value}::\`);
        this._moveKey(key, next);
      }
    }
    this.selected = \`room::\${value}\`;
    this._changed(\`Renamed room to \${value}.\`);
  }

  _renameSkill(oldId) {
    const value = this.inspector.querySelector('[data-field="skill.id"]')?.value.trim();
    if (!value || value === oldId) return;
    if (!/^[A-Za-z0-9_-]+$/.test(value)) throw new Error("Skill IDs may use letters, numbers, '_' and '-'.");
    if (this.pkg.skill_checks.skill_checks[value]) throw new Error(\`Skill check "\${value}" already exists.\`);
    this.pkg.skill_checks.skill_checks[value] = this.pkg.skill_checks.skill_checks[oldId];
    delete this.pkg.skill_checks.skill_checks[oldId];
    for (const connection of Object.values(this.pkg.story.connections || {})) {
      if (connection.skill_check === oldId) connection.skill_check = value;
    }
    this._moveKey(\`skill::\${oldId}\`, \`skill::\${value}\`);
    this.selected = \`skill::\${value}\`;
    this._changed(\`Renamed skill check to \${value}.\`);
  }

  _renameItem(oldId) {
    const value = this.inspector.querySelector('[data-field="item.id"]')?.value.trim();
    if (!value || value === oldId) return;
    if (!/^[A-Za-z0-9_-]+$/.test(value)) throw new Error("Item IDs may use letters, numbers, '_' and '-'.");
    if (this.pkg.inventory.items[value]) throw new Error(\`Item "\${value}" already exists.\`);
    this.pkg.inventory.items[value] = this.pkg.inventory.items[oldId];
    delete this.pkg.inventory.items[oldId];
    for (const [roomId, ids] of Object.entries(this.pkg.inventory.room_items || {})) {
      this.pkg.inventory.room_items[roomId] = ids.map((id) => id === oldId ? value : id);
    }
    for (const roomId of Object.keys(this.pkg.inventory.room_requirements || {})) {
      if (this.pkg.inventory.room_requirements[roomId] === oldId) {
        this.pkg.inventory.room_requirements[roomId] = value;
      }
    }
    for (const connection of Object.values(this.pkg.story.connections || {})) {
      if (connection.requires_item === oldId) connection.requires_item = value;
    }
    this._moveKey(\`item::\${oldId}\`, \`item::\${value}\`);
    this.selected = \`item::\${value}\`;
    this._changed(\`Renamed item to \${value}.\`);
  }

  _moveKey(oldKey, newKey) {
    if (this.positions[oldKey]) {
      this.positions[newKey] = this.positions[oldKey];
      delete this.positions[oldKey];
    }
  }

  _deleteSelected() {
    const [type, id, extra] = this.selected.split("::");
    if (type === "room") this._deleteRoom(id);
    else if (type === "skill") this._deleteSkill(id);
    else if (type === "item") this._deleteItem(id);
    else if (type === "revisit") this._deleteRevisit(id, Number(extra));
  }

  _deleteRoom(roomId) {
    if (this.pkg.story.start_room === roomId) {
      throw new Error("Move the start room before deleting it.");
    }
    delete this.pkg.story.rooms[roomId];
    for (const [id, connection] of Object.entries(this.pkg.story.connections || {})) {
      if (connection.from === roomId || connection.to === roomId) delete this.pkg.story.connections[id];
    }
    delete this.pkg.story.revisits?.[roomId];
    delete this.pkg.inventory.room_items?.[roomId];
    delete this.pkg.inventory.room_requirements?.[roomId];
    for (const check of Object.values(this.pkg.skill_checks.skill_checks || {})) {
      for (const branch of ["success", "failure"]) {
        if (check[branch]?.to === roomId) delete check[branch].to;
      }
    }
    delete this.positions[\`room::\${roomId}\`];
    for (const key of Object.keys(this.positions)) {
      if (key.startsWith(\`revisit::\${roomId}::\`)) delete this.positions[key];
    }
    this.selected = "world";
    this._changed(\`Deleted room \${roomId}.\`);
  }

  _deleteSkill(skillId) {
    delete this.pkg.skill_checks.skill_checks[skillId];
    for (const connection of Object.values(this.pkg.story.connections || {})) {
      if (connection.skill_check === skillId) delete connection.skill_check;
    }
    delete this.positions[\`skill::\${skillId}\`];
    this.selected = "world";
    this._changed(\`Deleted skill check \${skillId}.\`);
  }

  _deleteItem(itemId) {
    delete this.pkg.inventory.items[itemId];
    for (const [roomId, ids] of Object.entries(this.pkg.inventory.room_items || {})) {
      this.pkg.inventory.room_items[roomId] = ids.filter((id) => id !== itemId);
      if (!this.pkg.inventory.room_items[roomId].length) delete this.pkg.inventory.room_items[roomId];
    }
    for (const roomId of Object.keys(this.pkg.inventory.room_requirements || {})) {
      if (this.pkg.inventory.room_requirements[roomId] === itemId) {
        delete this.pkg.inventory.room_requirements[roomId];
      }
    }
    for (const connection of Object.values(this.pkg.story.connections || {})) {
      if (connection.requires_item === itemId) delete connection.requires_item;
    }
    delete this.positions[\`item::\${itemId}\`];
    this.selected = "world";
    this._changed(\`Deleted item \${itemId}.\`);
  }

  _deleteConnection(connectionId) {
    delete this.pkg.story.connections[connectionId];
    this._changed("Deleted exit.");
  }

  _deleteRevisit(roomId, index) {
    const data = this.pkg.story.revisits?.[roomId];
    if (!data?.entries?.[index]) return;
    data.entries.splice(index, 1);
    if (!data.entries.length) delete this.pkg.story.revisits[roomId];
    this.selected = \`room::\${roomId}\`;
    this._changed("Deleted revisit entry.");
  }

  _addConnection(roomId) {
    const existing = new Set(Object.keys(this.pkg.story.connections || {}));
    const base = \`\${roomId}__new_exit\`;
    let id = base;
    let n = 2;
    while (existing.has(id)) id = \`\${base}_\${n++}\`;
    const rooms = Object.keys(this.pkg.story.rooms);
    const target = rooms.find((id) => id !== roomId) || roomId;
    this.pkg.story.connections[id] = {
      from: roomId,
      to: target,
      label: "New exit",
    };
    this._changed("Added exit.");
  }

  _addRevisit(roomId) {
    this.pkg.story.revisits ||= {};
    this.pkg.story.revisits[roomId] ||= {show_all: false, entries: []};
    this.pkg.story.revisits[roomId].entries.push({
      count: 1,
      content: "You have been here before.",
    });
    const index = this.pkg.story.revisits[roomId].entries.length - 1;
    this.selected = \`revisit::\${roomId}::\${index}\`;
    this._changed("Added revisit entry.");
  }

  _action(action) {
    try {
      if (action === "add-room") this._addRoom();
      if (action === "add-skill") this._addSkill();
      if (action === "add-item") this._addItem();
      if (action === "add-revisit") {
        const room = this.selected.startsWith("room::")
          ? this._selectedId()
          : null;
        if (!room) throw new Error("Select a room before adding a revisit entry.");
        this._addRevisit(room);
      }
      if (action === "auto-layout") this._autoLayout();
      if (action === "fit") this._fit();
      if (action === "zoom-in") this._zoomAtCenter(1.15);
      if (action === "zoom-out") this._zoomAtCenter(0.87);
      if (action === "zoom-reset") {
        this.scale = 1;
        this.panX = 24;
        this.panY = 24;
        this._applyViewport();
      }
    } catch (error) {
      this.onStatus(error instanceof Error ? error.message : String(error));
    }
  }

  _addRoom() {
    const rooms = this.pkg.story.rooms;
    let id = "room_1";
    let n = 1;
    while (rooms[id]) id = \`room_\${++n}\`;
    rooms[id] = {description: "New room.", show_map: true};
    const others = Object.keys(rooms);
    this.pkg.story.connections ||= {};
    this.selected = \`room::\${id}\`;
    this.positions[this.selected] = {
      x: 100 + (others.length % 4) * 260,
      y: 320 + Math.floor(others.length / 4) * 190,
    };
    this._changed(\`Added room \${id}.\`);
  }

  _addSkill() {
    const checks = this.pkg.skill_checks.skill_checks;
    let id = "skill_1";
    let n = 1;
    while (checks[id]) id = \`skill_\${++n}\`;
    checks[id] = {
      dice_type: "1d20",
      target: 10,
      description: "Describe the challenge.",
      success: {description: "Success.", to: ""},
      failure: {description: "Failure.", to: ""},
    };
    this.selected = \`skill::\${id}\`;
    this.positions[this.selected] = {x: 420, y: 320 + Object.keys(checks).length * 180};
    this._changed(\`Added skill check \${id}.\`);
  }

  _addItem() {
    const items = this.pkg.inventory.items;
    let id = "item_1";
    let n = 1;
    while (items[id]) id = \`item_\${++n}\`;
    items[id] = {name: "New item"};
    this.selected = \`item::\${id}\`;
    this.positions[this.selected] = {x: 760, y: 320 + Object.keys(items).length * 150};
    this._changed(\`Added item \${id}.\`);
  }

  _autoLayout() {
    const nodes = this._nodeData();
    const buckets = {
      world: [],
      room: [],
      skill: [],
      item: [],
      revisit: [],
    };
    nodes.forEach((node) => buckets[node.type].push(node));
    const layout = (list, x, y, width, rowHeight) => {
      list.forEach((node, index) => {
        this.positions[node.key] = {
          x: x + (index % 3) * width,
          y: y + Math.floor(index / 3) * rowHeight,
        };
      });
    };
    layout(buckets.world, 50, 50, 250, 180);
    layout(buckets.room, 50, 220, 280, 190);
    layout(buckets.skill, 70, 220 + Math.max(1, buckets.room.length / 3) * 190, 280, 190);
    layout(buckets.item, 70, 420 + Math.max(1, buckets.room.length / 3) * 190, 280, 170);
    layout(buckets.revisit, 70, 600 + Math.max(1, buckets.room.length / 3) * 190, 280, 170);
    this._changed("Auto-layout complete.");
    this._fit();
  }

  _zoomAtCenter(multiplier) {
    const rect = this.stage.getBoundingClientRect();
    const sx = rect.width / 2;
    const sy = rect.height / 2;
    const wx = (sx - this.panX) / this.scale;
    const wy = (sy - this.panY) / this.scale;
    this.scale = Math.max(0.35, Math.min(2.25, this.scale * multiplier));
    this.panX = sx - wx * this.scale;
    this.panY = sy - wy * this.scale;
    this._applyViewport();
  }

  _fit() {
    const nodes = this._nodeData();
    if (!nodes.length) return;
    let minX = Infinity;
    let minY = Infinity;
    let maxX = -Infinity;
    let maxY = -Infinity;
    nodes.forEach((node) => {
      const pos = this._positionFor(node, 0);
      minX = Math.min(minX, pos.x);
      minY = Math.min(minY, pos.y);
      maxX = Math.max(maxX, pos.x + 240);
      maxY = Math.max(maxY, pos.y + 150);
    });
    const width = Math.max(1, maxX - minX);
    const height = Math.max(1, maxY - minY);
    const scaleX = this.stage.clientWidth / (width + 80);
    const scaleY = this.stage.clientHeight / (height + 80);
    this.scale = Math.max(0.35, Math.min(1.5, scaleX, scaleY));
    this.panX = (this.stage.clientWidth - width * this.scale) / 2 - minX * this.scale;
    this.panY = (this.stage.clientHeight - height * this.scale) / 2 - minY * this.scale;
    this._applyViewport();
  }

  _persistPositions() {
    this._ensureMetadata();
    this.pkg.story.metadata.__editor_graph.nodes = this.positions;
    this.onChange(this.pkg);
  }

  _changed(status) {
    this._ensureMetadata();
    this.pkg.story.metadata.__editor_graph.nodes = this.positions;
    this._renderNodes();
    this._renderInspector();
    this._renderEdges();
    this.onChange(this.pkg);
    this.onStatus(status);
  }
}

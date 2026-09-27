
const esc = function(value) {
  return String(value == null ? "" : value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
};

const text = function(value, fallback) {
  return value == null ? (fallback || "") : String(value);
};

const clone = function(value) {
  return JSON.parse(JSON.stringify(value));
};

export class GraphEditor {
  constructor(options) {
    this.mount = options.mount;
    this.pkg = options.packageData;
    this.onChange = options.onChange;
    this.onStatus = options.onStatus;
    this.selected = "world";
    this.scale = 1;
    this.panX = 30;
    this.panY = 30;
    this.drag = null;
    this.pan = null;
    this.connecting = null;
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
    var metadata = this.pkg && this.pkg.story && this.pkg.story.metadata;
    var graph = metadata && metadata.__editor_graph;
    return graph && graph.nodes ? clone(graph.nodes) : {};
  }

  _ensureShape() {
    var story = this.pkg.story;
    var inventory = this.pkg.inventory;
    story.rooms = story.rooms || {};
    story.connections = story.connections || {};
    story.revisits = story.revisits || {};
    story.metadata = story.metadata || {};
    this.pkg.skill_checks = this.pkg.skill_checks || {
      schema_version: 1,
      skill_checks: {}
    };
    this.pkg.skill_checks.skill_checks = this.pkg.skill_checks.skill_checks || {};
    inventory.items = inventory.items || {};
    inventory.room_items = inventory.room_items || {};
    inventory.room_requirements = inventory.room_requirements || {};
    if (!story.metadata.__editor_graph || typeof story.metadata.__editor_graph !== "object") {
      story.metadata.__editor_graph = {};
    }
    story.metadata.__editor_graph.nodes = this.positions;
  }

  _buildShell() {
    this.mount.innerHTML =
      '<div class="graph-toolbar">' +
        '<button data-graph-action="add-room">+ Room</button>' +
        '<button data-graph-action="add-exit">+ Exit</button>' +
        '<button data-graph-action="add-skill">+ Skill Check</button>' +
        '<button data-graph-action="add-item">+ Pickup</button>' +
        '<button data-graph-action="add-revisit">+ Revisit</button>' +
        '<span class="graph-toolbar-spacer"></span>' +
        '<button data-graph-action="auto-layout">Auto Layout</button>' +
        '<button data-graph-action="fit">Fit</button>' +
        '<button data-graph-action="zoom-out">−</button>' +
        '<button data-graph-action="zoom-reset">100%</button>' +
        '<button data-graph-action="zoom-in">+</button>' +
      '</div>' +
      '<div class="graph-main">' +
        '<div class="graph-stage" tabindex="0">' +
          '<svg class="graph-edges" aria-hidden="true"></svg>' +
          '<div class="graph-node-layer"></div>' +
          '<div class="graph-help">' +
            'Drag nodes to arrange the flow. Drag a port to another port to build exits, ' +
            'pickups and skill branches. Empty space pans; wheel zooms. Delete removes the selected node.' +
          '</div>' +
        '</div>' +
        '<aside class="graph-inspector"></aside>' +
      '</div>';

    this.stage = this.mount.querySelector(".graph-stage");
    this.edges = this.mount.querySelector(".graph-edges");
    this.nodeLayer = this.mount.querySelector(".graph-node-layer");
    this.inspector = this.mount.querySelector(".graph-inspector");
  }

  _bind() {
    this.mount.addEventListener("click", (event) => {
      var action = event.target.closest("[data-graph-action]");
      if (action) this._action(action.dataset.graphAction);
    });

    this.inspector.addEventListener("click", (event) => {
      var button = event.target.closest("[data-inspector-action]");
      if (button) this._inspectorAction(button.dataset.inspectorAction, button.dataset);
    });

    this.inspector.addEventListener("change", (event) => {
      var field = event.target.closest("[data-field]");
      if (field) this._fieldChanged(field);
    });

    this.stage.addEventListener("pointerdown", (event) => {
      if (event.target.closest(".graph-port")) return;
      if (event.target.closest(".graph-node")) return;
      this.pan = {
        pointerId: event.pointerId,
        x: event.clientX,
        y: event.clientY,
        panX: this.panX,
        panY: this.panY
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

    var endPan = (event) => {
      if (!this.pan || event.pointerId !== this.pan.pointerId) return;
      this.pan = null;
      this.stage.classList.remove("panning");
      this._persistPositions();
    };
    this.stage.addEventListener("pointerup", endPan);
    this.stage.addEventListener("pointercancel", endPan);

    document.addEventListener("pointermove", (event) => {
      if (!this.connecting) return;
      this.connecting.clientX = event.clientX;
      this.connecting.clientY = event.clientY;
      this._renderEdges();
    });

    document.addEventListener("pointerup", (event) => {
      if (!this.connecting) return;
      var wire = this.connecting;
      this.connecting = null;
      this.stage.classList.remove("wiring");

      var element = document.elementFromPoint(event.clientX, event.clientY);
      var target = element && element.closest(".graph-port");
      if (target) {
        this._finishConnection(
          wire.nodeKey,
          wire.port,
          wire.direction,
          target.dataset.nodeKey,
          target.dataset.port,
          target.dataset.direction
        );
      } else {
        this.onStatus("Wire cancelled.");
      }
      this._renderEdges();
    });

    this.stage.addEventListener("wheel", (event) => {
      event.preventDefault();
      var rect = this.stage.getBoundingClientRect();
      var sx = event.clientX - rect.left;
      var sy = event.clientY - rect.top;
      var wx = (sx - this.panX) / this.scale;
      var wy = (sy - this.panY) / this.scale;
      var next = Math.max(0.35, Math.min(2.25, this.scale * (event.deltaY < 0 ? 1.1 : 0.9)));
      this.panX = sx - wx * next;
      this.panY = sy - wy * next;
      this.scale = next;
      this._applyViewport();
    }, {passive: false});

    window.addEventListener("keydown", (event) => {
      if (!this.mount.isConnected) return;
      var active = document.activeElement;
      if (active && ["INPUT", "TEXTAREA", "SELECT"].includes(active.tagName)) return;
      if (event.key === "Delete" && this.selected !== "world") {
        event.preventDefault();
        this._deleteSelected();
      }
      if (event.key === "0") this._fit();
      if (event.key === "Escape" && this.connecting) {
        this.connecting = null;
        this.stage.classList.remove("wiring");
        this._renderEdges();
        this.onStatus("Wire cancelled.");
      }
    });

    window.addEventListener("resize", () => {
      if (this.mount.isConnected) this._renderEdges();
    });
  }

  render() {
    this._ensureShape();
    this._renderNodes();
    this._renderInspector();
    this._renderEdges();
    this._applyViewport();
  }

  _nodeExists(key) {
    if (key === "world") return true;
    var parts = key.split("::");
    if (parts[0] === "room") return !!this.pkg.story.rooms[parts[1]];
    if (parts[0] === "exit") return !!this.pkg.story.connections[parts[1]];
    if (parts[0] === "skill") return !!this.pkg.skill_checks.skill_checks[parts[1]];
    if (parts[0] === "item") return !!this.pkg.inventory.items[parts[1]];
    if (parts[0] === "revisit") {
      var index = Number(parts[2]);
      return !!(this.pkg.story.revisits[parts[1]] &&
        Array.isArray(this.pkg.story.revisits[parts[1]].entries) &&
        this.pkg.story.revisits[parts[1]].entries[index]);
    }
    return false;
  }

  _nodeData() {
    var nodes = [{
      key: "world",
      type: "world",
      title: this.pkg.story.name || "World",
      subtitle: "Narrative VM program"
    }];

    Object.entries(this.pkg.story.rooms).forEach(([id, room]) => {
      var badges = [];
      if (id === this.pkg.story.start_room) badges.push("START");
      if (room.image) badges.push("IMAGE");
      if ((this.pkg.inventory.room_items[id] || []).length) badges.push("PICKUPS");
      if (this.pkg.story.revisits[id] && (this.pkg.story.revisits[id].entries || []).length) badges.push("REVISITS");
      var exitCount = Object.values(this.pkg.story.connections).filter((connection) => connection.from === id).length;
      if (exitCount) badges.push(exitCount + " EXITS");

      nodes.push({
        key: "room::" + id,
        type: "room",
        id: id,
        title: room.name || id,
        subtitle: id,
        body: text(room.description, "No description").slice(0, 150),
        badges: badges
      });
    });

    Object.entries(this.pkg.story.connections).forEach(([id, connection]) => {
      var skill = connection.skill_check
        ? this.pkg.skill_checks.skill_checks[connection.skill_check]
        : null;
      nodes.push({
        key: "exit::" + id,
        type: "exit",
        id: id,
        title: connection.label || id,
        subtitle: connection.to ? "→ " + connection.to : "unassigned destination",
        body: [
          skill ? "Check: " + connection.skill_check : "Direct exit",
          connection.requires_item
            ? "Needs: " + (this.pkg.inventory.items[connection.requires_item]?.name || connection.requires_item)
            : ""
        ].filter(Boolean).join(" · "),
        badges: [
          skill ? "SKILL" : "DIRECT",
          connection.requires_item ? "LOCKED" : ""
        ].filter(Boolean)
      });
    });

    Object.entries(this.pkg.skill_checks.skill_checks).forEach(([id, check]) => {
      nodes.push({
        key: "skill::" + id,
        type: "skill",
        id: id,
        title: id,
        subtitle: (check.dice_type || "1d20") + " ≥ " + (check.target == null ? 10 : check.target),
        body: text(check.description || "Skill check").slice(0, 130)
      });
    });

    Object.entries(this.pkg.inventory.items).forEach(([id, item]) => {
      var placed = Object.entries(this.pkg.inventory.room_items)
        .filter((entry) => Array.isArray(entry[1]) && entry[1].includes(id))
        .map((entry) => entry[0]);
      nodes.push({
        key: "item::" + id,
        type: "item",
        id: id,
        title: item.name || id,
        subtitle: id,
        body: placed.length ? "Pickup in: " + placed.join(", ") : "Not placed"
      });
    });

    Object.entries(this.pkg.story.revisits).forEach(([roomId, data]) => {
      var entries = Array.isArray(data.entries) ? data.entries : [];
      entries.forEach((entry, index) => {
        nodes.push({
          key: "revisit::" + roomId + "::" + index,
          type: "revisit",
          id: roomId,
          index: index,
          title: "Revisit " + (entry.count == null ? 0 : entry.count) + "+",
          subtitle: roomId,
          body: text(entry.content, "").slice(0, 130)
        });
      });
    });

    return nodes;
  }

  _positionFor(node, index) {
    var pos = this.positions[node.key];
    if (pos && Number.isFinite(pos.x) && Number.isFinite(pos.y)) return pos;

    var base = {
      world: {x: 60, y: 50},
      room: {x: 60, y: 220},
      exit: {x: 330, y: 220},
      skill: {x: 620, y: 220},
      item: {x: 910, y: 220},
      revisit: {x: 1170, y: 220}
    }[node.type] || {x: 60, y: 220};

    pos = {
      x: base.x + (index % 3) * 260,
      y: base.y + Math.floor(index / 3) * 190
    };
    this.positions[node.key] = pos;
    return pos;
  }

  _portMarkup(node) {
    var ports = [];
    if (node.type === "world") {
      ports.push(
        '<span class="graph-port port-out port-right" data-node-key="' + esc(node.key) +
        '" data-port="start" data-direction="out" title="Start room"></span>'
      );
    } else if (node.type === "room") {
      ports.push(
        '<span class="graph-port port-in port-left" data-node-key="' + esc(node.key) +
        '" data-port="in" data-direction="in" title="Room arrival"></span>'
      );
      ports.push(
        '<span class="graph-port port-out port-right" data-node-key="' + esc(node.key) +
        '" data-port="exit" data-direction="out" title="Create exit"></span>'
      );
      ports.push(
        '<span class="graph-port port-in port-bottom" data-node-key="' + esc(node.key) +
        '" data-port="pickup" data-direction="in" title="Pickup appears here"></span>'
      );
      ports.push(
        '<span class="graph-port port-in port-top" data-node-key="' + esc(node.key) +
        '" data-port="requirement" data-direction="in" title="Item required here"></span>'
      );
    } else if (node.type === "exit") {
      ports.push(
        '<span class="graph-port port-in port-left" data-node-key="' + esc(node.key) +
        '" data-port="from" data-direction="in" title="Exit source"></span>'
      );
      ports.push(
        '<span class="graph-port port-out port-right" data-node-key="' + esc(node.key) +
        '" data-port="target" data-direction="out" title="Exit destination"></span>'
      );
      ports.push(
        '<span class="graph-port port-out port-bottom" data-node-key="' + esc(node.key) +
        '" data-port="skill" data-direction="out" title="Use skill check"></span>'
      );
    } else if (node.type === "skill") {
      ports.push(
        '<span class="graph-port port-in port-left" data-node-key="' + esc(node.key) +
        '" data-port="challenge" data-direction="in" title="Skill check"></span>'
      );
      ports.push(
        '<span class="graph-port port-out port-right success" data-node-key="' + esc(node.key) +
        '" data-port="success" data-direction="out" title="Success"></span>'
      );
      ports.push(
        '<span class="graph-port port-out port-bottom failure" data-node-key="' + esc(node.key) +
        '" data-port="failure" data-direction="out" title="Failure"></span>'
      );
    } else if (node.type === "item") {
      ports.push(
        '<span class="graph-port port-out port-right" data-node-key="' + esc(node.key) +
        '" data-port="item" data-direction="out" title="Place or require item"></span>'
      );
    }
    return ports.join("");
  }

  _renderNodes() {
    this.nodeLayer.innerHTML = "";
    var nodes = this._nodeData();

    nodes.forEach((node, index) => {
      var pos = this._positionFor(node, index);
      var el = document.createElement("article");
      el.className = "graph-node node-" + node.type + (node.key === this.selected ? " selected" : "");
      el.dataset.nodeKey = node.key;
      el.style.left = pos.x + "px";
      el.style.top = pos.y + "px";

      var badges = node.badges && node.badges.length
        ? '<div class="graph-badges">' +
          node.badges.map((badge) => "<span>" + esc(badge) + "</span>").join("") +
          "</div>"
        : "";

      el.innerHTML =
        '<div class="graph-node-header">' +
          '<span class="node-kind">' + esc(node.type) + "</span>" +
          "<strong>" + esc(node.title) + "</strong>" +
        "</div>" +
        '<div class="graph-node-subtitle">' + esc(node.subtitle) + "</div>" +
        (node.body ? '<div class="graph-node-body">' + esc(node.body) + "</div>" : "") +
        badges +
        '<div class="graph-ports">' + this._portMarkup(node) + "</div>";

      el.querySelectorAll(".graph-port").forEach((port) => {
        port.addEventListener("pointerdown", (event) => {
          event.preventDefault();
          event.stopPropagation();
          if (event.button !== 0) return;
          this._startConnection(
            node.key,
            port.dataset.port,
            port.dataset.direction,
            event.clientX,
            event.clientY
          );
        });
      });

      el.addEventListener("click", (event) => {
        if (event.target.closest(".graph-port")) return;
        event.stopPropagation();
        this.selected = node.key;
        this._renderNodes();
        this._renderInspector();
        this._renderEdges();
      });

      el.addEventListener("pointerdown", (event) => {
        if (event.target.closest(".graph-port")) return;
        event.stopPropagation();
        if (event.button !== 0) return;
        var current = this.positions[node.key];
        this.drag = {
          pointerId: event.pointerId,
          key: node.key,
          x: event.clientX,
          y: event.clientY,
          startX: current.x,
          startY: current.y
        };
        el.setPointerCapture(event.pointerId);
        el.classList.add("dragging");
      });

      el.addEventListener("pointermove", (event) => {
        if (!this.drag || event.pointerId !== this.drag.pointerId) return;
        var dx = (event.clientX - this.drag.x) / this.scale;
        var dy = (event.clientY - this.drag.y) / this.scale;
        this.positions[this.drag.key] = {
          x: Math.max(0, this.drag.startX + dx),
          y: Math.max(0, this.drag.startY + dy)
        };
        el.style.left = this.positions[this.drag.key].x + "px";
        el.style.top = this.positions[this.drag.key].y + "px";
        this._renderEdges();
      });

      var endDrag = (event) => {
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
    var transform = "translate(" + this.panX + "px, " + this.panY + "px) scale(" + this.scale + ")";
    this.nodeLayer.style.transform = transform;
    this.edges.style.transform = transform;
    var zoomButton = this.mount.querySelector('[data-graph-action="zoom-reset"]');
    if (zoomButton) zoomButton.textContent = Math.round(this.scale * 100) + "%";
    this._renderEdges();
  }

  _startConnection(nodeKey, port, direction, clientX, clientY) {
    if (direction !== "out") return;
    this.connecting = {
      nodeKey: nodeKey,
      port: port,
      direction: direction,
      clientX: clientX,
      clientY: clientY
    };
    this.stage.classList.add("wiring");
    this.onStatus("Wiring: release on a compatible port.");
    this._renderEdges();
  }

  _portAnchor(el, port, fallbackSide) {
    var stageRect = this.stage.getBoundingClientRect();
    var portEl = el.querySelector('.graph-port[data-port="' + port + '"]');
    if (portEl) {
      var rect = portEl.getBoundingClientRect();
      return {
        x: (rect.left + rect.width / 2 - stageRect.left - this.panX) / this.scale,
        y: (rect.top + rect.height / 2 - stageRect.top - this.panY) / this.scale
      };
    }

    var pos = this.positions[el.dataset.nodeKey] || {x: 0, y: 0};
    return {
      x: pos.x + (fallbackSide === "out" ? (el.offsetWidth || 230) : 0),
      y: pos.y + (el.offsetHeight || 100) / 2
    };
  }

  _finishConnection(sourceKey, sourcePort, sourceDirection, targetKey, targetPort, targetDirection) {
    if (sourceDirection !== "out" || targetDirection !== "in") {
      this.onStatus("A wire must run from an output port to an input port.");
      return;
    }

    var sourceParts = sourceKey.split("::");
    var targetParts = targetKey.split("::");
    var sourceType = sourceParts[0];
    var sourceId = sourceParts[1];
    var targetType = targetParts[0];
    var targetId = targetParts[1];

    if (sourceType === "world" && sourcePort === "start" &&
        targetType === "room" && targetPort === "in") {
      this.pkg.story.start_room = targetId;
      this._changed("Set start room to " + targetId + ".");
      return;
    }

    if (sourceType === "room" && sourcePort === "exit" &&
        targetType === "room" && targetPort === "in") {
      var roomExit = this._createConnection(sourceId, targetId);
      this.selected = "exit::" + roomExit;
      this._changed("Created Room → Exit → Room.");
      return;
    }

    if (sourceType === "room" && sourcePort === "exit" &&
        targetType === "exit" && targetPort === "from") {
      this.pkg.story.connections[targetId].from = sourceId;
      this._changed("Moved exit to " + sourceId + ".");
      return;
    }

    if (sourceType === "room" && sourcePort === "exit" &&
        targetType === "skill" && targetPort === "challenge") {
      var skillExit = this._createConnection(
        sourceId,
        this._fallbackRoom(sourceId),
        targetId
      );
      this.selected = "exit::" + skillExit;
      this._changed("Created Room → Exit → Skill Check.");
      return;
    }

    if (sourceType === "exit" && sourcePort === "target" &&
        targetType === "room" && targetPort === "in") {
      var connection = this.pkg.story.connections[sourceId];
      if (!connection) return;
      connection.to = targetId;
      this._changed("Set exit destination to " + targetId + ".");
      return;
    }

    if (sourceType === "exit" && sourcePort === "skill" &&
        targetType === "skill" && targetPort === "challenge") {
      var exitConnection = this.pkg.story.connections[sourceId];
      if (!exitConnection) return;
      exitConnection.skill_check = targetId;
      this._changed("Attached " + targetId + " to the exit.");
      return;
    }

    if (sourceType === "skill" &&
        (sourcePort === "success" || sourcePort === "failure") &&
        targetType === "room" && targetPort === "in") {
      var check = this.pkg.skill_checks.skill_checks[sourceId];
      if (!check) return;
      check[sourcePort] = check[sourcePort] || {};
      check[sourcePort].to = targetId;
      this._changed("Set " + sourcePort + " branch to " + targetId + ".");
      return;
    }

    if (sourceType === "item" && sourcePort === "item" &&
        targetType === "room" &&
        (targetPort === "pickup" || targetPort === "requirement")) {
      if (targetPort === "pickup") {
        var ids = new Set(this.pkg.inventory.room_items[targetId] || []);
        ids.add(sourceId);
        this.pkg.inventory.room_items[targetId] = Array.from(ids);
        this._changed("Placed " + sourceId + " as a pickup in " + targetId + ".");
      } else {
        this.pkg.inventory.room_requirements[targetId] = sourceId;
        this._changed("Made " + sourceId + " required to enter " + targetId + ".");
      }
      return;
    }

    this.onStatus(
      "Incompatible connection: " + sourceType + "." + sourcePort +
      " → " + targetType + "." + targetPort
    );
  }

  _edgeData() {
    var edges = [];
    var selected = this.selected;
    var rooms = this.pkg.story.rooms;
    var connections = this.pkg.story.connections;

    Object.entries(connections).forEach(([id, connection]) => {
      var from = "room::" + connection.from;
      var exit = "exit::" + id;

      edges.push({
        from: from,
        fromPort: "exit",
        to: exit,
        toPort: "from",
        kind: "exit-link",
        label: connection.label || id,
        selected: selected === from || selected === exit
      });

      if (connection.skill_check) {
        edges.push({
          from: exit,
          fromPort: "skill",
          to: "skill::" + connection.skill_check,
          toPort: "challenge",
          kind: "skill-link",
          label: "check",
          selected: selected === exit || selected === "skill::" + connection.skill_check
        });
      } else if (connection.to && rooms[connection.to]) {
        edges.push({
          from: exit,
          fromPort: "target",
          to: "room::" + connection.to,
          toPort: "in",
          kind: "transition",
          label: "to " + (rooms[connection.to].name || connection.to),
          selected: selected === exit || selected === "room::" + connection.to
        });
      }
    });

    var users = {};
    Object.entries(connections).forEach(([id, connection]) => {
      if (connection.skill_check) {
        users[connection.skill_check] = users[connection.skill_check] || [];
        users[connection.skill_check].push(connection);
      }
    });

    Object.entries(this.pkg.skill_checks.skill_checks).forEach(([id, check]) => {
      var linked = users[id] || [];
      if (!linked.length) return;
      linked.forEach((connection) => {
        ["success", "failure"].forEach((branch) => {
          var outcome = check[branch] || {};
          var target = outcome.to || connection.to || connection.from;
          if (!rooms[target]) return;
          edges.push({
            from: "skill::" + id,
            fromPort: branch,
            to: "room::" + target,
            toPort: "in",
            kind: branch,
            label: branch,
            selected: selected === "skill::" + id || selected === "room::" + target
          });
        });
      });
    });

    Object.entries(this.pkg.inventory.room_items).forEach(([roomId, itemIds]) => {
      if (!Array.isArray(itemIds)) return;
      itemIds.forEach((itemId) => {
        if (!this.pkg.inventory.items[itemId]) return;
        edges.push({
          from: "item::" + itemId,
          fromPort: "item",
          to: "room::" + roomId,
          toPort: "pickup",
          kind: "contains",
          label: "pickup",
          selected: selected === "item::" + itemId || selected === "room::" + roomId
        });
      });
    });

    Object.entries(this.pkg.inventory.room_requirements).forEach(([roomId, itemId]) => {
      if (!this.pkg.inventory.items[itemId]) return;
      edges.push({
        from: "item::" + itemId,
        fromPort: "item",
        to: "room::" + roomId,
        toPort: "requirement",
        kind: "requirement",
        label: "requires",
        selected: selected === "item::" + itemId || selected === "room::" + roomId
      });
    });

    Object.entries(this.pkg.story.revisits).forEach(([roomId, data]) => {
      var entries = Array.isArray(data.entries) ? data.entries : [];
      entries.forEach((entry, index) => {
        edges.push({
          from: "room::" + roomId,
          fromPort: "exit",
          to: "revisit::" + roomId + "::" + index,
          toPort: "in",
          kind: "revisit",
          label: data.show_all ? "revisit · all" : "revisit",
          selected: selected === "room::" + roomId || selected === "revisit::" + roomId + "::" + index
        });
      });
    });

    if (this.pkg.story.start_room && rooms[this.pkg.story.start_room]) {
      edges.push({
        from: "world",
        fromPort: "start",
        to: "room::" + this.pkg.story.start_room,
        toPort: "in",
        kind: "start",
        label: "start",
        selected: selected === "room::" + this.pkg.story.start_room
      });
    }

    return edges;
  }

  _renderEdges() {
    if (!this.edges) return;
    var width = this.stage.clientWidth || 1;
    var height = this.stage.clientHeight || 1;
    this.edges.setAttribute("width", width);
    this.edges.setAttribute("height", height);
    this.edges.setAttribute("viewBox", "0 0 " + width + " " + height);

    var ns = "http://www.w3.org/2000/svg";
    this.edges.innerHTML =
      '<defs>' +
        '<marker id="graph-arrow" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto" markerUnits="strokeWidth">' +
          '<path d="M0,0 L10,5 L0,10 z"></path>' +
        "</marker>" +
      "</defs>";

    var nodeMap = new Map(
      Array.from(this.nodeLayer.children).map((element) => [element.dataset.nodeKey, element])
    );

    this._edgeData().forEach((edge) => {
      var sourceEl = nodeMap.get(edge.from);
      var targetEl = nodeMap.get(edge.to);
      if (!sourceEl || !targetEl) return;

      var a = this._portAnchor(sourceEl, edge.fromPort, "out");
      var b = this._portAnchor(targetEl, edge.toPort, "in");
      var same = edge.from === edge.to;
      var bend = Math.max(70, Math.abs(b.x - a.x) * 0.45);
      var d = same
        ? "M " + a.x + " " + a.y + " C " + (a.x + 90) + " " + (a.y - 85) + ", " +
          (b.x + 90) + " " + (b.y - 85) + ", " + b.x + " " + b.y
        : "M " + a.x + " " + a.y + " C " + (a.x + bend) + " " + a.y + ", " +
          (b.x - bend) + " " + b.y + ", " + b.x + " " + b.y;

      var path = document.createElementNS(ns, "path");
      path.setAttribute("d", d);
      path.setAttribute("class", "graph-edge graph-edge-" + edge.kind + (edge.selected ? " selected" : ""));
      path.setAttribute("marker-end", "url(#graph-arrow)");
      this.edges.appendChild(path);

      if (edge.label) {
        var label = document.createElementNS(ns, "text");
        label.setAttribute("x", (a.x + b.x) / 2);
        label.setAttribute("y", (a.y + b.y) / 2 - 7);
        label.setAttribute("class", "graph-edge-label");
        label.textContent = edge.label;
        this.edges.appendChild(label);
      }
    });

    if (this.connecting) {
      var sourceEl = nodeMap.get(this.connecting.nodeKey);
      if (sourceEl) {
        var start = this._portAnchor(sourceEl, this.connecting.port, "out");
        var rect = this.stage.getBoundingClientRect();
        var end = {
          x: (this.connecting.clientX - rect.left - this.panX) / this.scale,
          y: (this.connecting.clientY - rect.top - this.panY) / this.scale
        };
        var temp = document.createElementNS(ns, "path");
        temp.setAttribute(
          "d",
          "M " + start.x + " " + start.y +
          " C " + (start.x + 80) + " " + start.y + ", " +
          (end.x - 80) + " " + end.y + ", " + end.x + " " + end.y
        );
        temp.setAttribute("class", "graph-edge graph-edge-temp");
        temp.setAttribute("marker-end", "url(#graph-arrow)");
        this.edges.appendChild(temp);
      }
    }
  }

  _renderInspector() {
    this.inspector.innerHTML = "";
    var parts = this.selected.split("::");
    var type = parts[0];
    var id = parts[1];

    if (this.selected === "world") {
      this._worldInspector();
      return;
    }

    if (type === "room") this._roomInspector(id);
    else if (type === "exit") this._exitInspector(id);
    else if (type === "skill") this._skillInspector(id);
    else if (type === "item") this._itemInspector(id);
    else if (type === "revisit") this._revisitInspector(id, Number(parts[2]));
  }

  _worldInspector() {
    var story = this.pkg.story;
    this.inspector.innerHTML =
      '<div class="inspector-title"><h2>World</h2><p>Visual flow is the authoring surface over the narrative VM.</p></div>' +
      '<section class="inspector-section">' +
        '<label>World name<input data-field="world.name" value="' + esc(story.name) + '"></label>' +
        '<label>Start room<select data-field="world.start_room">' +
          Object.keys(story.rooms).map((roomId) =>
            '<option value="' + esc(roomId) + '"' + (roomId === story.start_room ? " selected" : "") + ">" + esc(roomId) + "</option>"
          ).join("") +
        '</select></label>' +
        '<label>Metadata JSON<textarea class="inspector-code" data-field="world.metadata">' +
          esc(JSON.stringify(
            Object.fromEntries(Object.entries(story.metadata).filter(([key]) => key !== "__editor_graph")),
            null,
            2
          )) +
        "</textarea></label>" +
        '<p class="inspector-note">The __editor_graph section is editor layout only and is ignored by the VM.</p>' +
      "</section>";
  }

  _roomInspector(roomId) {
    var room = this.pkg.story.rooms[roomId];
    if (!room) return;
    var itemIds = Object.keys(this.pkg.inventory.items);
    var placed = this.pkg.inventory.room_items[roomId] || [];
    var required = this.pkg.inventory.room_requirements[roomId] || "";
    var exits = Object.entries(this.pkg.story.connections).filter((entry) => entry[1].from === roomId);
    var revisits = this.pkg.story.revisits[roomId];
    var entries = revisits && Array.isArray(revisits.entries) ? revisits.entries : [];

    this.inspector.innerHTML =
      '<div class="inspector-title"><h2>Room</h2><p>' + esc(roomId) + "</p></div>" +
      '<section class="inspector-section">' +
        '<label>Room ID<input data-field="room.id" value="' + esc(roomId) + '"></label>' +
        '<button data-inspector-action="rename-room">Rename room</button>' +
        '<label>Display name<input data-field="room.name" value="' + esc(room.name || "") + '"></label>' +
        '<label>Description<textarea data-field="room.description">' + esc(room.description || "") + "</textarea></label>" +
        '<label>Image asset<input data-field="room.image" value="' + esc(room.image || "") + '" placeholder="assets/example.png"></label>' +
        '<label>Message<textarea data-field="room.message">' + esc(room.message || "") + "</textarea></label>" +
        '<label class="check-row"><input type="checkbox" data-field="room.show_map"' + (room.show_map ? " checked" : "") + '> Show map</label>' +
      "</section>" +
      '<section class="inspector-section"><h3>Exits from room</h3>' +
        (exits.length ? exits.map((entry) =>
          '<button class="linkish" data-inspector-action="select-node" data-node-key="exit::' + esc(entry[0]) + '">' +
            esc(entry[1].label || entry[0]) + " → " + esc(entry[1].to || "(unset)") +
          "</button>"
        ).join("") : '<p class="inspector-note">Drag the room output port to another room to create an exit.</p>') +
        '<button data-inspector-action="add-connection">+ Add exit</button>' +
      "</section>" +
      '<section class="inspector-section"><h3>Pickups</h3>' +
        (itemIds.length ? itemIds.map((itemId) =>
          '<label class="check-row"><input type="checkbox" data-item-placement="' + esc(itemId) + '"' +
          (placed.includes(itemId) ? " checked" : "") + "> " +
          esc(this.pkg.inventory.items[itemId].name || itemId) + "</label>"
        ).join("") : '<p class="inspector-note">Create an item and drag it to the room pickup port.</p>') +
      "</section>" +
      '<section class="inspector-section"><h3>Entry requirement</h3>' +
        '<select data-field="room.required_item"><option value="">None</option>' +
        itemIds.map((itemId) =>
          '<option value="' + esc(itemId) + '"' +
          (required === itemId ? " selected" : "") + ">" +
          esc(this.pkg.inventory.items[itemId].name || itemId) + "</option>"
        ).join("") +
        "</select>" +
      "</section>" +
      '<section class="inspector-section"><h3>Revisits</h3>' +
        '<label class="check-row"><input type="checkbox" data-field="room.revisit_show_all"' +
        (revisits && revisits.show_all ? " checked" : "") +
        "> Show all eligible entries</label>" +
        (entries.map((entry, index) =>
          '<div class="inspector-card"><div class="row-between"><strong>Entry ' + index + '</strong>' +
          '<button class="danger compact" data-inspector-action="delete-revisit" data-index="' + index + '">Delete</button></div>' +
          '<label>Visit count<input type="number" min="0" step="1" data-field="revisit.count" data-index="' + index + '" value="' + Number(entry.count || 0) + '"></label>' +
          '<label>Content<textarea data-field="revisit.content" data-index="' + index + '">' + esc(entry.content || "") + "</textarea></label></div>"
        ).join("")) +
        '<button data-inspector-action="add-revisit">+ Add revisit entry</button>' +
      "</section>" +
      '<button class="danger full-width" data-inspector-action="delete-room">Delete room</button>';

    this.inspector.querySelectorAll("[data-item-placement]").forEach((input) => {
      input.addEventListener("change", () => {
        var set = new Set(this.pkg.inventory.room_items[roomId] || []);
        if (input.checked) set.add(input.dataset.itemPlacement);
        else set.delete(input.dataset.itemPlacement);
        if (set.size) this.pkg.inventory.room_items[roomId] = Array.from(set);
        else delete this.pkg.inventory.room_items[roomId];
        this._changed("Updated pickup placement.");
      });
    });
  }

  _exitInspector(connectionId) {
    var connection = this.pkg.story.connections[connectionId];
    if (!connection) return;
    var rooms = Object.keys(this.pkg.story.rooms);
    var skillIds = Object.keys(this.pkg.skill_checks.skill_checks);
    var itemIds = Object.keys(this.pkg.inventory.items);

    this.inspector.innerHTML =
      '<div class="inspector-title"><h2>Exit</h2><p>' + esc(connectionId) + "</p></div>" +
      '<section class="inspector-section">' +
        '<label>Label<input data-field="connection.label" data-connection-id="' + esc(connectionId) + '" value="' + esc(connection.label || "") + '"></label>' +
        '<label>From<select data-field="connection.from" data-connection-id="' + esc(connectionId) + '">' +
          rooms.map((roomId) =>
            '<option value="' + esc(roomId) + '"' + (roomId === connection.from ? " selected" : "") + ">" + esc(roomId) + "</option>"
          ).join("") +
        '</select></label>' +
        '<label>Destination<select data-field="connection.to" data-connection-id="' + esc(connectionId) + '">' +
          rooms.map((roomId) =>
            '<option value="' + esc(roomId) + '"' + (roomId === connection.to ? " selected" : "") + ">" + esc(roomId) + "</option>"
          ).join("") +
        '</select></label>' +
        '<label>Skill check<select data-field="connection.skill_check" data-connection-id="' + esc(connectionId) + '">' +
          '<option value="">None</option>' +
          skillIds.map((skillId) =>
            '<option value="' + esc(skillId) + '"' + (skillId === connection.skill_check ? " selected" : "") + ">" + esc(skillId) + "</option>"
          ).join("") +
        '</select></label>' +
        '<label>Required item<select data-field="connection.requires_item" data-connection-id="' + esc(connectionId) + '">' +
          '<option value="">None</option>' +
          itemIds.map((itemId) =>
            '<option value="' + esc(itemId) + '"' + (itemId === connection.requires_item ? " selected" : "") + ">" +
            esc(this.pkg.inventory.items[itemId].name || itemId) + "</option>"
          ).join("") +
        '</select></label>' +
      "</section>" +
      '<p class="inspector-note">Wire Exit → Room to change the destination, or Exit → Skill Check to attach a check.</p>' +
      '<button class="danger full-width" data-inspector-action="delete-connection">Delete exit</button>';
  }

  _skillInspector(skillId) {
    var check = this.pkg.skill_checks.skill_checks[skillId];
    if (!check) return;
    var outcome = function(branch) { return check[branch] || {}; };

    this.inspector.innerHTML =
      '<div class="inspector-title"><h2>Skill Check</h2><p>' + esc(skillId) + "</p></div>" +
      '<section class="inspector-section">' +
        '<label>Skill ID<input data-field="skill.id" value="' + esc(skillId) + '"></label>' +
        '<button data-inspector-action="rename-skill">Rename skill check</button>' +
        '<label>Description<textarea data-field="skill.description">' + esc(check.description || "") + "</textarea></label>" +
        '<label>Dice expression<input data-field="skill.dice_type" value="' + esc(check.dice_type || "1d20") + '"></label>' +
        '<label>Target<input type="number" step="1" data-field="skill.target" value="' + Number(check.target == null ? 10 : check.target) + '"></label>' +
      "</section>" +
      ["success", "failure"].map((branch) =>
        '<section class="inspector-section"><h3>' + branch[0].toUpperCase() + branch.slice(1) + "</h3>" +
          '<label>Description<textarea data-field="skill.' + branch + '.description">' + esc(outcome(branch).description || "") + "</textarea></label>" +
          '<label>Destination<select data-field="skill.' + branch + '.to">' +
            '<option value="">Use exit fallback</option>' +
            Object.keys(this.pkg.story.rooms).map((roomId) =>
              '<option value="' + esc(roomId) + '"' +
              (roomId === outcome(branch).to ? " selected" : "") + ">" + esc(roomId) + "</option>"
            ).join("") +
          "</select></label>" +
        "</section>"
      ).join("") +
      '<p class="inspector-note">Wire the green Success port or red Failure port to a room to author the branch visually.</p>' +
      '<button class="danger full-width" data-inspector-action="delete-skill">Delete skill check</button>';
  }

  _itemInspector(itemId) {
    var item = this.pkg.inventory.items[itemId];
    if (!item) return;
    var rooms = Object.keys(this.pkg.story.rooms);

    this.inspector.innerHTML =
      '<div class="inspector-title"><h2>Pickup</h2><p>' + esc(itemId) + "</p></div>" +
      '<section class="inspector-section">' +
        '<label>Item ID<input data-field="item.id" value="' + esc(itemId) + '"></label>' +
        '<button data-inspector-action="rename-item">Rename pickup</button>' +
        '<label>Name<input data-field="item.name" value="' + esc(item.name || "") + '"></label>' +
      "</section>" +
      '<section class="inspector-section"><h3>Placed in rooms</h3>' +
        rooms.map((roomId) =>
          '<label class="check-row"><input type="checkbox" data-item-room="' + esc(roomId) + '"' +
          ((this.pkg.inventory.room_items[roomId] || []).includes(itemId) ? " checked" : "") + "> " +
          esc(this.pkg.story.rooms[roomId].name || roomId) + "</label>"
        ).join("") +
      "</section>" +
      '<section class="inspector-section"><h3>Required to enter</h3>' +
        rooms.map((roomId) =>
          '<label class="check-row"><input type="checkbox" data-item-requirement-room="' + esc(roomId) + '"' +
          (this.pkg.inventory.room_requirements[roomId] === itemId ? " checked" : "") + "> " +
          esc(this.pkg.story.rooms[roomId].name || roomId) + "</label>"
        ).join("") +
      "</section>" +
      '<button class="danger full-width" data-inspector-action="delete-item">Delete pickup</button>';

    this.inspector.querySelectorAll("[data-item-room]").forEach((input) => {
      input.addEventListener("change", () => {
        var roomId = input.dataset.itemRoom;
        var set = new Set(this.pkg.inventory.room_items[roomId] || []);
        if (input.checked) set.add(itemId);
        else set.delete(itemId);
        if (set.size) this.pkg.inventory.room_items[roomId] = Array.from(set);
        else delete this.pkg.inventory.room_items[roomId];
        this._changed("Updated pickup placement.");
      });
    });

    this.inspector.querySelectorAll("[data-item-requirement-room]").forEach((input) => {
      input.addEventListener("change", () => {
        var roomId = input.dataset.itemRequirementRoom;
        if (input.checked) this.pkg.inventory.room_requirements[roomId] = itemId;
        else if (this.pkg.inventory.room_requirements[roomId] === itemId) delete this.pkg.inventory.room_requirements[roomId];
        this._changed("Updated room requirement.");
      });
    });
  }

  _revisitInspector(roomId, index) {
    var data = this.pkg.story.revisits[roomId];
    var entry = data && data.entries && data.entries[index];
    if (!entry) return;
    this.inspector.innerHTML =
      '<div class="inspector-title"><h2>Revisit</h2><p>' + esc(roomId) + " · entry " + index + "</p></div>" +
      '<section class="inspector-section">' +
        '<label>Visit count<input type="number" min="0" step="1" data-field="revisit.count" value="' + Number(entry.count || 0) + '"></label>' +
        '<label>Content<textarea data-field="revisit.content">' + esc(entry.content || "") + "</textarea></label>" +
        '<label class="check-row"><input type="checkbox" data-field="revisit.show_all"' + (data.show_all ? " checked" : "") + '> Show all eligible entries</label>' +
      "</section>" +
      '<button class="linkish" data-inspector-action="select-node" data-node-key="room::' + esc(roomId) + '">Edit room</button>' +
      '<button class="danger full-width" data-inspector-action="delete-revisit">Delete revisit entry</button>';
  }

  _fieldChanged(field) {
    var name = field.dataset.field;
    var value = field.type === "checkbox" ? field.checked : field.value;
    var parts = name.split(".");
    var domain = parts.shift();

    try {
      if (domain === "world") this._setWorldField(parts, value);
      if (domain === "room") this._setRoomField(this._selectedId(), parts, value);
      if (domain === "connection") this._setConnectionField(field.dataset.connectionId || this._selectedId(), parts, value);
      if (domain === "skill") this._setSkillField(this._selectedId(), parts, value);
      if (domain === "item") this._setItemField(this._selectedId(), parts, value);
      if (domain === "revisit") this._setRevisitField(this._selectedId(), this._selectedRevisitIndex(), parts, value);
      this._changed("Graph data updated.");
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
      var graph = this.pkg.story.metadata.__editor_graph;
      var parsed = JSON.parse(String(value) || "{}");
      this.pkg.story.metadata = parsed;
      this.pkg.story.metadata.__editor_graph = graph;
    }
  }

  _setRoomField(roomId, parts, value) {
    var room = this.pkg.story.rooms[roomId];
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
      this.pkg.story.revisits[roomId] = this.pkg.story.revisits[roomId] || {
        show_all: false,
        entries: []
      };
      this.pkg.story.revisits[roomId].show_all = !!value;
      if (!value && !this.pkg.story.revisits[roomId].entries.length) delete this.pkg.story.revisits[roomId];
    }
  }

  _setConnectionField(id, parts, value) {
    var connection = this.pkg.story.connections[id];
    if (!connection) return;
    if (parts[0] === "label") connection.label = String(value);
    if (parts[0] === "from") connection.from = String(value);
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
    var check = this.pkg.skill_checks.skill_checks[skillId];
    if (!check) return;
    if (parts[0] === "description") check.description = String(value);
    if (parts[0] === "dice_type") check.dice_type = String(value);
    if (parts[0] === "target") check.target = Number(value);
    if (parts[0] === "success" || parts[0] === "failure") {
      check[parts[0]] = check[parts[0]] || {};
      if (parts[1] === "description") check[parts[0]].description = String(value);
      if (parts[1] === "to") {
        if (String(value)) check[parts[0]].to = String(value);
        else delete check[parts[0]].to;
      }
    }
  }

  _setItemField(itemId, parts, value) {
    var item = this.pkg.inventory.items[itemId];
    if (!item) return;
    if (parts[0] === "name") item.name = String(value);
  }

  _setRevisitField(roomId, index, parts, value) {
    var data = this.pkg.story.revisits[roomId];
    if (!data || !data.entries[index]) return;
    if (parts[0] === "count") data.entries[index].count = Number(value);
    if (parts[0] === "content") data.entries[index].content = String(value);
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
      if (action === "delete-connection") this._deleteConnection(data.connectionId || this._selectedId());
      if (action === "delete-skill") this._deleteSkill(this._selectedId());
      if (action === "delete-item") this._deleteItem(this._selectedId());
      if (action === "add-connection") this._addConnection(this._selectedId());
      if (action === "add-revisit") this._addRevisit(this._selectedId());
      if (action === "delete-revisit") {
        this._deleteRevisit(this._selectedId(), data.index == null ? this._selectedRevisitIndex() : Number(data.index));
      }
    } catch (error) {
      this.onStatus(error instanceof Error ? error.message : String(error));
    }
  }

  _renameRoom(oldId) {
    var input = this.inspector.querySelector('[data-field="room.id"]');
    var newId = input ? input.value.trim() : oldId;
    if (!newId || newId === oldId) return;
    if (!/^[A-Za-z0-9_-]+$/.test(newId)) throw new Error("Room IDs may use letters, numbers, '_' and '-'.");
    if (this.pkg.story.rooms[newId]) throw new Error("Room " + newId + " already exists.");

    this.pkg.story.rooms[newId] = this.pkg.story.rooms[oldId];
    delete this.pkg.story.rooms[oldId];
    if (this.pkg.story.start_room === oldId) this.pkg.story.start_room = newId;

    Object.values(this.pkg.story.connections).forEach((connection) => {
      if (connection.from === oldId) connection.from = newId;
      if (connection.to === oldId) connection.to = newId;
    });
    Object.values(this.pkg.skill_checks.skill_checks).forEach((check) => {
      ["success", "failure"].forEach((branch) => {
        if (check[branch] && check[branch].to === oldId) check[branch].to = newId;
      });
    });

    if (this.pkg.story.revisits[oldId]) {
      this.pkg.story.revisits[newId] = this.pkg.story.revisits[oldId];
      delete this.pkg.story.revisits[oldId];
    }
    if (this.pkg.inventory.room_items[oldId]) {
      this.pkg.inventory.room_items[newId] = this.pkg.inventory.room_items[oldId];
      delete this.pkg.inventory.room_items[oldId];
    }
    if (this.pkg.inventory.room_requirements[oldId]) {
      this.pkg.inventory.room_requirements[newId] = this.pkg.inventory.room_requirements[oldId];
      delete this.pkg.inventory.room_requirements[oldId];
    }

    this._movePosition("room::" + oldId, "room::" + newId);
    Object.keys(this.positions).forEach((key) => {
      if (key.indexOf("revisit::" + oldId + "::") === 0) {
        this._movePosition(key, key.replace("revisit::" + oldId + "::", "revisit::" + newId + "::"));
      }
    });

    this.selected = "room::" + newId;
    this._changed("Renamed room to " + newId + ".");
  }

  _renameSkill(oldId) {
    var input = this.inspector.querySelector('[data-field="skill.id"]');
    var newId = input ? input.value.trim() : oldId;
    if (!newId || newId === oldId) return;
    if (!/^[A-Za-z0-9_-]+$/.test(newId)) throw new Error("Skill IDs may use letters, numbers, '_' and '-'.");
    if (this.pkg.skill_checks.skill_checks[newId]) throw new Error("Skill check " + newId + " already exists.");

    this.pkg.skill_checks.skill_checks[newId] = this.pkg.skill_checks.skill_checks[oldId];
    delete this.pkg.skill_checks.skill_checks[oldId];
    Object.values(this.pkg.story.connections).forEach((connection) => {
      if (connection.skill_check === oldId) connection.skill_check = newId;
    });
    this._movePosition("skill::" + oldId, "skill::" + newId);
    this.selected = "skill::" + newId;
    this._changed("Renamed skill check to " + newId + ".");
  }

  _renameItem(oldId) {
    var input = this.inspector.querySelector('[data-field="item.id"]');
    var newId = input ? input.value.trim() : oldId;
    if (!newId || newId === oldId) return;
    if (!/^[A-Za-z0-9_-]+$/.test(newId)) throw new Error("Item IDs may use letters, numbers, '_' and '-'.");
    if (this.pkg.inventory.items[newId]) throw new Error("Item " + newId + " already exists.");

    this.pkg.inventory.items[newId] = this.pkg.inventory.items[oldId];
    delete this.pkg.inventory.items[oldId];

    Object.keys(this.pkg.inventory.room_items).forEach((roomId) => {
      this.pkg.inventory.room_items[roomId] = this.pkg.inventory.room_items[roomId]
        .map((id) => id === oldId ? newId : id);
    });
    Object.keys(this.pkg.inventory.room_requirements).forEach((roomId) => {
      if (this.pkg.inventory.room_requirements[roomId] === oldId) {
        this.pkg.inventory.room_requirements[roomId] = newId;
      }
    });
    Object.values(this.pkg.story.connections).forEach((connection) => {
      if (connection.requires_item === oldId) connection.requires_item = newId;
    });

    this._movePosition("item::" + oldId, "item::" + newId);
    this.selected = "item::" + newId;
    this._changed("Renamed pickup to " + newId + ".");
  }

  _movePosition(oldKey, newKey) {
    if (this.positions[oldKey]) {
      this.positions[newKey] = this.positions[oldKey];
      delete this.positions[oldKey];
    }
  }

  _deleteSelected() {
    var parts = this.selected.split("::");
    if (parts[0] === "room") this._deleteRoom(parts[1]);
    else if (parts[0] === "exit") this._deleteConnection(parts[1]);
    else if (parts[0] === "skill") this._deleteSkill(parts[1]);
    else if (parts[0] === "item") this._deleteItem(parts[1]);
    else if (parts[0] === "revisit") this._deleteRevisit(parts[1], Number(parts[2]));
  }

  _deleteRoom(roomId) {
    if (this.pkg.story.start_room === roomId) throw new Error("Move the start room before deleting it.");
    delete this.pkg.story.rooms[roomId];

    Object.keys(this.pkg.story.connections).forEach((id) => {
      var connection = this.pkg.story.connections[id];
      if (connection.from === roomId || connection.to === roomId) {
        delete this.pkg.story.connections[id];
        delete this.positions["exit::" + id];
      }
    });

    delete this.pkg.story.revisits[roomId];
    delete this.pkg.inventory.room_items[roomId];
    delete this.pkg.inventory.room_requirements[roomId];

    Object.values(this.pkg.skill_checks.skill_checks).forEach((check) => {
      ["success", "failure"].forEach((branch) => {
        if (check[branch] && check[branch].to === roomId) delete check[branch].to;
      });
    });

    delete this.positions["room::" + roomId];
    Object.keys(this.positions).forEach((key) => {
      if (key.indexOf("revisit::" + roomId + "::") === 0) delete this.positions[key];
    });

    this.selected = "world";
    this._changed("Deleted room " + roomId + ".");
  }

  _deleteConnection(connectionId) {
    delete this.pkg.story.connections[connectionId];
    delete this.positions["exit::" + connectionId];
    this.selected = "world";
    this._changed("Deleted exit.");
  }

  _deleteSkill(skillId) {
    delete this.pkg.skill_checks.skill_checks[skillId];
    Object.values(this.pkg.story.connections).forEach((connection) => {
      if (connection.skill_check === skillId) delete connection.skill_check;
    });
    delete this.positions["skill::" + skillId];
    this.selected = "world";
    this._changed("Deleted skill check.");
  }

  _deleteItem(itemId) {
    delete this.pkg.inventory.items[itemId];
    Object.keys(this.pkg.inventory.room_items).forEach((roomId) => {
      this.pkg.inventory.room_items[roomId] =
        this.pkg.inventory.room_items[roomId].filter((id) => id !== itemId);
      if (!this.pkg.inventory.room_items[roomId].length) delete this.pkg.inventory.room_items[roomId];
    });
    Object.keys(this.pkg.inventory.room_requirements).forEach((roomId) => {
      if (this.pkg.inventory.room_requirements[roomId] === itemId) delete this.pkg.inventory.room_requirements[roomId];
    });
    Object.values(this.pkg.story.connections).forEach((connection) => {
      if (connection.requires_item === itemId) delete connection.requires_item;
    });
    delete this.positions["item::" + itemId];
    this.selected = "world";
    this._changed("Deleted pickup.");
  }

  _deleteRevisit(roomId, index) {
    var data = this.pkg.story.revisits[roomId];
    if (!data || !data.entries[index]) return;
    data.entries.splice(index, 1);
    if (!data.entries.length) delete this.pkg.story.revisits[roomId];

    Object.keys(this.positions).forEach((key) => {
      if (key.indexOf("revisit::" + roomId + "::") !== 0) return;
      var oldIndex = Number(key.split("::")[2]);
      if (oldIndex === index) delete this.positions[key];
      else if (oldIndex > index) this._movePosition(key, "revisit::" + roomId + "::" + (oldIndex - 1));
    });

    this.selected = "room::" + roomId;
    this._changed("Deleted revisit entry.");
  }

  _createConnection(fromRoom, toRoom, skillId) {
    var existing = new Set(Object.keys(this.pkg.story.connections));
    var base = fromRoom + "__new_exit";
    var id = base;
    var n = 2;
    while (existing.has(id)) id = base + "_" + n++;

    this.pkg.story.connections[id] = {
      from: fromRoom,
      to: toRoom,
      label: skillId ? "Skill exit" : "New exit"
    };
    if (skillId) this.pkg.story.connections[id].skill_check = skillId;

    var from = this.positions["room::" + fromRoom] || {x: 100, y: 100};
    var to = this.positions["room::" + toRoom] || {x: from.x + 320, y: from.y};
    this.positions["exit::" + id] = {
      x: (from.x + to.x) / 2,
      y: (from.y + to.y) / 2
    };
    return id;
  }

  _addConnection(roomId) {
    var id = this._createConnection(roomId, this._fallbackRoom(roomId), null);
    this.selected = "exit::" + id;
    this._changed("Added exit.");
  }

  _addRoom() {
    var rooms = this.pkg.story.rooms;
    var id = "room_1";
    var n = 1;
    while (rooms[id]) id = "room_" + (++n);
    rooms[id] = {description: "New room.", show_map: true};
    this.positions["room::" + id] = {x: 100, y: 300 + Object.keys(rooms).length * 80};
    if (!this.pkg.story.start_room) this.pkg.story.start_room = id;
    this.selected = "room::" + id;
    this._changed("Added room " + id + ".");
  }

  _addSkill() {
    var checks = this.pkg.skill_checks.skill_checks;
    var id = "skill_1";
    var n = 1;
    while (checks[id]) id = "skill_" + (++n);
    checks[id] = {
      dice_type: "1d20",
      target: 10,
      description: "Describe the challenge.",
      success: {description: "Success.", to: ""},
      failure: {description: "Failure.", to: ""}
    };
    this.positions["skill::" + id] = {x: 620, y: 360 + Object.keys(checks).length * 80};
    this.selected = "skill::" + id;
    this._changed("Added skill check " + id + ".");
  }

  _addItem() {
    var items = this.pkg.inventory.items;
    var id = "item_1";
    var n = 1;
    while (items[id]) id = "item_" + (++n);
    items[id] = {name: "New pickup"};
    this.positions["item::" + id] = {x: 900, y: 360 + Object.keys(items).length * 80};
    this.selected = "item::" + id;
    this._changed("Added pickup " + id + ".");
  }

  _addRevisit(roomId) {
    if (!roomId) throw new Error("Select a room before adding a revisit entry.");
    this.pkg.story.revisits[roomId] = this.pkg.story.revisits[roomId] || {
      show_all: false,
      entries: []
    };
    this.pkg.story.revisits[roomId].entries.push({
      count: 1,
      content: "You have been here before."
    });
    var index = this.pkg.story.revisits[roomId].entries.length - 1;
    this.positions["revisit::" + roomId + "::" + index] = {
      x: (this.positions["room::" + roomId] || {x: 100, y: 100}).x + 260,
      y: (this.positions["room::" + roomId] || {x: 100, y: 100}).y + 150
    };
    this.selected = "revisit::" + roomId + "::" + index;
    this._changed("Added revisit entry.");
  }

  _fallbackRoom(sourceRoom) {
    var rooms = Object.keys(this.pkg.story.rooms);
    return rooms.find((id) => id !== sourceRoom) || sourceRoom;
  }

  _autoLayout() {
    var roomIds = Object.keys(this.pkg.story.rooms);
    var depth = {};
    var queue = [];
    var start = this.pkg.story.start_room;
    if (start && this.pkg.story.rooms[start]) {
      depth[start] = 0;
      queue.push(start);
    }

    while (queue.length) {
      var roomId = queue.shift();
      var d = depth[roomId];
      Object.values(this.pkg.story.connections).forEach((connection) => {
        if (connection.from !== roomId) return;
        var targets = [];
        if (connection.to && this.pkg.story.rooms[connection.to]) targets.push(connection.to);
        if (connection.skill_check) {
          var check = this.pkg.skill_checks.skill_checks[connection.skill_check] || {};
          ["success", "failure"].forEach((branch) => {
            if (check[branch] && check[branch].to && this.pkg.story.rooms[check[branch].to]) {
              targets.push(check[branch].to);
            }
          });
        }
        targets.forEach((target) => {
          if (depth[target] == null) {
            depth[target] = d + 1;
            queue.push(target);
          }
        });
      });
    }

    roomIds.forEach((roomId, index) => {
      if (depth[roomId] == null) depth[roomId] = 0;
    });

    var byDepth = {};
    roomIds.forEach((roomId) => {
      byDepth[depth[roomId]] = byDepth[depth[roomId]] || [];
      byDepth[depth[roomId]].push(roomId);
    });

    Object.entries(byDepth).forEach(([d, ids]) => {
      ids.forEach((roomId, index) => {
        this.positions["room::" + roomId] = {
          x: 80 + Number(d) * 360,
          y: 100 + index * 250
        };
      });
    });

    Object.entries(this.pkg.story.connections).forEach(([id, connection]) => {
      var from = this.positions["room::" + connection.from] || {x: 80, y: 100};
      var targets = [];
      if (connection.to && this.positions["room::" + connection.to]) targets.push(this.positions["room::" + connection.to]);
      if (!targets.length) targets.push({x: from.x + 300, y: from.y});
      this.positions["exit::" + id] = {
        x: (from.x + targets[0].x) / 2,
        y: (from.y + targets[0].y) / 2
      };
    });

    var skillIndex = 0;
    Object.keys(this.pkg.skill_checks.skill_checks).forEach((skillId) => {
      var users = Object.values(this.pkg.story.connections).filter((connection) => connection.skill_check === skillId);
      var first = users[0];
      var base = first ? this.positions["exit::" + Object.keys(this.pkg.story.connections).find((id) => this.pkg.story.connections[id] === first)] : null;
      this.positions["skill::" + skillId] = {
        x: base ? base.x + 30 : 620,
        y: base ? base.y + 130 + skillIndex * 20 : 260 + skillIndex * 180
      };
      skillIndex++;
    });

    Object.keys(this.pkg.inventory.items).forEach((itemId, index) => {
      var rooms = Object.entries(this.pkg.inventory.room_items).filter((entry) => entry[1].includes(itemId));
      var base = rooms.length ? this.positions["room::" + rooms[0][0]] : {x: 900, y: 100};
      this.positions["item::" + itemId] = {
        x: base.x,
        y: base.y + 170 + index * 50
      };
    });

    this._changed("Flow auto-layout complete.");
    this._fit();
  }

  _fit() {
    var nodes = this._nodeData();
    if (!nodes.length) return;
    var minX = Infinity;
    var minY = Infinity;
    var maxX = -Infinity;
    var maxY = -Infinity;

    nodes.forEach((node, index) => {
      var pos = this._positionFor(node, index);
      minX = Math.min(minX, pos.x);
      minY = Math.min(minY, pos.y);
      maxX = Math.max(maxX, pos.x + 240);
      maxY = Math.max(maxY, pos.y + 160);
    });

    var width = Math.max(1, maxX - minX);
    var height = Math.max(1, maxY - minY);
    var sx = this.stage.clientWidth / (width + 100);
    var sy = this.stage.clientHeight / (height + 100);
    this.scale = Math.max(0.35, Math.min(1.5, sx, sy));
    this.panX = (this.stage.clientWidth - width * this.scale) / 2 - minX * this.scale;
    this.panY = (this.stage.clientHeight - height * this.scale) / 2 - minY * this.scale;
    this._applyViewport();
  }

  _zoomAtCenter(multiplier) {
    var rect = this.stage.getBoundingClientRect();
    var sx = rect.width / 2;
    var sy = rect.height / 2;
    var wx = (sx - this.panX) / this.scale;
    var wy = (sy - this.panY) / this.scale;
    this.scale = Math.max(0.35, Math.min(2.25, this.scale * multiplier));
    this.panX = sx - wx * this.scale;
    this.panY = sy - wy * this.scale;
    this._applyViewport();
  }

  _action(action) {
    try {
      if (action === "add-room") this._addRoom();
      if (action === "add-exit") {
        if (!this.selected.startsWith("room::")) throw new Error("Select a room before adding an exit.");
        this._addConnection(this._selectedId());
      }
      if (action === "add-skill") this._addSkill();
      if (action === "add-item") this._addItem();
      if (action === "add-revisit") {
        if (!this.selected.startsWith("room::")) throw new Error("Select a room before adding a revisit.");
        this._addRevisit(this._selectedId());
      }
      if (action === "auto-layout") this._autoLayout();
      if (action === "fit") this._fit();
      if (action === "zoom-in") this._zoomAtCenter(1.15);
      if (action === "zoom-out") this._zoomAtCenter(0.87);
      if (action === "zoom-reset") {
        this.scale = 1;
        this.panX = 30;
        this.panY = 30;
        this._applyViewport();
      }
    } catch (error) {
      this.onStatus(error instanceof Error ? error.message : String(error));
    }
  }

  _changed(status) {
    this._ensureShape();
    this._renderNodes();
    this._renderInspector();
    this._renderEdges();
    this.onChange(this.pkg);
    this.onStatus(status);
  }

  _persistPositions() {
    this._ensureShape();
    this.onChange(this.pkg);
  }
}

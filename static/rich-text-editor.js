const esc = (value) =>
  String(value == null ? "" : value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");

const ALLOWED_TAGS = new Set([
  "P", "BR", "STRONG", "B", "EM", "I", "U",
  "H1", "H2", "H3", "UL", "OL", "LI",
  "BLOCKQUOTE", "SPAN", "DIV", "IMG", "A"
]);

const ALLOWED_STYLE = new Set([
  "font-weight", "font-style", "text-decoration", "text-align",
  "color", "background-color", "margin-left", "margin-top",
  "width", "height"
]);

function cleanStyle(value) {
  const parts = [];
  for (const declaration of String(value || "").split(";")) {
    const index = declaration.indexOf(":");
    if (index < 0) continue;
    const property = declaration.slice(0, index).trim().toLowerCase();
    const cssValue = declaration.slice(index + 1).trim();
    if (!ALLOWED_STYLE.has(property)) continue;
    if (/url\s*\(|expression\s*\(|javascript:/i.test(cssValue)) continue;
    if (!/^[#(),.%\-+\w\s]+$/.test(cssValue)) continue;
    parts.push(property + ": " + cssValue);
  }
  return parts.join("; ");
}

export function sanitizeRichHtml(html, resolveAsset) {
  const parser = new DOMParser();
  const documentNode = parser.parseFromString(
    String(html || ""),
    "text/html"
  );
  const walk = (node) => {
    for (const child of Array.from(node.childNodes)) {
      if (child.nodeType === Node.TEXT_NODE) continue;
      if (child.nodeType !== Node.ELEMENT_NODE) {
        child.remove();
        continue;
      }

      const tag = child.tagName;
      if (!ALLOWED_TAGS.has(tag)) {
        const fragment = documentNode.createDocumentFragment();
        while (child.firstChild) fragment.appendChild(child.firstChild);
        child.replaceWith(fragment);
        continue;
      }

      for (const attribute of Array.from(child.attributes)) {
        const name = attribute.name.toLowerCase();
        if (name.startsWith("on") || name === "srcdoc") {
          child.removeAttribute(attribute.name);
          continue;
        }
        if (name === "style") {
          const cleaned = cleanStyle(attribute.value);
          if (cleaned) child.setAttribute("style", cleaned);
          else child.removeAttribute("style");
          continue;
        }
        if (tag === "IMG" && name === "src") {
          const source = attribute.value;
          if (source.startsWith("data:image/")) {
            continue;
          }
          if (source.startsWith("assets/")) {
            child.setAttribute("src", resolveAsset(source));
            continue;
          }
          if (
            source.startsWith("/api/world/") ||
            source.startsWith("https://") ||
            source.startsWith("http://")
          ) {
            continue;
          }
          child.removeAttribute("src");
          continue;
        }
        if (tag === "IMG" && !["src", "alt"].includes(name)) {
          child.removeAttribute(attribute.name);
          continue;
        }
        if (tag === "A" && name === "href") {
          if (!/^(https?:|mailto:)/i.test(attribute.value)) {
            child.removeAttribute(attribute.name);
          }
          continue;
        }
        if (!(name === "href" || name === "target" || name === "rel" ||
              name === "alt")) {
          child.removeAttribute(attribute.name);
        }
      }

      if (tag === "A") {
        child.setAttribute("target", "_blank");
        child.setAttribute("rel", "noopener noreferrer");
      }
      walk(child);
    }
  };
  walk(documentNode.body);
  return documentNode.body.innerHTML;
}

function plainTextFromHtml(html) {
  const node = document.createElement("div");
  node.innerHTML = html;
  return node.innerText.replace(/\u00a0/g, " ").trim();
}

export class RichTextEditor {
  constructor(options) {
    this.assets = options.assets || {};
    this.resolveAsset = options.resolveAsset;
    this.onSave = options.onSave;
    this.onStatus = options.onStatus || (() => {});
    this.overlay = null;
    this.panel = null;
    this.editor = null;
    this.origin = null;
    this.selectedImage = null;
    this.dragImage = null;
  }

  open({roomId, room, originElement}) {
    this.close(false);
    this.origin = originElement || null;

    const overlay = document.createElement("div");
    overlay.className = "rich-editor-overlay";
    overlay.innerHTML =
      '<div class="rich-editor-backdrop"></div>' +
      '<section class="rich-editor-panel" role="dialog" aria-modal="true" aria-label="Description editor">' +
        '<header class="rich-editor-header">' +
          '<div><div class="rich-editor-kicker">ROOM DESCRIPTION</div>' +
          '<h2>' + esc(room.name || roomId) + '</h2></div>' +
          '<button class="rich-editor-close" data-rte-action="cancel" aria-label="Close">×</button>' +
        '</header>' +
        '<div class="rich-editor-toolbar">' +
          '<button data-command="bold"><strong>B</strong></button>' +
          '<button data-command="italic"><em>I</em></button>' +
          '<button data-command="underline"><u>U</u></button>' +
          '<span class="rte-divider"></span>' +
          '<button data-command="formatBlock" data-value="p">P</button>' +
          '<button data-command="formatBlock" data-value="h2">H2</button>' +
          '<button data-command="formatBlock" data-value="h3">H3</button>' +
          '<button data-command="formatBlock" data-value="blockquote">❝</button>' +
          '<button data-command="insertUnorderedList">• List</button>' +
          '<button data-command="insertOrderedList">1. List</button>' +
          '<button data-command="justifyLeft">Left</button>' +
          '<button data-command="justifyCenter">Center</button>' +
          '<span class="rte-divider"></span>' +
          '<label class="rte-color">Text <input type="color" data-rte-color="foreColor" value="#f5f7fb"></label>' +
          '<label class="rte-color">Highlight <input type="color" data-rte-color="hiliteColor" value="#39445a"></label>' +
          '<button data-rte-action="insert-image">＋ Image</button>' +
          '<input type="file" accept="image/*" data-rte-file hidden>' +
          '<span class="rte-toolbar-spacer"></span>' +
          '<button class="rte-save" data-rte-action="save">Save description</button>' +
        '</div>' +
        '<div class="rich-editor-hint">Drag images to move them. Drag the lower-right handle to resize. Formatting is saved with the room.</div>' +
        '<div class="rich-editor-workspace">' +
          '<div class="rich-editor-content" contenteditable="true" spellcheck="true"></div>' +
        '</div>' +
        '<footer class="rich-editor-footer">' +
          '<span data-rte-status>Editing ' + esc(roomId) + '</span>' +
          '<span>Esc cancels · Ctrl+Enter saves</span>' +
        '</footer>' +
      '</section>';

    document.body.appendChild(overlay);
    this.overlay = overlay;
    this.panel = overlay.querySelector(".rich-editor-panel");
    this.editor = overlay.querySelector(".rich-editor-content");

    this.editor.innerHTML = sanitizeRichHtml(
      room.description_html || room.description || "",
      this.resolveAsset
    );
    this.editor.querySelectorAll("img").forEach((image) => {
      image.classList.add("rte-image");
    });

    this._bind();
    this._animateOpen();
    this.editor.focus();
  }

  _bind() {
    this.overlay.addEventListener("click", (event) => {
      const action = event.target.closest("[data-rte-action]");
      if (!action) return;
      const name = action.dataset.rteAction;
      if (name === "insert-image") {
        this.overlay.querySelector("[data-rte-file]").click();
      } else if (name === "save") {
        this.save();
      } else if (name === "cancel") {
        this.close(true);
      }
    });

    this.overlay.addEventListener("input", (event) => {
      if (event.target.matches("[data-rte-color]")) {
        this._exec(event.target.dataset.rteColor, event.target.value);
      }
    });

    this.overlay.addEventListener("change", (event) => {
      if (event.target.matches("[data-rte-color]")) {
        this._exec(event.target.dataset.rteColor, event.target.value);
        this.editor.focus();
      }
      if (event.target.matches("[data-rte-file]")) {
        this._insertSelectedImage(event.target.files[0]);
        event.target.value = "";
      }
    });

    this.overlay.addEventListener("mousedown", (event) => {
      const button = event.target.closest("[data-command]");
      if (!button) return;
      event.preventDefault();
      this.editor.focus();
      this._exec(button.dataset.command, button.dataset.value);
    });

    this.editor.addEventListener("click", (event) => {
      const image = event.target.closest(".rte-image");
      if (!image) {
        this._clearImageSelection();
        return;
      }
      event.preventDefault();
      this._selectImage(image);
    });

    this.editor.addEventListener("pointerdown", (event) => {
      const image = event.target.closest(".rte-image");
      if (!image) return;
      event.preventDefault();
      event.stopPropagation();
      this._selectImage(image);
      this.dragImage = {
        image,
        startX: event.clientX,
        startY: event.clientY,
        marginLeft: parseFloat(image.style.marginLeft) || 0,
        marginTop: parseFloat(image.style.marginTop) || 0
      };
      image.setPointerCapture(event.pointerId);
    });

    this.editor.addEventListener("pointermove", (event) => {
      if (!this.dragImage) return;
      const drag = this.dragImage;
      const dx = event.clientX - drag.startX;
      const dy = event.clientY - drag.startY;
      drag.image.style.marginLeft = Math.round(drag.marginLeft + dx) + "px";
      drag.image.style.marginTop = Math.round(drag.marginTop + dy) + "px";
    });

    this.editor.addEventListener("pointerup", (event) => {
      if (!this.dragImage) return;
      if (this.dragImage.image.hasPointerCapture(event.pointerId)) {
        this.dragImage.image.releasePointerCapture(event.pointerId);
      }
      this.dragImage = null;
    });

    this.editor.addEventListener("pointercancel", () => {
      this.dragImage = null;
    });

    this.editor.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        event.preventDefault();
        this.close(true);
      }
      if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
        event.preventDefault();
        this.save();
      }
    });

    this.overlay.querySelector(".rich-editor-backdrop").addEventListener("click", () => {
      this.close(true);
    });
  }

  _exec(command, value) {
    document.execCommand(command, false, value || null);
    this._updateStatus("Rich text updated.");
  }

  async _insertSelectedImage(file) {
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      this._updateStatus("Choose an image file.");
      return;
    }

    const dataUrl = await new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(String(reader.result));
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });

    const extension = (
      file.name.split(".").pop() || "png"
    ).toLowerCase().replace(/[^a-z0-9]/g, "") || "png";
    const safeBase = (
      file.name.replace(/.[^.]+$/, "")
        .replace(/[^A-Za-z0-9_-]+/g, "_")
        .slice(0, 48) || "image"
    );
    const randomId = (
      crypto.randomUUID
        ? crypto.randomUUID()
        : Date.now().toString(36) + "_" + Math.random().toString(36).slice(2)
    );
    const assetName = "assets/rich_text/" +
      safeBase + "_" + randomId + "." + extension;

    this.assets[assetName] = {
      dataUrl,
      mime: file.type,
    };

    const image = document.createElement("img");
    image.className = "rte-image";
    image.alt = file.name;
    image.src = dataUrl;
    image.style.width = "320px";
    image.style.maxWidth = "none";
    image.style.marginLeft = "0px";
    image.style.marginTop = "0px";

    const range = window.getSelection()?.rangeCount
      ? window.getSelection().getRangeAt(0)
      : null;
    if (range && this.editor.contains(range.commonAncestorContainer)) {
      range.deleteContents();
      range.insertNode(image);
      range.setStartAfter(image);
      range.collapse(true);
      window.getSelection().removeAllRanges();
      window.getSelection().addRange(range);
    } else {
      this.editor.appendChild(image);
    }

    this._selectImage(image);
    this._updateStatus("Inserted " + file.name + ". Drag or resize it before saving.");
  }

  _selectImage(image) {
    this._clearImageSelection();
    this.selectedImage = image;
    image.classList.add("rte-image-selected");

    const handle = document.createElement("span");
    handle.className = "rte-image-resize";
    handle.setAttribute("contenteditable", "false");
    handle.title = "Drag to resize";
    image.parentElement?.appendChild(handle);
    this._resizeHandle = handle;
    this._resizeStart = null;

    handle.addEventListener("pointerdown", (event) => {
      event.preventDefault();
      event.stopPropagation();
      this._resizeStart = {
        width: image.getBoundingClientRect().width,
        x: event.clientX
      };
      handle.setPointerCapture(event.pointerId);
    });
    handle.addEventListener("pointermove", (event) => {
      if (!this._resizeStart) return;
      const next = Math.max(
        80,
        Math.min(
          1400,
          this._resizeStart.width + event.clientX - this._resizeStart.x
        )
      );
      image.style.width = Math.round(next) + "px";
    });
    handle.addEventListener("pointerup", () => {
      this._resizeStart = null;
    });
    handle.addEventListener("pointercancel", () => {
      this._resizeStart = null;
    });
  }

  _clearImageSelection() {
    if (this.selectedImage) {
      this.selectedImage.classList.remove("rte-image-selected");
    }
    if (this._resizeHandle) this._resizeHandle.remove();
    this.selectedImage = null;
    this._resizeHandle = null;
    this._resizeStart = null;
  }

  _serializableHtml() {
    this._clearImageSelection();
    const clone = this.editor.cloneNode(true);
    clone.querySelectorAll(".rte-image-resize").forEach((node) => node.remove());

    clone.querySelectorAll(".rte-image").forEach((image) => {
      const src = image.getAttribute("src") || "";
      if (src.startsWith("data:image/")) {
        const record = Object.entries(this.assets).find(
          ([, value]) => value && value.dataUrl === src
        );
        if (record) {
          image.setAttribute("src", record[0]);
        }
      }
      image.classList.remove("rte-image-selected");
    });

    return sanitizeRichHtml(
      clone.innerHTML,
      (asset) => asset
    );
  }

  save() {
    const html = this._serializableHtml();
    const plain = plainTextFromHtml(html);
    this.onSave({
      html,
      text: plain,
    });
    this._updateStatus("Description saved.");
    this.close(false);
  }

  _updateStatus(message) {
    const status = this.overlay?.querySelector("[data-rte-status]");
    if (status) status.textContent = message;
    this.onStatus(message);
  }

  _animateOpen() {
    const rect = this.origin?.getBoundingClientRect();
    const target = {
      left: window.innerWidth * 0.045,
      top: window.innerHeight * 0.055,
      width: window.innerWidth * 0.91,
      height: window.innerHeight * 0.89
    };

    if (!rect) {
      this.panel.animate(
        [
          {opacity: 0, transform: "scale(.96)"},
          {opacity: 1, transform: "scale(1)"}
        ],
        {duration: 260, easing: "cubic-bezier(.22,1,.36,1)", fill: "forwards"}
      );
      return;
    }

    this.panel.style.left = rect.left + "px";
    this.panel.style.top = rect.top + "px";
    this.panel.style.width = rect.width + "px";
    this.panel.style.height = rect.height + "px";

    requestAnimationFrame(() => {
      this.panel.animate(
        [
          {
            left: rect.left + "px",
            top: rect.top + "px",
            width: rect.width + "px",
            height: rect.height + "px",
            borderRadius: "10px"
          },
          {
            left: target.left + "px",
            top: target.top + "px",
            width: target.width + "px",
            height: target.height + "px",
            borderRadius: "18px"
          }
        ],
        {
          duration: 340,
          easing: "cubic-bezier(.22,1,.36,1)",
          fill: "forwards"
        }
      );
    });
  }

  close(animate = true) {
    if (!this.overlay) return;

    const overlay = this.overlay;
    const panel = this.panel;
    const rect = this.origin?.getBoundingClientRect();

    const finish = () => {
      if (overlay.isConnected) overlay.remove();
      this.overlay = null;
      this.panel = null;
      this.editor = null;
      this._clearImageSelection();
      if (this.origin?.isConnected) this.origin.focus?.();
      this.origin = null;
    };

    if (!animate || !rect) {
      finish();
      return;
    }

    panel.animate(
      [
        {
          left: panel.getBoundingClientRect().left + "px",
          top: panel.getBoundingClientRect().top + "px",
          width: panel.getBoundingClientRect().width + "px",
          height: panel.getBoundingClientRect().height + "px",
          borderRadius: "18px",
          opacity: 1
        },
        {
          left: rect.left + "px",
          top: rect.top + "px",
          width: rect.width + "px",
          height: rect.height + "px",
          borderRadius: "10px",
          opacity: 0.95
        }
      ],
      {
        duration: 300,
        easing: "cubic-bezier(.4,0,.2,1)",
        fill: "forwards"
      }
    ).finished.then(finish).catch(finish);
  }
}

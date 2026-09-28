const DB_NAME = "adventure-pwa";
const DB_VERSION = 1;
const STORE_NAME = "worlds";

class BrowserRuntime {
  constructor() {
    this.worker = new Worker("./pyodide-worker.js", {type: "module"});
    this.pending = new Map();
    this.nextId = 1;
    this.worlds = new Map();
    this.ready = this.initStorage();
    this.worker.onmessage = (event) => {
      const {id, ok, result, error} = event.data || {};
      const pending = this.pending.get(id);
      if (!pending) return;
      this.pending.delete(id);
      ok ? pending.resolve(result) : pending.reject(new Error(error || "Browser runtime failed"));
    };
    this.worker.onerror = (event) => {
      const message = event.message || "Browser runtime worker failed";
      for (const pending of this.pending.values()) pending.reject(new Error(message));
      this.pending.clear();
    };
  }

  async initStorage() {
    if (!("indexedDB" in window)) return;
    const db = await new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);
      request.onupgradeneeded = () => request.result.createObjectStore(STORE_NAME, {keyPath: "world"});
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error || new Error("Unable to open local story storage"));
    });
    const records = await new Promise((resolve, reject) => {
      const request = db.transaction(STORE_NAME, "readonly").objectStore(STORE_NAME).getAll();
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error || new Error("Unable to read local stories"));
    });
    for (const record of records) this.worlds.set(record.world, record.package);
    this.db = db;
    if (!this.worlds.size) {
      await this.seedBuiltins();
    }
  }

  async seedBuiltins() {
    const packageData = {
      world: "Three_Choices",
      source_format: "built-in",
      story: {
        schema_version: 3,
        name: "Three_Choices",
        start_room: "start",
        rooms: {
          start: {
            name: "Crossroads",
            description: "Three paths leave a quiet crossroads. The road behind you is already fading into the dusk.",
          },
          forest: {
            name: "Forest",
            description: "The forest closes around you. Somewhere beyond the trees, something is watching.",
          },
          tower: {
            name: "Tower",
            description: "An old tower rises above the road. A narrow door stands open.",
          },
          river: {
            name: "River",
            description: "A cold river blocks the trail. Flat stones form a precarious crossing.",
          },
        },
        connections: {
          start__forest: {from: "start", to: "forest", label: "Enter the forest"},
          start__tower: {from: "start", to: "tower", label: "Approach the tower"},
          start__river: {from: "start", to: "river", label: "Follow the river"},
          forest__start: {from: "forest", to: "start", label: "Return to the crossroads"},
          tower__start: {from: "tower", to: "start", label: "Return to the crossroads"},
          river__start: {from: "river", to: "start", label: "Return to the crossroads"},
        },
        revisits: {},
        metadata: {},
      },
      skill_checks: {schema_version: 1, skill_checks: {}},
      inventory: {schema_version: 1, items: {}, room_items: {}, room_requirements: {}},
      assets: {},
    };
    this.worlds.set(packageData.world, packageData);
    if (this.db) {
      await new Promise((resolve, reject) => {
        const request = this.db.transaction(STORE_NAME, "readwrite")
          .objectStore(STORE_NAME).put({world: packageData.world, package: packageData});
        request.onsuccess = () => resolve();
        request.onerror = () => reject(request.error || new Error("Unable to seed built-in story"));
      });
    }
  }

  async listStories() {
    await this.ready;
    return [...this.worlds.values()].sort((a, b) => a.world.localeCompare(b.world))
      .map((x) => ({id: x.world, source_format: x.source_format || "canonical"}));
  }

  async loadWorld(world) {
    await this.ready;
    const packageData = this.worlds.get(world);
    if (!packageData) throw new Error("Story not found: " + world);
    return structuredClone(packageData);
  }

  async saveLocalPackage(packageData) {
    await this.ready;
    const normalized = structuredClone(packageData);
    normalized.world = normalized.story.name;
    normalized.source_format = "canonical";
    this.worlds.set(normalized.world, normalized);
    if (this.db) {
      await new Promise((resolve, reject) => {
        const request = this.db.transaction(STORE_NAME, "readwrite").objectStore(STORE_NAME)
          .put({world: normalized.world, package: normalized});
        request.onsuccess = () => resolve();
        request.onerror = () => reject(request.error || new Error("Unable to save story"));
      });
    }
    return normalized;
  }

  async importZip(file) {
    const bytes = [...new Uint8Array(await file.arrayBuffer())];
    const packageData = await this.call("zip_read", bytes);
    await this.saveLocalPackage(packageData);
    return packageData;
  }

  async exportZip(packageData) {
    const bytes = await this.call("zip_write", packageData);
    return new Blob([new Uint8Array(bytes)], {type: "application/zip"});
  }

  async call(operation, payload) {
    return new Promise((resolve, reject) => {
      const id = this.nextId++;
      this.pending.set(id, {resolve, reject});
      this.worker.postMessage({id, operation, payload});
    });
  }

  async newGame(packageData) { return this.call("new_game", {package: packageData}); }
  async observe(packageData, state) { return this.call("observe", {package: packageData, state}); }
  async step(packageData, state, action) { return this.call("step", {package: packageData, state, action}); }
  async roll(packageData, state) { return this.call("roll", {package: packageData, state}); }
  async validate(packageData) { return this.call("validate", packageData); }
}

export const runtime = new BrowserRuntime();

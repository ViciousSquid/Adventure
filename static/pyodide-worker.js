const PYODIDE_VERSION = "0.314.0.7";
const PYODIDE_INDEX = "https://cdn.jsdelivr.net/pyodide/v" + PYODIDE_VERSION + "/full/";
let pyodide = null;

async function ensureRuntime() {
  if (pyodide) return pyodide;
  importScripts(PYODIDE_INDEX + "pyodide.js");
  pyodide = await loadPyodide({indexURL: PYODIDE_INDEX});
  const response = await fetch("./py/browser_runtime.py");
  if (!response.ok) throw new Error("Unable to load the Adventure browser runtime.");
  const source = await response.text();
  pyodide.FS.writeFile("/browser_runtime.py", source);
  pyodide.runPython("import sys; sys.path.insert(0, '/'); import browser_runtime");
  return pyodide;
}

self.onmessage = async (event) => {
  const {id, operation, payload} = event.data || {};
  try {
    const runtime = await ensureRuntime();
    runtime.globals.set("input_payload", payload);
    runtime.globals.set("input_operation", operation);
    const raw = runtime.runPython(
      "import browser_runtime, json\n"
      + "browser_result = browser_runtime.json_call(input_operation, input_payload)\n"
      + "json.dumps(browser_result, ensure_ascii=False)"
    );
    const result = JSON.parse(raw);
    self.postMessage({id, ok: true, result});
    runtime.globals.delete("input_payload");
    runtime.globals.delete("input_operation");
  } catch (error) {
    self.postMessage({id, ok: false, error: error instanceof Error ? error.message : String(error)});
  }
};

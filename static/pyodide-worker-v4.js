import { loadPyodide } from "https://cdn.jsdelivr.net/pyodide/v314.0.7/full/pyodide.mjs";

const PYODIDE_INDEX = "https://cdn.jsdelivr.net/pyodide/v314.0.7/full/";
let pyodideReadyPromise = null;

async function ensureRuntime() {
  if (!pyodideReadyPromise) {
    pyodideReadyPromise = loadPyodide({indexURL: PYODIDE_INDEX}).then(async (runtime) => {
      const response = await fetch("./py/browser_runtime.py?v=7");
      if (!response.ok) {
        throw new Error("Unable to load the Adventure browser runtime.");
      }
      const source = await response.text();
      runtime.FS.writeFile("/browser_runtime.py", source);
      runtime.runPython("import sys; sys.path.insert(0, '/'); import browser_runtime");
      return runtime;
    });
  }
  return pyodideReadyPromise;
}

self.onmessage = async (event) => {
  const {id, operation, payload} = event.data || {};
  try {
    const runtime = await ensureRuntime();
    runtime.globals.set("input_payload", payload);
    runtime.globals.set("input_operation", operation);
    const raw = runtime.runPython(
      "import browser_runtime, json\n"
      + "browser_payload = input_payload.to_py() if hasattr(input_payload, 'to_py') else input_payload\n"
      + "browser_result = browser_runtime.json_call(input_operation, browser_payload)\n"
      + "json.dumps(browser_result, ensure_ascii=False)"
    );
    const result = JSON.parse(raw);
    self.postMessage({id, ok: true, result});
    runtime.globals.delete("input_payload");
    runtime.globals.delete("input_operation");
  } catch (error) {
    self.postMessage({
      id,
      ok: false,
      error: error instanceof Error ? error.message : String(error),
    });
  }
};

// Legacy Squoosh expects filesystem WASM loading. Native Node fetch treats paths
// as URLs; disable it only in this tool and its workers. Cap the worker pool in
// CPU-limited VMs where os.cpus() still reports the physical host's core count.
globalThis.fetch = undefined;
const os = require('os');
const cpus = os.cpus;
os.cpus = () => cpus().slice(0, 2);

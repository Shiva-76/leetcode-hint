// Browser shim for Node.js built-ins (fs, path) imported by web-tree-sitter.
// These are never called in the browser — tree-sitter uses its own wasm loader.
export default {};
export const readFileSync = () => {};
export const existsSync   = () => false;
export const join         = (...args) => args.join('/');
export const resolve      = (...args) => args.join('/');
export const dirname      = (p) => p.split('/').slice(0, -1).join('/');

/**
 * create-icons.mjs
 * Generates icon16.png, icon48.png, icon128.png in public/icons/
 * Uses only Node.js built-ins (zlib + fs) — no extra deps needed.
 *
 * Icon design: indigo (#4F46E5) background, white "AI" text rendered
 * as simple pixel blocks for small sizes, clean at all sizes.
 */

import zlib from 'zlib';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT_DIR = path.join(__dirname, '..', 'public', 'icons');
fs.mkdirSync(OUT_DIR, { recursive: true });

// Indigo: #4F46E5  → R=79, G=70, B=229
// White:  #FFFFFF  → R=255, G=255, B=255
const BG  = [79,  70,  229];
const FG  = [255, 255, 255];

/**
 * Build a raw PNG Buffer for a solid-color image of given size.
 * Each pixel is either BG or FG based on the pixelFn callback.
 * @param {number} size
 * @param {function(x: number, y: number): boolean} pixelFn  true → FG
 * @returns {Buffer}
 */
function buildPNG(size, pixelFn) {
  // --- Build raw RGBA scanlines ---
  const scanlines = [];
  for (let y = 0; y < size; y++) {
    const row = Buffer.alloc(1 + size * 3); // filter byte + RGB pixels
    row[0] = 0; // filter type: None
    for (let x = 0; x < size; x++) {
      const [r, g, b] = pixelFn(x, y) ? FG : BG;
      row[1 + x * 3]     = r;
      row[1 + x * 3 + 1] = g;
      row[1 + x * 3 + 2] = b;
    }
    scanlines.push(row);
  }
  const rawData = Buffer.concat(scanlines);

  // --- Compress with zlib (deflate) ---
  const compressed = zlib.deflateSync(rawData);

  // --- PNG helpers ---
  function chunk(type, data) {
    const typeBytes = Buffer.from(type, 'ascii');
    const len = Buffer.alloc(4); len.writeUInt32BE(data.length);
    const crcInput = Buffer.concat([typeBytes, data]);
    const crc = Buffer.alloc(4); crc.writeUInt32BE(crc32(crcInput));
    return Buffer.concat([len, typeBytes, data, crc]);
  }

  // IHDR
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(size, 0);  // width
  ihdr.writeUInt32BE(size, 4);  // height
  ihdr[8]  = 8;  // bit depth
  ihdr[9]  = 2;  // color type: RGB
  ihdr[10] = 0;  // compression
  ihdr[11] = 0;  // filter
  ihdr[12] = 0;  // interlace: none

  return Buffer.concat([
    Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), // PNG signature
    chunk('IHDR', ihdr),
    chunk('IDAT', compressed),
    chunk('IEND', Buffer.alloc(0)),
  ]);
}

/** CRC-32 table */
const crcTable = (() => {
  const table = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = (c & 1) ? 0xEDB88320 ^ (c >>> 1) : c >>> 1;
    table[n] = c;
  }
  return table;
})();

function crc32(buf) {
  let crc = 0xFFFFFFFF;
  for (const byte of buf) crc = crcTable[(crc ^ byte) & 0xFF] ^ (crc >>> 8);
  return (crc ^ 0xFFFFFFFF) >>> 0;
}

// ── Icon pixel functions ──────────────────────────────────────────────────────

/**
 * Draw "AI" as block letters scaled to icon size.
 * Returns true (FG/white) if the pixel is part of the letter glyph.
 */
function drawAI(x, y, size) {
  const s = size;
  // Normalize to 0..1
  const nx = x / s;
  const ny = y / s;

  // Rounded corner mask — only draw inside rounded rect
  const r = 0.15; // corner radius fraction
  const cx = Math.min(Math.max(nx, r), 1 - r);
  const cy = Math.min(Math.max(ny, r), 1 - r);
  const distCorner = Math.hypot(nx - cx, ny - cy);
  if (distCorner > r) return null; // outside rounded rect → transparent (we'll use BG)

  // "A" occupies left ~55% of width (with padding), "I" right ~30%
  // Overall text block centered
  const pad = 0.12;
  const textW = 1 - 2 * pad;
  const textH = 1 - 2 * pad;

  // Map pixel to text-space
  const tx = (nx - pad) / textW;
  const ty = (ny - pad) / textH;
  if (tx < 0 || tx > 1 || ty < 0 || ty > 1) return false;

  const strokeW = 0.12; // relative stroke width

  // ── Letter "A" ── occupies tx 0..0.55
  const aRight = 0.55;
  if (tx >= 0 && tx <= aRight) {
    const ax = tx / aRight; // 0..1 within A
    // Left leg: thin vertical on left
    if (ax < strokeW) return true;
    // Right leg: thin vertical on right
    if (ax > 1 - strokeW) return true;
    // Crossbar: horizontal at midHeight
    if (ty > 0.42 && ty < 0.58 && ax > 0.1 && ax < 0.9) return true;
    // Diagonal fill: A shape — pixels inside the A outline
    const slopeL = ty > ax * (1 / (strokeW * 2)); // inside left slope
    const slopeR = ty > (1 - ax) * (1 / (strokeW * 2)); // inside right slope
    if (ax < 0.5 && ax >= strokeW && ty > ax && ty < ax + strokeW) return true; // left diagonal
    if (ax > 0.5 && ax <= 1 - strokeW && ty > (1 - ax) && ty < (1 - ax) + strokeW) return true; // right diagonal
  }

  // ── Letter "I" ── occupies tx 0.65..1.0
  const iLeft = 0.65;
  if (tx >= iLeft) {
    const ix = (tx - iLeft) / (1 - iLeft); // 0..1 within I
    const iStroke = 0.2;
    // Top bar
    if (ty < strokeW) return true;
    // Bottom bar
    if (ty > 1 - strokeW) return true;
    // Vertical stem
    if (ix > 0.5 - iStroke && ix < 0.5 + iStroke) return true;
  }

  return false;
}

// ── Generate PNGs ─────────────────────────────────────────────────────────────

const SIZES = [16, 48, 128];

for (const size of SIZES) {
  const png = buildPNG(size, (x, y) => !!drawAI(x, y, size));
  const outPath = path.join(OUT_DIR, `icon${size}.png`);
  fs.writeFileSync(outPath, png);
  console.log(`✓ Created ${outPath} (${size}x${size})`);
}

console.log('\nAll icons created successfully!');

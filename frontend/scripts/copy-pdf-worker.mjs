import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);

const pdfjsDistPath = path.dirname(require.resolve('pdfjs-dist/package.json'));
const sourcePath = path.join(pdfjsDistPath, 'build', 'pdf.worker.min.mjs');
const targetDir = path.resolve(process.cwd(), 'public');
const targetPath = path.join(targetDir, 'pdf.worker.min.mjs');

fs.mkdirSync(targetDir, { recursive: true });
fs.copyFileSync(sourcePath, targetPath);

console.log(`Copied PDF worker to ${targetPath}`);

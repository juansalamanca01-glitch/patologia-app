// Pruebas de "npm run check". Se ejecutan con: npm test (desde la raíz del proyecto).
import assert from 'node:assert/strict';
import path from 'node:path';
import { test } from 'node:test';
import { comprobaciones } from './check.mjs';

const RAIZ = path.join('C:', 'proyecto');

test('revisa formato y linter del frontend y del backend, en ese orden', () => {
  assert.deepEqual(
    comprobaciones(RAIZ, 'win32').map(({ nombre }) => nombre),
    [
      'Formato del frontend (Prettier)',
      'Linter del frontend (ESLint)',
      'Formato del backend (Ruff)',
      'Linter del backend (Ruff)',
    ],
  );
});

test('ninguna comprobación modifica archivos', () => {
  const [formatoFront, lintFront, formatoBack, lintBack] = comprobaciones(RAIZ, 'linux');
  assert.deepEqual(formatoFront.args, ['run', 'format:check']);
  assert.deepEqual(lintFront.args, ['run', 'lint']);
  assert.deepEqual(formatoBack.args, ['-m', 'ruff', 'format', '--check', '.']);
  assert.deepEqual(lintBack.args, ['-m', 'ruff', 'check', '.']);
  assert.ok(comprobaciones(RAIZ).every(({ args }) => !args.includes('--fix') && !args.includes('--write')));
});

test('Ruff usa el Python del venv según el sistema operativo', () => {
  const enWindows = comprobaciones(RAIZ, 'win32')[2];
  assert.equal(enWindows.comando, path.join(RAIZ, 'backend', 'venv', 'Scripts', 'python.exe'));
  assert.equal(enWindows.cwd, path.join(RAIZ, 'backend'));
  assert.equal(comprobaciones(RAIZ, 'darwin')[3].comando, path.join(RAIZ, 'backend', 'venv', 'bin', 'python'));
});

test('Prettier y ESLint se ejecutan en frontend/', () => {
  const [formatoFront, lintFront] = comprobaciones(RAIZ, 'win32');
  assert.equal(formatoFront.cwd, path.join(RAIZ, 'frontend'));
  assert.equal(lintFront.cwd, path.join(RAIZ, 'frontend'));
});

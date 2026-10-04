// Pruebas de las comprobaciones que hace "npm run dev" antes de arrancar.
// Se ejecutan con: npm test (desde la raíz del proyecto).
import assert from 'node:assert/strict';
import path from 'node:path';
import { test } from 'node:test';
import { revisarEntorno, rutaPython } from './entorno.mjs';

const RAIZ = path.join('C:', 'proyecto');

// Simula qué archivos existen: todos, salvo los indicados en "faltan".
function existeExcepto(...faltan) {
  const rutasQueFaltan = faltan.map((relativa) => path.join(RAIZ, relativa));
  return (ruta) => !rutasQueFaltan.includes(ruta);
}

test('en Windows, Python está en venv/Scripts/python.exe', () => {
  assert.equal(rutaPython(RAIZ, 'win32'), path.join(RAIZ, 'backend', 'venv', 'Scripts', 'python.exe'));
});

test('en Linux y Mac, Python está en venv/bin/python', () => {
  assert.equal(rutaPython(RAIZ, 'linux'), path.join(RAIZ, 'backend', 'venv', 'bin', 'python'));
  assert.equal(rutaPython(RAIZ, 'darwin'), path.join(RAIZ, 'backend', 'venv', 'bin', 'python'));
});

test('con todo instalado no hay errores ni avisos', () => {
  const { errores, avisos } = revisarEntorno({ raiz: RAIZ, plataforma: 'win32', existe: () => true });
  assert.deepEqual(errores, []);
  assert.deepEqual(avisos, []);
});

test('si falta el entorno virtual, explica cómo crearlo', () => {
  const { errores } = revisarEntorno({
    raiz: RAIZ, plataforma: 'win32', existe: existeExcepto(path.join('backend', 'venv', 'Scripts', 'python.exe')),
  });
  assert.equal(errores.length, 1);
  assert.match(errores[0].problema, /entorno virtual/);
  assert.match(errores[0].solucion, /python -m venv venv/);
});

test('si falta backend/.env, explica cómo crearlo', () => {
  const { errores } = revisarEntorno({
    raiz: RAIZ, plataforma: 'linux', existe: existeExcepto(path.join('backend', '.env')),
  });
  assert.equal(errores.length, 1);
  assert.match(errores[0].problema, /backend\/\.env/);
  assert.match(errores[0].solucion, /\.env\.example/);
});

test('si faltan las dependencias del frontend, pide npm install', () => {
  const { errores } = revisarEntorno({
    raiz: RAIZ, plataforma: 'win32', existe: existeExcepto(path.join('frontend', 'node_modules')),
  });
  assert.equal(errores.length, 1);
  assert.match(errores[0].solucion, /npm install/);
});

test('si falta frontend/.env solo avisa: la app funciona igual', () => {
  const { errores, avisos } = revisarEntorno({
    raiz: RAIZ, plataforma: 'win32', existe: existeExcepto(path.join('frontend', '.env')),
  });
  assert.deepEqual(errores, []);
  assert.equal(avisos.length, 1);
  assert.match(avisos[0], /frontend\/\.env/);
});

test('informa todos los problemas a la vez, no solo el primero', () => {
  const { errores } = revisarEntorno({ raiz: RAIZ, plataforma: 'win32', existe: () => false });
  assert.equal(errores.length, 3);
});

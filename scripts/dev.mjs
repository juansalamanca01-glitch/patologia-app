// npm run dev: levanta el backend (Django, puerto 8000) y el frontend (Vite, puerto 5173)
// en una sola terminal. Ctrl + C detiene los dos.
import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { revisarEntorno, rutaPython } from './entorno.mjs';

const raiz = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const carpetaBackend = path.join(raiz, 'backend');

// 1. Comprobar que todo esté instalado antes de arrancar.
const { errores, avisos } = revisarEntorno({ raiz, existe: existsSync });
avisos.forEach((aviso) => console.log(`Aviso: ${aviso}`));
if (errores.length > 0) {
  console.error('\nTodavía no se puede arrancar PathoLab. Falta preparar lo siguiente:\n');
  errores.forEach(({ problema, solucion }, i) => {
    console.error(`${i + 1}. ${problema}\n   Solución: ${solucion}\n`);
  });
  process.exit(1);
}

// 2. Avisar si hay migraciones sin aplicar (pasa al traer cambios de otro computador).
const python = rutaPython(raiz);
const revision = spawnSync(python, ['manage.py', 'migrate', '--check'], { cwd: carpetaBackend, encoding: 'utf8' });
if (revision.stderr && revision.stderr.includes('Error')) {
  // El backend ni siquiera pudo cargar su configuración (por ejemplo, un .env mal escrito).
  const ultimaLinea = revision.stderr.trim().split('\n').pop();
  console.error(`\nEl backend no pudo iniciar:\n  ${ultimaLinea}\n`);
  process.exit(1);
}
if (revision.status !== 0) {
  console.log('Aviso: hay migraciones de la base de datos sin aplicar. Ejecuta: cd backend && python manage.py migrate');
}

// 3. Arrancar los dos servidores. Si uno se detiene, se detiene también el otro.
// concurrently se carga aquí y no arriba: si falta el "npm install" de la raíz,
// así se puede explicar qué hacer en lugar de mostrar un error de Node.
let concurrently;
try {
  ({ default: concurrently } = await import('concurrently'));
} catch {
  console.error('\nFalta instalar las herramientas de la raíz del proyecto. Ejecuta (en la raíz): npm install\n');
  process.exit(1);
}

console.log(`
PathoLab en marcha:
  Aplicación:          http://localhost:5173
  API:                 http://localhost:8000/api/
  Panel de Django:     http://localhost:8000/admin/
Pulsa Ctrl + C para detener los dos servidores.
`);

const { result } = concurrently(
  [
    { command: `"${python}" manage.py runserver`, name: 'backend', cwd: carpetaBackend, prefixColor: 'green' },
    { command: 'npm run dev', name: 'frontend', cwd: path.join(raiz, 'frontend'), prefixColor: 'cyan' },
  ],
  { killOthersOn: ['failure', 'success'] },
);
result.catch(() => process.exit(1));

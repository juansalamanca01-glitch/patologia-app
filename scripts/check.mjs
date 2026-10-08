// npm run check: revisa el formato y el linter del frontend (Prettier, ESLint) y del
// backend (Ruff), sin cambiar ningún archivo. Termina con error si alguna falla.
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { rutaPython } from './entorno.mjs';

/**
 * Las cuatro comprobaciones, en orden. Ruff se ejecuta con el Python del venv
 * ("python -m ruff"), así la ruta es la misma en Windows, Mac y Linux.
 */
export function comprobaciones(raiz, plataforma = process.platform) {
  const frontend = path.join(raiz, 'frontend');
  const backend = path.join(raiz, 'backend');
  const python = rutaPython(raiz, plataforma);
  return [
    { nombre: 'Formato del frontend (Prettier)', comando: 'npm', args: ['run', 'format:check'], cwd: frontend },
    { nombre: 'Linter del frontend (ESLint)', comando: 'npm', args: ['run', 'lint'], cwd: frontend },
    { nombre: 'Formato del backend (Ruff)', comando: python, args: ['-m', 'ruff', 'format', '--check', '.'], cwd: backend },
    { nombre: 'Linter del backend (Ruff)', comando: python, args: ['-m', 'ruff', 'check', '.'], cwd: backend },
  ];
}

// Solo se ejecuta si se llama directamente (npm run check), no al importarlo en las pruebas.
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const raiz = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
  const resultados = comprobaciones(raiz).map(({ nombre, comando, args, cwd }) => {
    console.log(`\n=== ${nombre} ===`);
    // En Windows, npm es un archivo .cmd y necesita la terminal para ejecutarse. Con la
    // terminal, Node pide el comando en un solo texto; los argumentos son fijos, de este script.
    const { status, error } =
      comando === 'npm'
        ? spawnSync(`npm ${args.join(' ')}`, { cwd, stdio: 'inherit', shell: true })
        : spawnSync(comando, args, { cwd, stdio: 'inherit' });
    if (error) console.error(`No se pudo ejecutar: ${error.message}`);
    return { nombre, bien: status === 0 };
  });

  console.log('\n=== Resumen ===');
  resultados.forEach(({ nombre, bien }) => console.log(`${bien ? 'OK   ' : 'FALLA'}  ${nombre}`));
  if (resultados.some(({ bien }) => !bien)) {
    console.log(
      '\nPara corregir el formato: "npm run format" en frontend/ y "python -m ruff format ." en backend/.' +
        '\nSi falta Ruff: cd backend && pip install -r requirements-dev.txt',
    );
    process.exit(1);
  }
}

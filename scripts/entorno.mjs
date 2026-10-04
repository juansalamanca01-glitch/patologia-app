// Comprobaciones previas de "npm run dev": revisa que el entorno de desarrollo esté
// instalado y, si falta algo, explica qué comando ejecutar.
import path from 'node:path';

// Ruta del Python del entorno virtual del backend (cambia según el sistema operativo).
export function rutaPython(raiz, plataforma = process.platform) {
  const partes = plataforma === 'win32' ? ['Scripts', 'python.exe'] : ['bin', 'python'];
  return path.join(raiz, 'backend', 'venv', ...partes);
}

/**
 * Revisa lo necesario para arrancar backend y frontend.
 * - errores: impiden arrancar; cada uno trae el problema y la solución.
 * - avisos: la app funciona igual, pero conviene saberlo.
 * "existe" se recibe como parámetro para poder probar la función sin crear archivos.
 */
export function revisarEntorno({ raiz, plataforma = process.platform, existe }) {
  const errores = [];
  const avisos = [];
  const activarVenv = plataforma === 'win32' ? '.\\venv\\Scripts\\Activate.ps1' : 'source venv/bin/activate';
  const copiar = plataforma === 'win32' ? 'copy' : 'cp';

  if (!existe(rutaPython(raiz, plataforma))) {
    errores.push({
      problema: 'No existe el entorno virtual de Python del backend (backend/venv).',
      solucion: `cd backend && python -m venv venv && ${activarVenv} && pip install -r requirements.txt`,
    });
  }
  if (!existe(path.join(raiz, 'backend', '.env'))) {
    errores.push({
      problema: 'No existe backend/.env (sin SECRET_KEY el backend no arranca).',
      solucion: `cd backend && ${copiar} .env.example .env   y luego pon una SECRET_KEY propia (ver README).`,
    });
  }
  if (!existe(path.join(raiz, 'frontend', 'node_modules'))) {
    errores.push({
      problema: 'No están instaladas las dependencias del frontend (frontend/node_modules).',
      solucion: 'cd frontend && npm install',
    });
  }
  if (!existe(path.join(raiz, 'frontend', '.env'))) {
    avisos.push('No existe frontend/.env: se usará VITE_API_URL vacía, que es lo correcto en desarrollo.');
  }
  return { errores, avisos };
}

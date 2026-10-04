import { afterEach, describe, expect, it, vi } from 'vitest';

// client.js lee VITE_API_URL al cargarse, así que en cada prueba se fija la
// variable y se vuelve a importar el módulo desde cero.
async function cargarCliente() {
  vi.resetModules();
  return (await import('./client')).default;
}

// Hallazgo I-10 de docs/auditoria-inicial.md: la dirección del backend estaba
// fija en 'http://localhost:8000/api' y solo funcionaba en el computador del
// desarrollador.
describe('client.js: dirección de la API', () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it('sin VITE_API_URL usa /api (en desarrollo lo atiende el proxy de Vite)', async () => {
    vi.stubEnv('VITE_API_URL', '');
    expect((await cargarCliente()).defaults.baseURL).toBe('/api');
  });

  it('con VITE_API_URL usa esa dirección', async () => {
    vi.stubEnv('VITE_API_URL', 'https://api.patolab.com');
    expect((await cargarCliente()).defaults.baseURL).toBe('https://api.patolab.com/api');
  });

  it('una barra al final de VITE_API_URL no produce una doble barra', async () => {
    vi.stubEnv('VITE_API_URL', 'https://api.patolab.com/');
    expect((await cargarCliente()).defaults.baseURL).toBe('https://api.patolab.com/api');
  });
});

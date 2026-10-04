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

// Decisión D-6: al renovar el token, el backend devuelve también un token de
// renovación nuevo e invalida el anterior. El interceptor debe guardar los dos.
describe('client.js: renovación automática del token', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  it('ante un 401 renueva el token, guarda el refresh nuevo y repite la petición', async () => {
    vi.stubEnv('VITE_API_URL', '');
    const axios = (await import('axios')).default;
    const client = await cargarCliente();
    localStorage.setItem('access_token', 'access-vencido');
    localStorage.setItem('refresh_token', 'refresh-viejo');
    const renovar = vi.spyOn(axios, 'post').mockResolvedValue({ data: { access: 'access-nuevo', refresh: 'refresh-nuevo' } });
    let intentos = 0;
    client.defaults.adapter = (config) => {
      intentos += 1;
      if (intentos === 1) return Promise.reject({ config, response: { status: 401 } });
      return Promise.resolve({ data: { ok: true }, status: 200, statusText: 'OK', headers: {}, config });
    };

    const respuesta = await client.get('/informes/');

    expect(renovar).toHaveBeenCalledWith('/api/auth/refresh/', { refresh: 'refresh-viejo' });
    expect(localStorage.getItem('access_token')).toBe('access-nuevo');
    expect(localStorage.getItem('refresh_token')).toBe('refresh-nuevo');
    expect(respuesta.data).toEqual({ ok: true });
  });
});

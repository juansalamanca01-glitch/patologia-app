import axios from 'axios';

// Dirección del backend (auditoría I-10). Se toma de VITE_API_URL (frontend/.env):
// - vacía: se usa "/api" en el mismo sitio que la página. En desarrollo lo
//   reenvía el proxy de vite.config.js a http://localhost:8000; en producción,
//   el servidor web que sirva frontend y backend juntos.
// - con valor (p. ej. https://api.patolab.com): el backend está en otro dominio.
const API_URL = `${(import.meta.env.VITE_API_URL || '').replace(/\/+$/, '')}/api`;

const client = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Añade el token JWT a cada petición
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Si la API responde 401 (token vencido), lo renueva y repite la petición
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      const refresh = localStorage.getItem('refresh_token');
      if (refresh) {
        try {
          const { data } = await axios.post(`${API_URL}/auth/refresh/`, { refresh });
          localStorage.setItem('access_token', data.access);
          original.headers.Authorization = `Bearer ${data.access}`;
          return client(original);
        } catch {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

// Los listados de la API vienen paginados ({count, next, previous, results}).
// Devuelve la lista de resultados, o los datos tal cual si no vienen paginados.
export const resultados = (data) => data.results ?? data;

export default client;

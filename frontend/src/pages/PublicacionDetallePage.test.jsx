import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import client from '../api/client';
import PublicacionDetallePage from './PublicacionDetallePage';

// Sesión simulada: cada prueba elige el rol.
const sesion = vi.hoisted(() => ({ actual: null }));

vi.mock('../context/AuthContext', () => ({
  useAuth: () => sesion.actual,
}));

vi.mock('../api/client', async (importOriginal) => ({
  ...(await importOriginal()),
  default: { get: vi.fn(), post: vi.fn(), delete: vi.fn() },
}));

const PUBLICACION = {
  id: 4, titulo: 'Caso interesante', contenido: 'Texto', autor: 9, autor_nombre: 'Dr. X',
  fijado: false, tema_nombre: null, imagenes: [], comentarios: [], fecha_creacion: '2026-10-04T10:00:00Z',
};

function renderPublicacion() {
  render(
    <MemoryRouter initialEntries={['/foro/4']}>
      <Routes>
        <Route path="/foro/:id" element={<PublicacionDetallePage />} />
      </Routes>
    </MemoryRouter>,
  );
}

// Hallazgo M-7 de docs/auditoria-inicial.md: el auditor veía el formulario para
// comentar, pero la API le rechaza los comentarios (solo lectura).
describe('PublicacionDetallePage: formulario de comentarios', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    client.get.mockResolvedValue({ data: PUBLICACION });
  });

  it('el auditor no ve el formulario para comentar', async () => {
    sesion.actual = { user: { id: 3, rol: 'auditor' }, canWrite: false };
    renderPublicacion();
    expect(await screen.findByText('Caso interesante')).toBeInTheDocument();
    expect(screen.queryByPlaceholderText(/Escribe una observación/i)).toBeNull();
    expect(screen.queryByRole('button', { name: /Comentar/i })).toBeNull();
  });

  it('el patólogo sí puede comentar', async () => {
    sesion.actual = { user: { id: 2, rol: 'patologo' }, canWrite: true };
    renderPublicacion();
    expect(await screen.findByPlaceholderText(/Escribe una observación/i)).toBeInTheDocument();
  });
});

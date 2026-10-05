import { fireEvent, render, screen } from '@testing-library/react';
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

// Prueba manual del 2026-10-05 (Pendientes, punto 2): las imágenes del foro se veían
// pequeñas y no se podían ampliar. Cada miniatura abre un visor con la imagen grande.
describe('PublicacionDetallePage: visor de imágenes', () => {
  const IMAGENES = [
    { id: 1, imagen: '/media/foro/publicaciones/4/uno.png', descripcion: 'Corte uno' },
    { id: 2, imagen: '/media/foro/publicaciones/4/dos.png', descripcion: '' },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    sesion.actual = { user: { id: 1, rol: 'patologo' }, isAdmin: false, canWrite: true };
    client.get.mockResolvedValue({ data: { ...PUBLICACION, imagenes: IMAGENES } });
  });

  const imagenAmpliada = () => screen.getByRole('dialog', { name: /Imagen ampliada/ }).querySelector('img');

  it('al hacer clic en una miniatura la muestra ampliada', async () => {
    renderPublicacion();
    fireEvent.click(await screen.findByRole('button', { name: 'Ampliar imagen 2 de 2' }));
    expect(imagenAmpliada()).toHaveAttribute('src', IMAGENES[1].imagen);
    expect(screen.getByText('2 de 2')).toBeInTheDocument();
  });

  it('se pasa a la imagen siguiente y a la anterior, también con las flechas del teclado', async () => {
    renderPublicacion();
    fireEvent.click(await screen.findByRole('button', { name: 'Ampliar imagen 1 de 2' }));
    expect(screen.getByText('Corte uno')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Imagen siguiente' }));
    expect(imagenAmpliada()).toHaveAttribute('src', IMAGENES[1].imagen);
    fireEvent.keyDown(document, { key: 'ArrowLeft' });
    expect(imagenAmpliada()).toHaveAttribute('src', IMAGENES[0].imagen);
  });

  it('se cierra con el botón, con Escape o haciendo clic fuera de la imagen', async () => {
    renderPublicacion();
    const abrir = async () => fireEvent.click(await screen.findByRole('button', { name: 'Ampliar imagen 1 de 2' }));

    await abrir();
    fireEvent.click(screen.getByRole('button', { name: 'Cerrar' }));
    expect(screen.queryByRole('dialog')).toBeNull();

    await abrir();
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(screen.queryByRole('dialog')).toBeNull();

    await abrir();
    fireEvent.click(screen.getByRole('dialog'));
    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it('con una sola imagen no ofrece anterior ni siguiente', async () => {
    client.get.mockResolvedValue({ data: { ...PUBLICACION, imagenes: [IMAGENES[0]] } });
    renderPublicacion();
    fireEvent.click(await screen.findByRole('button', { name: 'Ampliar imagen 1 de 1' }));
    expect(screen.queryByRole('button', { name: 'Imagen siguiente' })).toBeNull();
    expect(screen.queryByRole('button', { name: 'Imagen anterior' })).toBeNull();
  });
});

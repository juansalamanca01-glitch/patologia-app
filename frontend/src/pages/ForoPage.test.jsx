import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import client from '../api/client';
import ForoPage from './ForoPage';

vi.mock('../api/client', () => ({
  default: { get: vi.fn(), post: vi.fn() },
}));

vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({ canWrite: true }),
}));

const MB = 1024 * 1024;

function archivo(nombre, tipo, tamano) {
  const file = new File(['x'], nombre, { type: tipo });
  // Se simula el tamaño sin crear archivos enormes en memoria.
  Object.defineProperty(file, 'size', { value: tamano });
  return file;
}

async function abrirFormularioYPublicar(container, archivos) {
  fireEvent.click(await screen.findByRole('button', { name: /Nueva publicación/i }));
  fireEvent.change(container.querySelector('input[maxlength="250"]'), { target: { value: 'Caso interesante' } });
  fireEvent.change(container.querySelector('.modal-card textarea'), { target: { value: 'Descripción del caso' } });
  fireEvent.change(container.querySelector('input[type="file"]'), { target: { files: archivos } });
  fireEvent.click(screen.getByRole('button', { name: /^Publicar$/ }));
}

// Hallazgo I-6 de docs/auditoria-inicial.md (punto 4): la publicación se creaba
// antes de subir las imágenes. Si el backend rechazaba una imagen, quedaba una
// publicación sin imágenes y, al reintentar, se creaba otra duplicada.
describe('ForoPage: imágenes de una nueva publicación', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    client.get.mockResolvedValue({ data: [] });
    client.post.mockResolvedValue({ data: { id: 7 } });
  });

  it('no publica nada si una imagen supera los 10 MB', async () => {
    const { container } = render(<MemoryRouter><ForoPage /></MemoryRouter>);
    await abrirFormularioYPublicar(container, [archivo('grande.png', 'image/png', 11 * MB)]);
    expect(await screen.findByText(/supera el tamaño máximo de 10 MB/i)).toBeInTheDocument();
    expect(client.post).not.toHaveBeenCalled();
  });

  it('no publica nada si un archivo no es una imagen', async () => {
    const { container } = render(<MemoryRouter><ForoPage /></MemoryRouter>);
    await abrirFormularioYPublicar(container, [archivo('notas.pdf', 'application/pdf', 1000)]);
    expect(await screen.findByText(/no es una imagen/i)).toBeInTheDocument();
    expect(client.post).not.toHaveBeenCalled();
  });

  it('si el backend rechaza las imágenes, cierra el formulario para no duplicar la publicación', async () => {
    client.post
      .mockResolvedValueOnce({ data: { id: 7 } })
      .mockRejectedValueOnce({ response: { data: { detail: '«foto.png» no es una imagen válida.' } } });
    const { container } = render(<MemoryRouter><ForoPage /></MemoryRouter>);
    await abrirFormularioYPublicar(container, [archivo('foto.png', 'image/png', 2 * MB)]);
    expect(await screen.findByText(/La publicación se creó, pero las imágenes no se pudieron subir/i)).toBeInTheDocument();
    expect(container.querySelector('.modal-card')).toBeNull();
  });

  it('publica y sube las imágenes cuando son válidas', async () => {
    const { container } = render(<MemoryRouter><ForoPage /></MemoryRouter>);
    await abrirFormularioYPublicar(container, [archivo('foto.png', 'image/png', 2 * MB)]);
    await vi.waitFor(() => expect(client.post).toHaveBeenCalledTimes(2));
    expect(client.post.mock.calls[0][0]).toBe('/foro/publicaciones/');
    expect(client.post.mock.calls[1][0]).toBe('/foro/publicaciones/7/imagenes/');
  });
});

import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import client from '../api/client';
import PatologiasPage from './PatologiasPage';

vi.mock('../api/client', async (importOriginal) => ({
  ...(await importOriginal()),
  default: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), delete: vi.fn() },
}));

vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({ canWrite: true }),
}));

const PIEL = { id: 1, nombre: 'Biopsia de Piel', categoria: null, categoria_nombre: null, activa: true, descripcion: '', protocolo_medico: '' };

// Decisión D-4 (auditoría M-5): una patología se puede desactivar desde la
// pantalla Patologías, en lugar de borrarla.
describe('PatologiasPage: activar y desactivar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    client.get.mockImplementation((url) => Promise.resolve({ data: { results: url === '/patologias/' ? [PIEL] : [] } }));
    client.patch.mockResolvedValue({ data: {} });
    client.post.mockResolvedValue({ data: {} });
  });

  it('el formulario de edición permite desactivar una patología', async () => {
    const { container } = render(<PatologiasPage />);
    fireEvent.click(await screen.findByRole('button', { name: 'Editar' }));
    const casilla = screen.getByRole('checkbox', { name: /Activa/i });
    expect(casilla).toBeChecked();
    fireEvent.click(casilla);
    fireEvent.submit(container.querySelector('.modal-card form'));
    await vi.waitFor(() => expect(client.patch).toHaveBeenCalled());
    expect(client.patch.mock.calls[0][0]).toBe('/patologias/1/');
    expect(client.patch.mock.calls[0][1]).toMatchObject({ activa: false });
  });

  it('una patología nueva se crea activa', async () => {
    const { container } = render(<PatologiasPage />);
    fireEvent.click(await screen.findByRole('button', { name: /\+ Patología/i }));
    expect(screen.getByRole('checkbox', { name: /Activa/i })).toBeChecked();
    fireEvent.change(container.querySelector('.modal-card input:not([type="checkbox"])'), { target: { value: 'Nueva' } });
    fireEvent.submit(container.querySelector('.modal-card form'));
    await vi.waitFor(() => expect(client.post).toHaveBeenCalled());
    expect(client.post.mock.calls[0][1]).toMatchObject({ nombre: 'Nueva', activa: true });
  });
});

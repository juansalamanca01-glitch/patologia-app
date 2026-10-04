import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import client from '../api/client';
import DashboardPage from './DashboardPage';

vi.mock('../api/client', async (importOriginal) => ({
  ...(await importOriginal()),
  default: { get: vi.fn(), delete: vi.fn() },
}));

vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({ user: { id: 1, rol: 'patologo', username: 'patologo1' }, canWrite: true, isAdmin: false }),
}));

const BORRADOR = { id: 5, numero_caso: 'PAT-1', patologia_nombre: 'Piel', fecha: '2026-10-04', estado: 'borrador', autor: 1 };

function simularApi() {
  client.get.mockImplementation((url) => Promise.resolve({
    data: url === '/informes/estadisticas/' ? { total: 1, borradores: 1, finalizados: 0 } : { results: [BORRADOR] },
  }));
}

// Hallazgo M-9 de docs/auditoria-inicial.md: los errores solo se escribían en la
// consola del navegador; el usuario no veía nada.
describe('DashboardPage: errores visibles', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('muestra un mensaje si no se puede cargar el panel', async () => {
    client.get.mockRejectedValue(new Error('Network Error'));
    render(<MemoryRouter><DashboardPage /></MemoryRouter>);
    expect(await screen.findByText(/No se pudo cargar el panel/i)).toBeInTheDocument();
  });

  it('muestra el motivo si no se puede eliminar un borrador', async () => {
    simularApi();
    client.delete.mockRejectedValue({ response: { data: { detail: 'El informe está finalizado y no se puede modificar.' } } });
    render(<MemoryRouter><DashboardPage /></MemoryRouter>);
    fireEvent.click(await screen.findByTitle('Eliminar borrador'));
    fireEvent.click(screen.getByRole('button', { name: 'Confirmar' }));
    expect(await screen.findByText('El informe está finalizado y no se puede modificar.')).toBeInTheDocument();
  });
});

import { fireEvent, render, screen } from '@testing-library/react';
import { RouterProvider, createMemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import Navbar from './Navbar';

const logout = vi.fn();
vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({ user: { id: 1, username: 'patologo1', rol: 'patologo' }, logout, canWrite: true }),
}));

// D-13: "Salir" no cierra la sesión de inmediato: navega a /salir. Así, si hay cambios
// sin guardar en un informe, el aviso aparece mientras la sesión sigue abierta.
describe('Navbar: cerrar sesión', () => {
  it('"Salir" lleva a /salir sin cerrar todavía la sesión', async () => {
    const router = createMemoryRouter([
      { path: '/', element: <Navbar /> },
      { path: '/salir', element: <h1>Pantalla de salida</h1> },
    ], { initialEntries: ['/'] });
    render(<RouterProvider router={router} />);
    fireEvent.click(screen.getByRole('button', { name: 'Salir' }));
    expect(await screen.findByRole('heading', { name: 'Pantalla de salida' })).toBeInTheDocument();
    expect(logout).not.toHaveBeenCalled();
  });
});

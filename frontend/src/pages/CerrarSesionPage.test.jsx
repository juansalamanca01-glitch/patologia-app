import { render, screen } from '@testing-library/react';
import { RouterProvider, createMemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import CerrarSesionPage from './CerrarSesionPage';

const sesion = vi.hoisted(() => ({ user: null, logout: null }));
vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({ user: sesion.user, logout: sesion.logout }),
}));

function abrir() {
  const router = createMemoryRouter([
    { path: '/salir', element: <CerrarSesionPage /> },
    { path: '/login', element: <h1>Inicio de sesión</h1> },
  ], { initialEntries: ['/salir'] });
  render(<RouterProvider router={router} />);
}

// D-13: /salir es donde se cierra la sesión, después de que el informe haya podido
// avisar de los cambios sin guardar.
describe('CerrarSesionPage', () => {
  beforeEach(() => {
    sesion.logout = vi.fn();
  });

  it('cierra la sesión y, cuando ya no hay usuario, lleva al login', async () => {
    sesion.user = null;
    abrir();
    expect(await screen.findByRole('heading', { name: 'Inicio de sesión' })).toBeInTheDocument();
    expect(sesion.logout).toHaveBeenCalled();
  });

  it('mientras la sesión se cierra, muestra que está cerrando', () => {
    sesion.user = { id: 1 };
    abrir();
    expect(screen.getByRole('heading', { name: 'Cerrando sesión' })).toBeInTheDocument();
    expect(sesion.logout).toHaveBeenCalled();
  });
});

import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import App from './App';

// Sin sesión: así se ven el login y las páginas legales antes de iniciar sesión.
vi.mock('./context/AuthContext', () => ({
  AuthProvider: ({ children }) => children,
  useAuth: () => ({ user: null, loading: false, login: vi.fn(), logout: vi.fn(), isAdmin: false, canWrite: false }),
}));

function abrir(ruta) {
  window.history.pushState({}, '', ruta);
  return render(<App />);
}

// La política de privacidad y los términos deben poder leerse antes de iniciar sesión.
describe('Enlaces legales sin sesión', () => {
  beforeEach(() => window.history.pushState({}, '', '/'));

  it('el login muestra el pie con la política de privacidad y los términos', () => {
    abrir('/login');
    expect(screen.getByRole('button', { name: /Iniciar Sesión/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Política de Privacidad' })).toHaveAttribute('href', '/politica-privacidad');
    expect(screen.getByRole('link', { name: 'Términos y Condiciones' })).toHaveAttribute('href', '/terminos-condiciones');
  });

  it('desde el login se abre la política de privacidad', () => {
    abrir('/login');
    fireEvent.click(screen.getByRole('link', { name: 'Política de Privacidad' }));
    expect(screen.getByRole('heading', { level: 1, name: 'Política de Privacidad' })).toBeInTheDocument();
  });

  it('una página legal sin sesión tiene el pie y un enlace para volver al login', () => {
    abrir('/terminos-condiciones');
    expect(screen.getByRole('heading', { level: 1, name: /Términos y Condiciones/ })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Volver al inicio de sesión/ })).toHaveAttribute('href', '/login');
    expect(screen.getByRole('link', { name: 'Política de Privacidad' })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('link', { name: /Volver al inicio de sesión/ }));
    expect(screen.getByRole('button', { name: /Iniciar Sesión/i })).toBeInTheDocument();
  });
});

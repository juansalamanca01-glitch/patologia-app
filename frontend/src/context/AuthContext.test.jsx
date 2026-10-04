import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import client from '../api/client';
import { AuthProvider, useAuth } from './AuthContext';

vi.mock('../api/client', () => ({ default: { post: vi.fn() } }));

function MostrarPermisos() {
  const { user, isAdmin, canWrite } = useAuth();
  return <p>{`${user?.rol}: isAdmin=${isAdmin} canWrite=${canWrite}`}</p>;
}

function renderConRol(rol) {
  localStorage.setItem('access_token', 'token');
  localStorage.setItem('user_data', JSON.stringify({ id: 1, username: 'prueba', rol }));
  render(<AuthProvider><MostrarPermisos /></AuthProvider>);
}

// Las páginas deciden qué botones mostrar con isAdmin y canWrite.
// Si este cálculo falla, un patólogo dejaría de poder crear informes.
describe('AuthContext: permisos según el rol', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('el patólogo puede escribir, pero no es admin', () => {
    renderConRol('patologo');
    expect(screen.getByText('patologo: isAdmin=false canWrite=true')).toBeInTheDocument();
  });

  it('el admin puede escribir', () => {
    renderConRol('admin');
    expect(screen.getByText('admin: isAdmin=true canWrite=true')).toBeInTheDocument();
  });

  it('el auditor solo puede leer', () => {
    renderConRol('auditor');
    expect(screen.getByText('auditor: isAdmin=false canWrite=false')).toBeInTheDocument();
  });
});

function BotonSalir() {
  const { logout } = useAuth();
  return <button onClick={logout}>Salir</button>;
}

// Decisión D-6 (auditoría M-11): al salir se avisa al backend para que invalide
// el token de renovación; antes solo se borraban los tokens del navegador.
describe('AuthContext: cerrar sesión', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
    client.post.mockResolvedValue({ data: {} });
  });

  it('invalida el token en el backend y borra los datos del navegador', () => {
    localStorage.setItem('access_token', 'access');
    localStorage.setItem('refresh_token', 'refresh-de-la-sesion');
    localStorage.setItem('user_data', JSON.stringify({ id: 1, rol: 'patologo' }));
    render(<AuthProvider><BotonSalir /></AuthProvider>);
    fireEvent.click(screen.getByRole('button', { name: 'Salir' }));
    expect(client.post).toHaveBeenCalledWith('/auth/logout/', { refresh: 'refresh-de-la-sesion' });
    expect(localStorage.getItem('access_token')).toBeNull();
    expect(localStorage.getItem('refresh_token')).toBeNull();
    expect(localStorage.getItem('user_data')).toBeNull();
  });
});

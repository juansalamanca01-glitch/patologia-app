import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
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

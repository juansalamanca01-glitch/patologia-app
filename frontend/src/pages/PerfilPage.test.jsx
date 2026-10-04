import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import client from '../api/client';
import PerfilPage from './PerfilPage';

// Se reemplaza el cliente de la API para simular sus respuestas sin backend.
vi.mock('../api/client', () => ({
  default: { get: vi.fn(), patch: vi.fn(), post: vi.fn() },
}));

const PERFIL = {
  username: 'patologo1',
  rol: 'patologo',
  nombre_completo: 'Dr. Carlos Méndez',
  email: 'patologo@patologia.local',
  telefono: '',
  especialidad: 'Patología Quirúrgica',
};

// Hallazgo M-8 de docs/auditoria-inicial.md: si la carga del perfil fallaba,
// la página intentaba leer perfil.nombre_completo con perfil = null y toda la
// pantalla quedaba en blanco.
describe('PerfilPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('muestra un mensaje y un botón para reintentar si falla la carga', async () => {
    client.get.mockRejectedValue(new Error('Network Error'));
    render(<PerfilPage />);
    expect(await screen.findByText(/No se pudo cargar tu perfil/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Reintentar/i })).toBeInTheDocument();
  });

  it('al pulsar Reintentar vuelve a pedir el perfil y lo muestra', async () => {
    client.get.mockRejectedValueOnce(new Error('Network Error')).mockResolvedValueOnce({ data: PERFIL });
    render(<PerfilPage />);
    (await screen.findByRole('button', { name: /Reintentar/i })).click();
    expect(await screen.findByDisplayValue('Dr. Carlos Méndez')).toBeInTheDocument();
    expect(client.get).toHaveBeenCalledTimes(2);
  });

  it('muestra el formulario cuando la carga funciona', async () => {
    client.get.mockResolvedValue({ data: PERFIL });
    render(<PerfilPage />);
    expect(await screen.findByDisplayValue('Dr. Carlos Méndez')).toBeInTheDocument();
    expect(screen.getByText(/@patologo1/)).toBeInTheDocument();
  });
});

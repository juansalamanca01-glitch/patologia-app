import { fireEvent, render, screen } from '@testing-library/react';
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
  registro_medico: 'RM-PRUEBA-0001',
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

// Decisión D-6: al cambiar la contraseña se invalidan las sesiones anteriores y el
// backend devuelve tokens nuevos; la página los guarda para que la sesión siga abierta.
describe('PerfilPage: cambiar contraseña', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    client.get.mockResolvedValue({ data: PERFIL });
  });

  it('guarda los tokens nuevos que devuelve el backend', async () => {
    client.post.mockResolvedValue({ data: { detail: 'ok', access: 'access-nuevo', refresh: 'refresh-nuevo' } });
    const { container } = render(<PerfilPage />);
    await screen.findByDisplayValue('Dr. Carlos Méndez');
    const [actual, nueva, confirmar] = container.querySelectorAll('input[type="password"]');
    fireEvent.change(actual, { target: { value: 'ClaveVieja-2026' } });
    fireEvent.change(nueva, { target: { value: 'Histologia-Segura-2026' } });
    fireEvent.change(confirmar, { target: { value: 'Histologia-Segura-2026' } });
    fireEvent.submit(nueva.closest('form'));
    expect(await screen.findByText('Contraseña actualizada correctamente.')).toBeInTheDocument();
    expect(localStorage.getItem('access_token')).toBe('access-nuevo');
    expect(localStorage.getItem('refresh_token')).toBe('refresh-nuevo');
  });
});

// Informe v2, etapa 6 (decisión D-8): el registro médico lo asigna un administrador.
describe('PerfilPage: registro médico', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('muestra el registro médico sin dejar editarlo y no lo envía al guardar', async () => {
    client.get.mockResolvedValue({ data: PERFIL });
    client.patch.mockResolvedValue({ data: PERFIL });
    render(<PerfilPage />);
    const campo = await screen.findByLabelText('Registro médico');
    expect(campo).toHaveValue('RM-PRUEBA-0001');
    expect(campo).toHaveAttribute('readonly');
    fireEvent.click(screen.getByRole('button', { name: /Guardar cambios/i }));
    await vi.waitFor(() => expect(client.patch).toHaveBeenCalled());
    expect(client.patch.mock.calls[0][1]).not.toHaveProperty('registro_medico');
  });

  it('avisa a un patólogo sin registro médico que no podrá finalizar informes', async () => {
    client.get.mockResolvedValue({ data: { ...PERFIL, registro_medico: '' } });
    render(<PerfilPage />);
    expect(await screen.findByText(/no podrás finalizar informes/i)).toBeInTheDocument();
  });

  it('no muestra el aviso a un auditor', async () => {
    client.get.mockResolvedValue({ data: { ...PERFIL, rol: 'auditor', registro_medico: '' } });
    render(<PerfilPage />);
    await screen.findByLabelText('Registro médico');
    expect(screen.queryByText(/no podrás finalizar informes/i)).not.toBeInTheDocument();
  });
});

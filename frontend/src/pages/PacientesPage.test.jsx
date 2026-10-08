import { fireEvent, render, screen, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import client from '../api/client';
import { reiniciarOpciones } from '../hooks/useOpciones';
import PacientesPage from './PacientesPage';

vi.mock('../api/client', async (importOriginal) => ({
  ...(await importOriginal()),
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
}));

let auth;
vi.mock('../context/AuthContext', () => ({ useAuth: () => auth }));

const PATOLOGO = { canWrite: true, isAdmin: false };
const ADMIN = { canWrite: true, isAdmin: true };
const AUDITOR = { canWrite: false, isAdmin: false };

// Solo datos ficticios (docs/propuesta-informe-v2.md, sección 8).
const PACIENTE = {
  id: 1,
  tipo_documento: 'CC',
  numero_documento: 'PRUEBA0001',
  nombres: 'Paciente Ficticio',
  apellidos: 'Uno',
  fecha_nacimiento: '1980-10-05',
  edad: '45 años',
  sexo: 'femenino',
  eps: 3,
  eps_nombre: 'Particular',
};

const OPCIONES = {
  sexos: [
    { valor: 'femenino', etiqueta: 'Femenino' },
    { valor: 'masculino', etiqueta: 'Masculino' },
  ],
  tipos_documento: [
    { valor: 'CC', etiqueta: 'Cédula de ciudadanía' },
    { valor: 'TI', etiqueta: 'Tarjeta de identidad' },
  ],
  tipos_estudio: [{ valor: 'histologia', etiqueta: 'Histología' }],
};

const pagina = (lista) => ({ data: { count: lista.length, next: null, previous: null, results: lista } });

// Informe v2, etapa 3: pantalla de pacientes. Permisos de la decisión D-11.
describe('PacientesPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    reiniciarOpciones();
    auth = PATOLOGO;
    client.get.mockImplementation((url) => {
      if (url === '/opciones/') return Promise.resolve({ data: OPCIONES });
      if (url === '/pacientes/eps/') return Promise.resolve(pagina([{ id: 3, nombre: 'Particular' }]));
      return Promise.resolve(pagina([PACIENTE]));
    });
    client.post.mockResolvedValue({ data: {} });
    client.put.mockResolvedValue({ data: {} });
    client.delete.mockResolvedValue({ data: {} });
  });

  it('lista los pacientes con documento, edad, sexo y EPS', async () => {
    render(<PacientesPage />);
    const fila = (await screen.findByText('Paciente Ficticio Uno')).closest('tr');
    expect(within(fila).getByText('CC PRUEBA0001')).toBeInTheDocument();
    expect(within(fila).getByText('45 años')).toBeInTheDocument();
    expect(await within(fila).findByText('Femenino')).toBeInTheDocument();
    expect(within(fila).getByText('Particular')).toBeInTheDocument();
  });

  it('busca con ?q=', async () => {
    render(<PacientesPage />);
    await screen.findByText('Paciente Ficticio Uno');
    fireEvent.change(screen.getByLabelText('Buscar'), { target: { value: ' ficticio ' } });
    fireEvent.click(screen.getByRole('button', { name: 'Buscar' }));
    await vi.waitFor(() => expect(client.get).toHaveBeenCalledWith('/pacientes/', { params: { q: 'ficticio' } }));
  });

  it('crea un paciente con los datos del formulario', async () => {
    render(<PacientesPage />);
    fireEvent.click(await screen.findByRole('button', { name: '+ Paciente' }));
    await screen.findByRole('option', { name: 'Particular' });
    fireEvent.change(screen.getByLabelText('Número de documento'), { target: { value: 'PRUEBA0002' } });
    fireEvent.change(screen.getByLabelText('Nombres'), { target: { value: 'Prueba' } });
    fireEvent.change(screen.getByLabelText('Apellidos'), { target: { value: 'Apellido Dos' } });
    fireEvent.change(screen.getByLabelText('Fecha de nacimiento'), { target: { value: '1962-11-03' } });
    fireEvent.change(screen.getByLabelText('Sexo'), { target: { value: 'masculino' } });
    fireEvent.change(screen.getByLabelText('EPS'), { target: { value: '3' } });
    fireEvent.click(screen.getByRole('button', { name: 'Guardar' }));
    await vi.waitFor(() => expect(client.post).toHaveBeenCalled());
    expect(client.post).toHaveBeenCalledWith('/pacientes/', {
      tipo_documento: 'CC',
      numero_documento: 'PRUEBA0002',
      nombres: 'Prueba',
      apellidos: 'Apellido Dos',
      fecha_nacimiento: '1962-11-03',
      sexo: 'masculino',
      eps: 3,
    });
  });

  it('muestra junto al campo el error que devuelve el backend', async () => {
    client.put.mockRejectedValue({
      response: { data: { numero_documento: ['Ya existe un paciente con este tipo y número de documento.'] } },
    });
    render(<PacientesPage />);
    fireEvent.click(await screen.findByRole('button', { name: 'Editar' }));
    expect(screen.getByLabelText('Nombres')).toHaveValue('Paciente Ficticio');
    fireEvent.click(screen.getByRole('button', { name: 'Guardar' }));
    expect(await screen.findByText('Ya existe un paciente con este tipo y número de documento.')).toBeInTheDocument();
    expect(client.put.mock.calls[0][0]).toBe('/pacientes/1/');
  });

  it('al editar, conserva la EPS desactivada que ya tenía el paciente', async () => {
    client.get.mockImplementation((url) => {
      if (url === '/opciones/') return Promise.resolve({ data: OPCIONES });
      if (url === '/pacientes/eps/') return Promise.resolve(pagina([])); // "Particular" ya no está activa
      return Promise.resolve(pagina([PACIENTE]));
    });
    render(<PacientesPage />);
    fireEvent.click(await screen.findByRole('button', { name: 'Editar' }));
    expect(await screen.findByRole('option', { name: 'Particular (desactivada)' })).toBeInTheDocument();
    expect(screen.getByLabelText('EPS')).toHaveValue('3');
  });

  it('el patólogo edita pero no ve "Eliminar"', async () => {
    render(<PacientesPage />);
    expect(await screen.findByRole('button', { name: 'Editar' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Eliminar' })).not.toBeInTheDocument();
  });

  it('el auditor solo lee', async () => {
    auth = AUDITOR;
    render(<PacientesPage />);
    await screen.findByText('Paciente Ficticio Uno');
    expect(screen.queryByRole('button', { name: '+ Paciente' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Editar' })).not.toBeInTheDocument();
  });

  it('el admin elimina y ve el error si el backend lo rechaza', async () => {
    auth = ADMIN;
    client.delete.mockRejectedValue({ response: { data: { detail: 'No se puede eliminar este paciente.' } } });
    render(<PacientesPage />);
    fireEvent.click(await screen.findByRole('button', { name: 'Eliminar' }));
    const modal = screen.getByText('¿Eliminar paciente?').closest('.modal-card');
    fireEvent.click(within(modal).getByRole('button', { name: 'Eliminar' }));
    expect(await screen.findByText('No se puede eliminar este paciente.')).toBeInTheDocument();
    expect(client.delete).toHaveBeenCalledWith('/pacientes/1/');
  });
});

// Informe v2, etapa 4: historial de informes de cada paciente
// (GET /api/pacientes/{id}/informes/).
describe('PacientesPage: historial de informes', () => {
  const INFORME = {
    id: 5,
    numero_peticion: 'P-2026-00001',
    tipo_estudio: 'histologia',
    patologia_nombre: 'Piel',
    fecha: '2026-10-04',
    estado: 'finalizado',
  };

  beforeEach(() => {
    vi.clearAllMocks();
    reiniciarOpciones();
    auth = AUDITOR;
    client.get.mockImplementation((url) => {
      if (url === '/opciones/') return Promise.resolve({ data: OPCIONES });
      if (url === '/pacientes/1/informes/') return Promise.resolve(pagina([INFORME]));
      return Promise.resolve(pagina([PACIENTE]));
    });
  });

  it('cualquier usuario ve los informes de un paciente, con enlace a cada uno', async () => {
    render(
      <MemoryRouter>
        <PacientesPage />
      </MemoryRouter>,
    );
    fireEvent.click(await screen.findByRole('button', { name: 'Informes' }));
    const enlace = await screen.findByRole('link', { name: 'P-2026-00001' });
    expect(enlace).toHaveAttribute('href', '/informes/5');
    const fila = enlace.closest('tr');
    expect(await within(fila).findByText('Histología')).toBeInTheDocument();
    expect(within(fila).getByText('Piel')).toBeInTheDocument();
    expect(within(fila).getByText('Finalizado')).toBeInTheDocument();
    expect(client.get).toHaveBeenCalledWith('/pacientes/1/informes/', { params: { page_size: 1000 } });
  });

  it('avisa si el paciente no tiene informes', async () => {
    client.get.mockImplementation((url) => {
      if (url === '/opciones/') return Promise.resolve({ data: OPCIONES });
      if (url === '/pacientes/1/informes/') return Promise.resolve(pagina([]));
      return Promise.resolve(pagina([PACIENTE]));
    });
    render(
      <MemoryRouter>
        <PacientesPage />
      </MemoryRouter>,
    );
    fireEvent.click(await screen.findByRole('button', { name: 'Informes' }));
    expect(await screen.findByText(/no tiene informes/)).toBeInTheDocument();
  });
});

import { fireEvent, render, screen, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import client from '../api/client';
import CatalogosPage from './CatalogosPage';

vi.mock('../api/client', async (importOriginal) => ({
  ...(await importOriginal()),
  default: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), delete: vi.fn() },
}));

let auth;
vi.mock('../context/AuthContext', () => ({ useAuth: () => auth }));

const pagina = (lista) => ({ data: { count: lista.length, next: null, previous: null, results: lista } });

// Informe v2, etapa 4: pantalla para administrar los catálogos de EPS y servicios.
// Los administran patólogos y admin (D-11); se desactivan en lugar de borrarse (D-4).
describe('CatalogosPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    auth = { canWrite: true };
    client.get.mockImplementation((url) => Promise.resolve(pagina(
      url === '/pacientes/eps/'
        ? [{ id: 3, nombre: 'Particular', activa: true }, { id: 4, nombre: 'EPS Liquidada', activa: false }]
        : [{ id: 8, nombre: 'Urgencias', activo: true }],
    )));
    client.post.mockResolvedValue({ data: {} });
    client.patch.mockResolvedValue({ data: {} });
    client.delete.mockResolvedValue({ data: {} });
  });

  const seccion = async (titulo) => (await screen.findByRole('heading', { name: new RegExp(titulo) })).closest('.card');

  it('lista EPS y servicios, activos e inactivos, con la lista completa', async () => {
    render(<CatalogosPage />);
    const eps = await seccion('EPS');
    expect(await within(eps).findByText('Particular')).toBeInTheDocument();
    expect(within(eps).getByText('EPS Liquidada')).toBeInTheDocument();
    expect(within(eps).getByText('Inactiva')).toBeInTheDocument();
    const servicios = await seccion('Servicios');
    expect(await within(servicios).findByText('Urgencias')).toBeInTheDocument();
    expect(client.get).toHaveBeenCalledWith('/pacientes/eps/', { params: { page_size: 1000 } });
    expect(client.get).toHaveBeenCalledWith('/servicios/', { params: { page_size: 1000 } });
  });

  it('agrega un servicio', async () => {
    render(<CatalogosPage />);
    const servicios = await seccion('Servicios');
    fireEvent.change(within(servicios).getByLabelText('Nuevo servicio'), { target: { value: 'Pediatría' } });
    fireEvent.click(within(servicios).getByRole('button', { name: 'Agregar' }));
    await vi.waitFor(() => expect(client.post).toHaveBeenCalledWith('/servicios/', { nombre: 'Pediatría' }));
  });

  it('desactiva y activa usando el campo de cada catálogo', async () => {
    render(<CatalogosPage />);
    const eps = await seccion('EPS');
    fireEvent.click(await within(eps).findByRole('button', { name: 'Desactivar Particular' }));
    await vi.waitFor(() => expect(client.patch).toHaveBeenCalledWith('/pacientes/eps/3/', { activa: false }));
    fireEvent.click(within(eps).getByRole('button', { name: 'Activar EPS Liquidada' }));
    await vi.waitFor(() => expect(client.patch).toHaveBeenCalledWith('/pacientes/eps/4/', { activa: true }));
    const servicios = await seccion('Servicios');
    fireEvent.click(await within(servicios).findByRole('button', { name: 'Desactivar Urgencias' }));
    await vi.waitFor(() => expect(client.patch).toHaveBeenCalledWith('/servicios/8/', { activo: false }));
  });

  it('cambia el nombre', async () => {
    render(<CatalogosPage />);
    const servicios = await seccion('Servicios');
    fireEvent.click(await within(servicios).findByRole('button', { name: 'Renombrar Urgencias' }));
    fireEvent.change(within(servicios).getByLabelText('Nombre de Urgencias'), { target: { value: 'Urgencias adultos' } });
    fireEvent.click(within(servicios).getByRole('button', { name: 'Guardar' }));
    await vi.waitFor(() => expect(client.patch).toHaveBeenCalledWith('/servicios/8/', { nombre: 'Urgencias adultos' }));
  });

  it('muestra el motivo si el backend no deja borrar (en uso)', async () => {
    client.delete.mockRejectedValue({
      response: { data: { detail: 'No se puede eliminar: este servicio tiene 2 informe(s) asociado(s). Desactívelo en su lugar.' } },
    });
    render(<CatalogosPage />);
    const servicios = await seccion('Servicios');
    fireEvent.click(await within(servicios).findByRole('button', { name: 'Eliminar Urgencias' }));
    fireEvent.click(within(servicios).getByRole('button', { name: 'Confirmar' }));
    expect(await screen.findByText(/Desactívelo en su lugar/)).toBeInTheDocument();
    expect(client.delete).toHaveBeenCalledWith('/servicios/8/');
  });

  it('muestra el error de nombre repetido', async () => {
    client.post.mockRejectedValue({ response: { data: { nombre: ['Ya existe un elemento con este nombre.'] } } });
    render(<CatalogosPage />);
    const eps = await seccion('EPS');
    fireEvent.change(within(eps).getByLabelText('Nueva EPS'), { target: { value: 'particular' } });
    fireEvent.click(within(eps).getByRole('button', { name: 'Agregar' }));
    expect(await within(eps).findByText('Ya existe un elemento con este nombre.')).toBeInTheDocument();
  });

  it('el auditor solo lee', async () => {
    auth = { canWrite: false };
    render(<CatalogosPage />);
    const eps = await seccion('EPS');
    await within(eps).findByText('Particular');
    expect(screen.queryByRole('button', { name: 'Agregar' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Desactivar/ })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Eliminar/ })).not.toBeInTheDocument();
  });
});

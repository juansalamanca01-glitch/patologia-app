import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import client from '../api/client';
import BuscarPage from './BuscarPage';

vi.mock('../api/client', async (importOriginal) => ({
  ...(await importOriginal()),
  default: { get: vi.fn() },
}));

const INFORME = {
  id: 5, numero_peticion: 'P-2026-00001', patologia_nombre: 'Piel', tipo_muestra: '',
  autor_nombre: 'patologo1', fecha: '2026-10-04', estado: 'borrador',
};

// Decisión D-7 de docs/decisiones.md: los informes se identifican y se buscan
// por su número de petición (y por el número de orden externo).
describe('BuscarPage: número de petición', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    client.get.mockResolvedValue({ data: { count: 1, next: null, previous: null, results: [INFORME] } });
  });

  it('el buscador ofrece buscar por número de petición', () => {
    render(<MemoryRouter><BuscarPage /></MemoryRouter>);
    expect(screen.getByLabelText('Buscar')).toHaveAttribute('placeholder', expect.stringMatching(/petición/i));
  });

  it('los resultados muestran el número de petición', async () => {
    render(<MemoryRouter><BuscarPage /></MemoryRouter>);
    fireEvent.change(screen.getByLabelText('Buscar'), { target: { value: 'P-2026' } });
    // Al abrir, la página ya hace una búsqueda: hay que esperar a que el botón vuelva a decir "Buscar".
    fireEvent.click(await screen.findByRole('button', { name: 'Buscar' }));
    expect(await screen.findByText('P-2026-00001')).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /petición/i })).toBeInTheDocument();
  });
});

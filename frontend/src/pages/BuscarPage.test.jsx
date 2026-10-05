import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import client from '../api/client';
import { reiniciarOpciones } from '../hooks/useOpciones';
import BuscarPage from './BuscarPage';

vi.mock('../api/client', async (importOriginal) => ({
  ...(await importOriginal()),
  default: { get: vi.fn() },
}));

const INFORME = {
  id: 5, numero_peticion: 'P-2026-00001', patologia_nombre: 'Piel', tipo_muestra: '',
  autor_nombre: 'patologo1', fecha: '2026-10-04', estado: 'borrador',
  paciente: 1, paciente_nombre: 'Paciente Ficticio Uno', paciente_documento: 'CC PRUEBA0001',
  tipo_estudio: 'histologia',
};

const OPCIONES = { sexos: [], tipos_documento: [], tipos_estudio: [{ valor: 'histologia', etiqueta: 'Histología' }] };

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

// Informe v2, etapa 4: los resultados muestran el paciente y el tipo de estudio,
// y la búsqueda también encuentra por nombre o documento del paciente.
describe('BuscarPage: paciente y tipo de estudio', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    reiniciarOpciones();
    const antiguo = { ...INFORME, id: 6, numero_peticion: 'P-2025-00001', paciente: null, paciente_nombre: null, paciente_documento: null };
    client.get.mockImplementation((url) => Promise.resolve({
      data: url === '/opciones/' ? OPCIONES : { count: 2, next: null, previous: null, results: [INFORME, antiguo] },
    }));
  });

  it('muestra las columnas del informe v2', async () => {
    render(<MemoryRouter><BuscarPage /></MemoryRouter>);
    expect(await screen.findByText('Paciente Ficticio Uno')).toBeInTheDocument();
    const columnas = screen.getAllByRole('columnheader').map((c) => c.textContent).filter(Boolean);
    expect(columnas).toEqual(['N.º de petición', 'Paciente', 'Tipo de estudio', 'Patología', 'Autor', 'Fecha', 'Estado']);
    expect(screen.getByText('CC PRUEBA0001')).toBeInTheDocument();
    expect(await screen.findAllByText('Histología')).toHaveLength(2);
    expect(screen.getByText('No registrado')).toBeInTheDocument();
  });

  it('el buscador ofrece buscar por paciente', () => {
    render(<MemoryRouter><BuscarPage /></MemoryRouter>);
    expect(screen.getByLabelText('Buscar')).toHaveAttribute('placeholder', expect.stringMatching(/paciente/i));
  });
});

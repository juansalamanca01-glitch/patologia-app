import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import client from '../../api/client';
import { reiniciarOpciones } from '../../hooks/useOpciones';
import SelectorPaciente from './SelectorPaciente';

vi.mock('../../api/client', async (importOriginal) => ({
  ...(await importOriginal()),
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn() },
}));

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
  tipos_documento: [{ valor: 'CC', etiqueta: 'Cédula de ciudadanía' }],
  tipos_estudio: [],
};

const pagina = (lista) => ({ data: { count: lista.length, next: null, previous: null, results: lista } });

// Informe v2, etapa 4: el informe se asocia a un paciente que se busca por
// documento o nombre, o que se crea en el momento.
describe('SelectorPaciente', () => {
  let onSeleccionar;

  beforeEach(() => {
    vi.clearAllMocks();
    reiniciarOpciones();
    onSeleccionar = vi.fn();
    client.get.mockImplementation((url) => {
      if (url === '/opciones/') return Promise.resolve({ data: OPCIONES });
      if (url === '/pacientes/eps/') return Promise.resolve(pagina([{ id: 3, nombre: 'Particular' }]));
      return Promise.resolve(pagina([PACIENTE]));
    });
  });

  it('busca pacientes por documento o nombre y permite seleccionar uno', async () => {
    render(<SelectorPaciente paciente={null} onSeleccionar={onSeleccionar} />);
    fireEvent.change(screen.getByLabelText('Buscar paciente'), { target: { value: ' PRUEBA0001 ' } });
    fireEvent.click(screen.getByRole('button', { name: 'Buscar' }));
    await vi.waitFor(() => expect(client.get).toHaveBeenCalledWith('/pacientes/', { params: { q: 'PRUEBA0001' } }));
    fireEvent.click(await screen.findByRole('button', { name: /Seleccionar/ }));
    expect(onSeleccionar).toHaveBeenCalledWith(
      expect.objectContaining({
        id: 1,
        nombre_completo: 'Paciente Ficticio Uno',
        numero_documento: 'PRUEBA0001',
        eps: 3,
      }),
    );
  });

  it('Enter en la búsqueda busca y no envía el formulario del informe', async () => {
    const enviar = vi.fn((e) => e.preventDefault());
    render(
      <form onSubmit={enviar}>
        <SelectorPaciente paciente={null} onSeleccionar={onSeleccionar} />
      </form>,
    );
    fireEvent.change(screen.getByLabelText('Buscar paciente'), { target: { value: 'ficticio' } });
    fireEvent.keyDown(screen.getByLabelText('Buscar paciente'), { key: 'Enter' });
    await vi.waitFor(() => expect(client.get).toHaveBeenCalledWith('/pacientes/', { params: { q: 'ficticio' } }));
    expect(enviar).not.toHaveBeenCalled();
  });

  it('avisa si la búsqueda no encuentra pacientes', async () => {
    client.get.mockResolvedValue(pagina([]));
    render(<SelectorPaciente paciente={null} onSeleccionar={onSeleccionar} />);
    fireEvent.change(screen.getByLabelText('Buscar paciente'), { target: { value: 'nadie' } });
    fireEvent.click(screen.getByRole('button', { name: 'Buscar' }));
    expect(await screen.findByText(/No se encontraron pacientes/)).toBeInTheDocument();
  });

  it('crea un paciente nuevo y lo deja seleccionado', async () => {
    client.post.mockResolvedValue({ data: { ...PACIENTE, id: 7, numero_documento: 'PRUEBA0007' } });
    render(<SelectorPaciente paciente={null} onSeleccionar={onSeleccionar} />);
    fireEvent.click(screen.getByRole('button', { name: 'Nuevo paciente' }));
    await screen.findByRole('option', { name: 'Particular' });
    fireEvent.change(screen.getByLabelText('Número de documento'), { target: { value: 'PRUEBA0007' } });
    fireEvent.change(screen.getByLabelText('Nombres'), { target: { value: 'Paciente Ficticio' } });
    fireEvent.change(screen.getByLabelText('Apellidos'), { target: { value: 'Uno' } });
    fireEvent.change(screen.getByLabelText('Fecha de nacimiento'), { target: { value: '1980-10-05' } });
    fireEvent.change(screen.getByLabelText('Sexo'), { target: { value: 'femenino' } });
    fireEvent.click(screen.getByRole('button', { name: 'Guardar' }));
    await vi.waitFor(() => expect(onSeleccionar).toHaveBeenCalledWith(expect.objectContaining({ id: 7 })));
    expect(client.post.mock.calls[0][0]).toBe('/pacientes/');
  });

  it('muestra el paciente seleccionado y permite cambiarlo', async () => {
    const seleccionado = {
      id: 1,
      nombre_completo: 'Paciente Ficticio Uno',
      tipo_documento: 'CC',
      numero_documento: 'PRUEBA0001',
      sexo: 'femenino',
      edad: '45 años',
    };
    render(<SelectorPaciente paciente={seleccionado} onSeleccionar={onSeleccionar} />);
    expect(screen.getByText('Paciente Ficticio Uno')).toBeInTheDocument();
    expect(screen.getByText('CC PRUEBA0001')).toBeInTheDocument();
    expect(screen.getByText('45 años')).toBeInTheDocument();
    expect(await screen.findByText('Femenino')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Cambiar' }));
    expect(screen.getByLabelText('Buscar paciente')).toBeInTheDocument();
  });

  it('en solo lectura no permite cambiar el paciente', () => {
    const seleccionado = {
      id: 1,
      nombre_completo: 'Paciente Ficticio Uno',
      tipo_documento: 'CC',
      numero_documento: 'PRUEBA0001',
    };
    render(<SelectorPaciente paciente={seleccionado} onSeleccionar={onSeleccionar} disabled />);
    expect(screen.queryByRole('button', { name: 'Cambiar' })).not.toBeInTheDocument();
  });

  it('un informe antiguo sin paciente en solo lectura dice "No registrado"', () => {
    render(<SelectorPaciente paciente={null} onSeleccionar={onSeleccionar} disabled />);
    expect(screen.getByText('No registrado')).toBeInTheDocument();
    expect(screen.queryByLabelText('Buscar paciente')).not.toBeInTheDocument();
  });
});

// Prueba manual del 2026-10-05 (Pendientes, punto 1): en pantalla, cada dato del
// paciente salía pegado a su etiqueta ("PacientePaciente Ficticio Uno"). Cada dato
// es ahora un par etiqueta–valor (<dt>/<dd>), separado aunque falte el CSS.
describe('SelectorPaciente: datos del paciente seleccionado', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    reiniciarOpciones();
    client.get.mockImplementation((url) =>
      url === '/opciones/' ? Promise.resolve({ data: OPCIONES }) : Promise.resolve(pagina([])),
    );
  });

  it('cada dato va separado de su etiqueta', async () => {
    const seleccionado = { ...PACIENTE, nombre_completo: 'Paciente Ficticio Uno' };
    render(<SelectorPaciente paciente={seleccionado} onSeleccionar={vi.fn()} />);
    await screen.findByText('Femenino');
    expect(screen.getAllByRole('term').map((t) => t.textContent)).toEqual([
      'Paciente',
      'Identificación',
      'Edad',
      'Sexo',
    ]);
    expect(screen.getAllByRole('definition').map((d) => d.textContent)).toEqual([
      'Paciente Ficticio Uno',
      'CC PRUEBA0001',
      '45 años',
      'Femenino',
    ]);
  });
});

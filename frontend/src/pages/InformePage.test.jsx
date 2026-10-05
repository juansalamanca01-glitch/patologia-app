import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import client from '../api/client';
import { reiniciarOpciones } from '../hooks/useOpciones';
import InformePage from './InformePage';

// Se simula solo el cliente; resultados() y el resto del módulo son los reales.
vi.mock('../api/client', async (importOriginal) => ({
  ...(await importOriginal()),
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
}));

vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({ user: { id: 1, rol: 'patologo' }, canWrite: true, isAdmin: false }),
}));

const INFORME = {
  id: 5,
  numero_peticion: 'P-2026-00001',
  numero_orden_externa: 'ORD-9',
  // Solo datos ficticios (docs/propuesta-informe-v2.md, sección 8).
  paciente: 1,
  paciente_datos: {
    id: 1, nombre_completo: 'Paciente Ficticio Uno', tipo_documento: 'CC', numero_documento: 'PRUEBA0001',
    fecha_nacimiento: '1980-10-05', sexo: 'femenino', edad: '45 años',
  },
  medico_tratante: 'Médico Ficticio',
  fecha_ingreso: '2026-10-01',
  eps: 4,
  eps_nombre: 'EPS Liquidada',
  servicio: 8,
  servicio_nombre: 'Urgencias',
  estudios_solicitados: 'Biopsia de piel',
  tipo_estudio: 'citologia_no_ginecologica',
  patologia: 1,
  autor: 1,
  estado: 'borrador',
  tipo_muestra: '',
  descripcion_microscopica: 'Nidos de células basaloides.',
  diagnosticos: [
    { orden: 1, descripcion: 'Carcinoma basocelular nodular', codigo_cie10: 'C44.3' },
    { orden: 2, descripcion: 'Márgenes libres de lesión', codigo_cie10: '' },
  ],
  comentarios: 'Se sugiere correlación clínica.',
  datos_ingresados: {},
  texto_generado: '',
};

const OPCIONES = {
  sexos: [{ valor: 'femenino', etiqueta: 'Femenino' }],
  tipos_documento: [{ valor: 'CC', etiqueta: 'Cédula de ciudadanía' }],
  tipos_estudio: [
    { valor: 'histologia', etiqueta: 'Histología' },
    { valor: 'citologia_no_ginecologica', etiqueta: 'Citología no ginecológica' },
  ],
};

const PACIENTE = {
  id: 1, tipo_documento: 'CC', numero_documento: 'PRUEBA0001', nombres: 'Paciente Ficticio',
  apellidos: 'Uno', fecha_nacimiento: '1980-10-05', edad: '45 años', sexo: 'femenino',
  eps: 3, eps_nombre: 'Particular',
};

// Simula las respuestas de la API según la URL pedida.
function simularApi() {
  client.get.mockImplementation((url) => {
    if (url === '/opciones/') return Promise.resolve({ data: OPCIONES });
    // EPS y servicios activos: "EPS Liquidada" (la del informe guardado) ya no está activa.
    if (url === '/pacientes/eps/') return Promise.resolve({ data: { results: [{ id: 3, nombre: 'Particular', activa: true }] } });
    if (url === '/servicios/') return Promise.resolve({ data: { results: [{ id: 8, nombre: 'Urgencias', activo: true }] } });
    if (url === '/pacientes/') return Promise.resolve({ data: { results: [PACIENTE] } });
    if (url === '/patologias/') return Promise.resolve({ data: { results: [{ id: 1, nombre: 'Piel', activa: true }] } });
    if (url === '/informes/5/') return Promise.resolve({ data: INFORME });
    if (url === '/patologias/1/') return Promise.resolve({ data: { plantillas: [] } });
    if (url === '/informes/5/pdf/') return Promise.resolve({ data: new Blob(['%PDF'], { type: 'application/pdf' }) });
    return Promise.reject(new Error(`URL no simulada: ${url}`));
  });
}

function renderInforme() {
  return render(
    <MemoryRouter initialEntries={['/informes/5']}>
      <Routes>
        <Route path="/informes/:id" element={<InformePage />} />
      </Routes>
    </MemoryRouter>,
  );
}

// Hallazgo I-5 de docs/auditoria-inicial.md: el PDF se descargaba armando una
// URL con ?token=<access_token>, que queda en el historial y en los registros.
describe('InformePage: exportar PDF', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem('access_token', 'token-secreto');
    URL.createObjectURL = vi.fn(() => 'blob:pdf');
    URL.revokeObjectURL = vi.fn();
    simularApi();
  });

  it('pide el PDF con Axios (token en la cabecera) y no pone el token en una URL', async () => {
    const submitSpy = vi.spyOn(HTMLFormElement.prototype, 'submit').mockImplementation(() => {});
    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
    renderInforme();

    (await screen.findByRole('button', { name: /Exportar PDF/i })).click();

    await vi.waitFor(() => {
      expect(client.get).toHaveBeenCalledWith('/informes/5/pdf/', { responseType: 'blob' });
    });
    expect(submitSpy).not.toHaveBeenCalled();
    expect(document.querySelector('input[name="token"]')).toBeNull();
    // El archivo se entrega con un enlace temporal "blob:" y el número de petición (D-7).
    expect(clickSpy).toHaveBeenCalled();
    const enlace = clickSpy.mock.contexts[0];
    expect(enlace.href).toBe('blob:pdf');
    expect(enlace.download).toBe('informe_P-2026-00001.pdf');
  });
});

// El selector de patologías pide la lista completa (no solo 20). Al crear un
// informe ofrece solo las activas (decisión D-4); al editar, todas, para que se
// vea la patología de un informe viejo aunque ya esté desactivada.
describe('InformePage: selector de patologías', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    simularApi();
  });

  it('al crear un informe pide todas las patologías activas', async () => {
    render(
      <MemoryRouter initialEntries={['/informes/nuevo']}>
        <Routes>
          <Route path="/informes/nuevo" element={<InformePage />} />
        </Routes>
      </MemoryRouter>,
    );
    await vi.waitFor(() => {
      expect(client.get).toHaveBeenCalledWith('/patologias/', { params: { page_size: 1000, activa: 'true' } });
    });
  });

  it('al editar un informe pide todas las patologías, también las inactivas', async () => {
    renderInforme();
    await vi.waitFor(() => {
      expect(client.get).toHaveBeenCalledWith('/patologias/', { params: { page_size: 1000 } });
    });
  });
});

// Hallazgo M-9 de docs/auditoria-inicial.md: si fallaba la carga de las patologías
// o de los campos de la plantilla, el formulario quedaba vacío sin ningún aviso.
describe('InformePage: errores visibles', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('avisa si no se pueden cargar las patologías', async () => {
    client.get.mockRejectedValue(new Error('Network Error'));
    render(
      <MemoryRouter initialEntries={['/informes/nuevo']}>
        <Routes>
          <Route path="/informes/nuevo" element={<InformePage />} />
        </Routes>
      </MemoryRouter>,
    );
    expect(await screen.findByText(/No se pudieron cargar las patologías/i)).toBeInTheDocument();
  });

  it('avisa si no se pueden cargar los campos de la patología', async () => {
    simularApi();
    const simulacion = client.get.getMockImplementation();
    client.get.mockImplementation((url, ...resto) => (
      url === '/patologias/1/' ? Promise.reject(new Error('Network Error')) : simulacion(url, ...resto)
    ));
    renderInforme();
    expect(await screen.findByText(/No se pudieron cargar los campos de la patología/i)).toBeInTheDocument();
  });
});

// Busca y selecciona el paciente ficticio en el SelectorPaciente.
async function seleccionarPaciente() {
  fireEvent.change(screen.getByLabelText('Buscar paciente'), { target: { value: 'PRUEBA0001' } });
  fireEvent.click(screen.getByRole('button', { name: 'Buscar' }));
  fireEvent.click(await screen.findByRole('button', { name: /Seleccionar/ }));
}

// Decisión D-7 de docs/decisiones.md: el número de petición lo asigna el sistema
// al guardar. El formulario ya no pide número de caso; sí permite anotar el
// número de orden externo de la institución remitente (opcional).
describe('InformePage: número de petición', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    simularApi();
  });

  function renderNuevo() {
    return render(
      <MemoryRouter initialEntries={['/informes/nuevo']}>
        <Routes>
          <Route path="/informes/nuevo" element={<InformePage />} />
        </Routes>
      </MemoryRouter>,
    );
  }

  it('un informe nuevo no pide número de caso', async () => {
    renderNuevo();
    await screen.findByRole('option', { name: 'Piel' });
    expect(screen.queryByLabelText(/Número de caso/i)).toBeNull();
  });

  it('al guardar envía la orden externa y no envía número de caso', async () => {
    client.post.mockResolvedValue({ data: { id: 9, numero_peticion: 'P-2026-00002' } });
    renderNuevo();
    await screen.findByRole('option', { name: 'Piel' });
    await seleccionarPaciente();
    fireEvent.change(screen.getByLabelText(/Tipo de Patología/i), { target: { value: '1' } });
    fireEvent.change(screen.getByLabelText(/orden externa/i), { target: { value: 'ORD-1' } });
    fireEvent.click(screen.getByRole('button', { name: /Guardar Informe/i }));

    await vi.waitFor(() => expect(client.post).toHaveBeenCalled());
    const [url, datos] = client.post.mock.calls[0];
    expect(url).toBe('/informes/');
    expect(datos).not.toHaveProperty('numero_caso');
    expect(datos.numero_orden_externa).toBe('ORD-1');
  });

  it('un informe guardado muestra su número de petición y su orden externa', async () => {
    renderInforme();
    expect(await screen.findByRole('heading', { name: /Informe P-2026-00001/ })).toBeInTheDocument();
    expect(screen.getByLabelText(/orden externa/i)).toHaveValue('ORD-9');
  });
});

// Informe v2, etapa 4 (docs/propuesta-informe-v2.md, 6.3): el formulario sigue el
// orden del informe real: Paciente, Datos de la solicitud y Estudio.
describe('InformePage: paciente y datos de la solicitud', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    reiniciarOpciones();
    simularApi();
  });

  function renderNuevo() {
    return render(
      <MemoryRouter initialEntries={['/informes/nuevo']}>
        <Routes>
          <Route path="/informes/nuevo" element={<InformePage />} />
        </Routes>
      </MemoryRouter>,
    );
  }

  it('muestra las tarjetas en el orden del informe real', async () => {
    renderNuevo();
    await screen.findByRole('option', { name: 'Piel' });
    const titulos = screen.getAllByRole('heading', { level: 2 }).map((h) => h.textContent);
    expect(titulos.slice(0, 3)).toEqual(['Paciente', 'Datos de la solicitud', 'Estudio']);
  });

  it('un informe nuevo empieza con la fecha de hoy y el tipo de estudio Histología', async () => {
    renderNuevo();
    expect(await screen.findByRole('option', { name: 'Histología' })).toBeInTheDocument();
    expect(screen.getByLabelText('Fecha de ingreso')).toHaveValue(new Date().toLocaleDateString('en-CA'));
    expect(screen.getByLabelText('Tipo de estudio')).toHaveValue('histologia');
  });

  it('no deja guardar sin paciente', async () => {
    renderNuevo();
    await screen.findByRole('option', { name: 'Piel' });
    fireEvent.change(screen.getByLabelText(/Tipo de Patología/i), { target: { value: '1' } });
    fireEvent.click(screen.getByRole('button', { name: /Guardar Informe/i }));
    expect(await screen.findByText('Seleccione un paciente.')).toBeInTheDocument();
    expect(client.post).not.toHaveBeenCalled();
  });

  it('al elegir el paciente precarga su EPS y al guardar envía los datos de la solicitud', async () => {
    client.post.mockResolvedValue({ data: { id: 9, numero_peticion: 'P-2026-00002' } });
    renderNuevo();
    await screen.findByRole('option', { name: 'Piel' });
    await screen.findByRole('option', { name: 'Urgencias' });
    await seleccionarPaciente();
    expect(screen.getByLabelText('EPS')).toHaveValue('3');
    fireEvent.change(screen.getByLabelText('Médico tratante'), { target: { value: 'Médico Ficticio' } });
    fireEvent.change(screen.getByLabelText('Fecha de ingreso'), { target: { value: '2026-10-01' } });
    fireEvent.change(screen.getByLabelText('Servicio'), { target: { value: '8' } });
    fireEvent.change(screen.getByLabelText('Estudios solicitados'), { target: { value: 'Biopsia de piel' } });
    fireEvent.change(screen.getByLabelText('Tipo de estudio'), { target: { value: 'citologia_no_ginecologica' } });
    fireEvent.change(screen.getByLabelText(/Tipo de Patología/i), { target: { value: '1' } });
    fireEvent.click(screen.getByRole('button', { name: /Guardar Informe/i }));

    await vi.waitFor(() => expect(client.post).toHaveBeenCalled());
    expect(client.post.mock.calls[0][1]).toMatchObject({
      paciente: 1, medico_tratante: 'Médico Ficticio', fecha_ingreso: '2026-10-01', eps: 3, servicio: 8,
      estudios_solicitados: 'Biopsia de piel', tipo_estudio: 'citologia_no_ginecologica', patologia: 1,
    });
  });

  it('al editar carga el paciente y los datos de la solicitud, y conserva la EPS desactivada', async () => {
    renderInforme();
    expect(await screen.findByText('Paciente Ficticio Uno')).toBeInTheDocument();
    expect(screen.getByText('CC PRUEBA0001')).toBeInTheDocument();
    expect(screen.getByLabelText('Médico tratante')).toHaveValue('Médico Ficticio');
    expect(screen.getByLabelText('Fecha de ingreso')).toHaveValue('2026-10-01');
    expect(await screen.findByRole('option', { name: 'EPS Liquidada (desactivada)' })).toBeInTheDocument();
    expect(screen.getByLabelText('EPS')).toHaveValue('4');
    expect(screen.getByLabelText('Servicio')).toHaveValue('8');
    expect(screen.getByLabelText('Estudios solicitados')).toHaveValue('Biopsia de piel');
    expect(await screen.findByRole('option', { name: 'Citología no ginecológica' })).toBeInTheDocument();
    expect(screen.getByLabelText('Tipo de estudio')).toHaveValue('citologia_no_ginecologica');
  });
});

// Informe v2, etapa 5 (docs/propuesta-informe-v2.md, 3.4, 3.6 y 6.3): descripción
// microscópica, diagnósticos con CIE-10 y comentarios (antes "notas", P-5).
describe('InformePage: contenido del informe', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    reiniciarOpciones();
    simularApi();
  });

  function renderNuevo() {
    return render(
      <MemoryRouter initialEntries={['/informes/nuevo']}>
        <Routes>
          <Route path="/informes/nuevo" element={<InformePage />} />
        </Routes>
      </MemoryRouter>,
    );
  }

  it('muestra las tarjetas del contenido en el orden del informe real', async () => {
    renderNuevo();
    await screen.findByRole('option', { name: 'Piel' });
    const titulos = screen.getAllByRole('heading', { level: 2 }).map((h) => h.textContent);
    expect(titulos).toEqual([
      'Paciente', 'Datos de la solicitud', 'Estudio',
      'Descripción microscópica', 'Diagnósticos', 'Comentarios',
    ]);
    expect(screen.queryByText(/Notas/i)).toBeNull();
  });

  it('al guardar envía la microscópica, los diagnósticos en orden y los comentarios', async () => {
    client.post.mockResolvedValue({ data: { id: 9, numero_peticion: 'P-2026-00002' } });
    renderNuevo();
    await screen.findByRole('option', { name: 'Piel' });
    await seleccionarPaciente();
    fireEvent.change(screen.getByLabelText(/Tipo de Patología/i), { target: { value: '1' } });
    fireEvent.change(screen.getByLabelText('Descripción microscópica'), { target: { value: 'Nidos basaloides.' } });
    fireEvent.click(screen.getByRole('button', { name: /Agregar diagnóstico/ }));
    fireEvent.change(screen.getByLabelText('Diagnóstico 1'), { target: { value: 'Carcinoma basocelular' } });
    fireEvent.change(screen.getByLabelText('CIE-10 del diagnóstico 1'), { target: { value: 'C44.3' } });
    fireEvent.change(screen.getByLabelText('Comentarios'), { target: { value: 'Correlación clínica.' } });
    fireEvent.click(screen.getByRole('button', { name: /Guardar Informe/i }));

    await vi.waitFor(() => expect(client.post).toHaveBeenCalled());
    const datos = client.post.mock.calls[0][1];
    expect(datos).toMatchObject({
      descripcion_microscopica: 'Nidos basaloides.',
      diagnosticos: [{ descripcion: 'Carcinoma basocelular', codigo_cie10: 'C44.3' }],
      comentarios: 'Correlación clínica.',
    });
    expect(datos).not.toHaveProperty('notas');
    expect(datos.diagnosticos[0]).not.toHaveProperty('clave');
  });

  it('no deja guardar un diagnóstico sin descripción', async () => {
    renderNuevo();
    await screen.findByRole('option', { name: 'Piel' });
    await seleccionarPaciente();
    fireEvent.change(screen.getByLabelText(/Tipo de Patología/i), { target: { value: '1' } });
    fireEvent.click(screen.getByRole('button', { name: /Agregar diagnóstico/ }));
    fireEvent.click(screen.getByRole('button', { name: /Guardar Informe/i }));
    expect(await screen.findByText('Escriba la descripción del diagnóstico.')).toBeInTheDocument();
    expect(client.post).not.toHaveBeenCalled();
  });

  it('al editar carga la microscópica, los diagnósticos y los comentarios', async () => {
    renderInforme();
    expect(await screen.findByLabelText('Descripción microscópica')).toHaveValue('Nidos de células basaloides.');
    expect(screen.getByLabelText('Diagnóstico 1')).toHaveValue('Carcinoma basocelular nodular');
    expect(screen.getByLabelText('CIE-10 del diagnóstico 1')).toHaveValue('C44.3');
    expect(screen.getByLabelText('Diagnóstico 2')).toHaveValue('Márgenes libres de lesión');
    expect(screen.getByLabelText('Comentarios')).toHaveValue('Se sugiere correlación clínica.');
  });

  it('muestra junto a la fila el error del backend en un diagnóstico', async () => {
    client.put.mockRejectedValue({
      response: { data: { diagnosticos: [{}, { codigo_cie10: ['Código CIE-10 no válido.'] }] } },
    });
    renderInforme();
    await screen.findByLabelText('Diagnóstico 2');
    fireEvent.click(screen.getByRole('button', { name: /Actualizar Informe/i }));
    expect(await screen.findByText('Código CIE-10 no válido.')).toBeInTheDocument();
  });
});

import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import client from '../api/client';
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
  patologia: 1,
  autor: 1,
  estado: 'borrador',
  tipo_muestra: '',
  notas: '',
  datos_ingresados: {},
  texto_generado: '',
};

// Simula las respuestas de la API según la URL pedida.
function simularApi() {
  client.get.mockImplementation((url) => {
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

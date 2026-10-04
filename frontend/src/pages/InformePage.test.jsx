import { render, screen } from '@testing-library/react';
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
  numero_caso: 'PAT-2026-0001',
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
    if (url === '/patologias/') return Promise.resolve({ data: { results: [] } });
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
    // El archivo se entrega con un enlace temporal "blob:" y el nombre del caso.
    expect(clickSpy).toHaveBeenCalled();
    const enlace = clickSpy.mock.contexts[0];
    expect(enlace.href).toBe('blob:pdf');
    expect(enlace.download).toBe('informe_PAT-2026-0001.pdf');
  });
});

// Los listados vienen de 20 en 20: el selector de patologías pide la lista completa.
describe('InformePage: selector de patologías', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    simularApi();
  });

  it('pide todas las patologías, no solo la primera página de 20', async () => {
    render(
      <MemoryRouter initialEntries={['/informes/nuevo']}>
        <Routes>
          <Route path="/informes/nuevo" element={<InformePage />} />
        </Routes>
      </MemoryRouter>,
    );
    await vi.waitFor(() => {
      expect(client.get).toHaveBeenCalledWith('/patologias/', { params: { page_size: 1000 } });
    });
  });
});

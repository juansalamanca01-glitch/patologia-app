import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import client from '../../api/client';
import SeccionAdendas from './SeccionAdendas';

vi.mock('../../api/client', async (importOriginal) => ({
  ...(await importOriginal()),
  default: { get: vi.fn(), post: vi.fn() },
}));

// Solo datos ficticios (docs/propuesta-informe-v2.md, sección 8).
const FIRMA = { nombre: 'Dra. Ficticia Firma', especialidad: 'Patología Quirúrgica', registro_medico: 'RM-PRUEBA-0001' };
const ADENDA = {
  id: 1, numero: 1, motivo: 'Corrección del diagnóstico', texto: 'Se aclara el diagnóstico.',
  autor: 1, fecha: '2026-10-05T14:15:00Z', firma: FIRMA,
};

function dibujar(props = {}) {
  const onAgregada = vi.fn();
  render(
    <SeccionAdendas informeId={5} estado="finalizado" adendas={[ADENDA]} puedeAgregar onAgregada={onAgregada} {...props} />,
  );
  return onAgregada;
}

function llenarYGuardar(motivo = 'Resultado de inmunohistoquímica', texto = 'CK5/6 positivo.') {
  fireEvent.click(screen.getByRole('button', { name: /Agregar adenda/i }));
  fireEvent.change(screen.getByLabelText(/Motivo/), { target: { value: motivo } });
  fireEvent.change(screen.getByLabelText(/Texto/), { target: { value: texto } });
  fireEvent.click(screen.getByRole('button', { name: 'Guardar adenda' }));
}

describe('SeccionAdendas (informe v2, etapa 8)', () => {
  beforeEach(() => vi.clearAllMocks());

  it('muestra cada adenda con número, fecha, motivo, texto y firma', () => {
    dibujar();
    // 14:15 UTC son las 9:15 en Bogotá.
    expect(screen.getByText(/Adenda N\.º 1/)).toHaveTextContent(/05\/10\/2026.*9:15/);
    expect(screen.getByText('Corrección del diagnóstico')).toBeInTheDocument();
    expect(screen.getByText('Se aclara el diagnóstico.')).toBeInTheDocument();
    expect(screen.getByText('Dra. Ficticia Firma')).toBeInTheDocument();
    expect(screen.getByText(/Registro médico N\.º RM-PRUEBA-0001/)).toBeInTheDocument();
  });

  it('en un borrador no se muestra', () => {
    const { container } = render(
      <SeccionAdendas informeId={5} estado="borrador" adendas={[]} puedeAgregar onAgregada={vi.fn()} />,
    );
    expect(container).toBeEmptyDOMElement();
  });

  it('sin permiso no ofrece agregar, y sin adendas no muestra nada', () => {
    dibujar({ puedeAgregar: false });
    expect(screen.queryByRole('button', { name: /Agregar adenda/i })).not.toBeInTheDocument();
    expect(screen.getByText('Corrección del diagnóstico')).toBeInTheDocument();

    const { container } = render(
      <SeccionAdendas informeId={5} estado="finalizado" adendas={[]} puedeAgregar={false} onAgregada={vi.fn()} />,
    );
    expect(container).toBeEmptyDOMElement();
  });

  it('pide confirmación antes de guardar, porque una adenda no se modifica', async () => {
    const nueva = { ...ADENDA, id: 2, numero: 2, motivo: 'Resultado de inmunohistoquímica', texto: 'CK5/6 positivo.' };
    client.post.mockResolvedValue({ data: nueva });
    const onAgregada = dibujar();
    llenarYGuardar();
    expect(client.post).not.toHaveBeenCalled();
    expect(screen.getByText(/no se pueden modificar ni borrar/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Sí, guardar adenda/i }));
    expect(await screen.findByText('Adenda agregada correctamente.')).toBeInTheDocument();
    expect(client.post).toHaveBeenCalledWith('/informes/5/adendas/', {
      motivo: 'Resultado de inmunohistoquímica', texto: 'CK5/6 positivo.',
    });
    expect(onAgregada).toHaveBeenCalledWith(nueva);
    // El formulario se cierra.
    expect(screen.queryByLabelText(/Motivo/)).not.toBeInTheDocument();
  });

  it('volver de la confirmación conserva lo escrito y no guarda', () => {
    dibujar();
    llenarYGuardar();
    fireEvent.click(screen.getByRole('button', { name: 'Volver' }));
    expect(screen.getByLabelText(/Motivo/)).toHaveValue('Resultado de inmunohistoquímica');
    expect(client.post).not.toHaveBeenCalled();
  });

  it('no deja guardar sin motivo ni texto', () => {
    dibujar();
    llenarYGuardar('  ', '');
    expect(screen.getByText('Escriba el motivo de la adenda.')).toBeInTheDocument();
    expect(screen.getByText('Escriba el texto de la adenda.')).toBeInTheDocument();
    expect(screen.queryByText(/no se pueden modificar ni borrar/)).not.toBeInTheDocument();
  });

  it('muestra el error del backend (por ejemplo, sin registro médico)', async () => {
    client.post.mockRejectedValue({
      response: { status: 400, data: { detail: 'Para firmar una adenda necesita registro médico; un administrador debe registrarlo.' } },
    });
    const onAgregada = dibujar();
    llenarYGuardar();
    fireEvent.click(screen.getByRole('button', { name: /Sí, guardar adenda/i }));
    expect(await screen.findByText(/necesita registro médico/)).toBeInTheDocument();
    expect(onAgregada).not.toHaveBeenCalled();
    // Lo escrito no se pierde.
    expect(screen.getByLabelText(/Motivo/)).toHaveValue('Resultado de inmunohistoquímica');
  });

  it('muestra junto al campo los errores de validación del backend', async () => {
    client.post.mockRejectedValue({
      response: { status: 400, data: { motivo: ['Asegúrese de que este campo no tenga más de 300 caracteres.'] } },
    });
    dibujar();
    llenarYGuardar();
    fireEvent.click(screen.getByRole('button', { name: /Sí, guardar adenda/i }));
    expect(await screen.findByText(/no tenga más de 300 caracteres/)).toBeInTheDocument();
  });
});

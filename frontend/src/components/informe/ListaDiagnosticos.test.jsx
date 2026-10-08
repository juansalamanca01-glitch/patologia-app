import { useState } from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import ListaDiagnosticos, { conClaves, sinClaves } from './ListaDiagnosticos';

// Envoltorio con estado: ListaDiagnosticos es un componente controlado.
function Prueba({ inicial = [], disabled = false, error }) {
  const [lista, setLista] = useState(conClaves(inicial));
  return (
    <>
      <ListaDiagnosticos diagnosticos={lista} onCambiar={setLista} disabled={disabled} error={error} />
      <output data-testid="lista">{JSON.stringify(sinClaves(lista))}</output>
    </>
  );
}

const lista = () => JSON.parse(screen.getByTestId('lista').textContent);

const DOS = [
  { descripcion: 'Carcinoma basocelular nodular', codigo_cie10: 'C44.3' },
  { descripcion: 'Márgenes libres de lesión', codigo_cie10: '' },
];

// Informe v2, etapa 5 (docs/propuesta-informe-v2.md, 3.6 y 6.3): filas con
// descripción y CIE-10 opcional, para agregar, quitar y reordenar.
describe('ListaDiagnosticos', () => {
  it('sin diagnósticos muestra un aviso y permite agregar uno', () => {
    render(<Prueba />);
    expect(screen.getByText(/Todavía no hay diagnósticos/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /Agregar diagnóstico/ }));
    fireEvent.change(screen.getByLabelText('Diagnóstico 1'), { target: { value: 'Nevus intradérmico' } });
    fireEvent.change(screen.getByLabelText('CIE-10 del diagnóstico 1'), { target: { value: 'D22.5' } });
    expect(lista()).toEqual([{ descripcion: 'Nevus intradérmico', codigo_cie10: 'D22.5' }]);
  });

  it('sube, baja y quita diagnósticos', () => {
    render(<Prueba inicial={DOS} />);
    expect(screen.getByRole('button', { name: 'Subir diagnóstico 1' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Bajar diagnóstico 2' })).toBeDisabled();

    fireEvent.click(screen.getByRole('button', { name: 'Subir diagnóstico 2' }));
    expect(lista().map((d) => d.descripcion)).toEqual(['Márgenes libres de lesión', 'Carcinoma basocelular nodular']);
    expect(screen.getByLabelText('Diagnóstico 1')).toHaveValue('Márgenes libres de lesión');

    fireEvent.click(screen.getByRole('button', { name: 'Bajar diagnóstico 1' }));
    expect(lista()).toEqual(DOS);

    fireEvent.click(screen.getByRole('button', { name: 'Quitar diagnóstico 1' }));
    expect(lista()).toEqual([DOS[1]]);
  });

  it('en solo lectura no muestra botones y los campos están deshabilitados', () => {
    render(<Prueba inicial={DOS} disabled />);
    expect(screen.queryByRole('button')).toBeNull();
    expect(screen.getByLabelText('Diagnóstico 1')).toBeDisabled();
    expect(screen.getByLabelText('CIE-10 del diagnóstico 1')).toBeDisabled();
  });

  it('muestra los errores de cada fila y el error general', () => {
    const { rerender } = render(<Prueba inicial={DOS} error={[{}, { codigo_cie10: ['Código CIE-10 no válido.'] }]} />);
    expect(screen.getByText('Código CIE-10 no válido.')).toBeInTheDocument();
    rerender(<Prueba inicial={DOS} error="Un informe admite como máximo 20 diagnósticos." />);
    expect(screen.getByText('Un informe admite como máximo 20 diagnósticos.')).toBeInTheDocument();
  });
});

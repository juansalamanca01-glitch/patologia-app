import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import SeccionFirma from './SeccionFirma';

// Solo datos ficticios (docs/propuesta-informe-v2.md, sección 8).
const FIRMA = { nombre: 'Dra. Ficticia Firma', especialidad: 'Patología Quirúrgica', registro_medico: 'RM-PRUEBA-0001' };

describe('SeccionFirma (informe v2, etapa 6)', () => {
  it('en un informe finalizado muestra la firma y la fecha de informe', () => {
    render(<SeccionFirma firma={FIRMA} estado="finalizado" fechaInforme="2026-10-04T20:30:00Z" />);
    expect(screen.getByText('Dra. Ficticia Firma')).toBeInTheDocument();
    expect(screen.getByText('Patología Quirúrgica')).toBeInTheDocument();
    expect(screen.getByText(/Registro médico N\.º RM-PRUEBA-0001/)).toBeInTheDocument();
    // 20:30 UTC son las 15:30 en Bogotá.
    expect(screen.getByText(/04\/10\/2026.*3:30/)).toBeInTheDocument();
    expect(screen.queryByText(/Al finalizar/)).not.toBeInTheDocument();
  });

  it('en un borrador dice quién firmará al finalizar', () => {
    render(<SeccionFirma firma={FIRMA} estado="borrador" fechaInforme={null} />);
    expect(screen.getByText(/Al finalizar, el informe llevará la firma del patólogo autor/)).toBeInTheDocument();
    expect(screen.getByText('Dra. Ficticia Firma')).toBeInTheDocument();
    expect(screen.queryByText(/Fecha de informe/)).not.toBeInTheDocument();
  });

  it('avisa si el autor no tiene registro médico', () => {
    render(<SeccionFirma firma={{ ...FIRMA, registro_medico: '' }} estado="borrador" fechaInforme={null} />);
    expect(screen.getByText(/no tiene registro médico/)).toBeInTheDocument();
    expect(screen.queryByText(/Registro médico N\.º/)).not.toBeInTheDocument();
  });

  it('no muestra nada si no hay firma (informe sin guardar)', () => {
    const { container } = render(<SeccionFirma firma={null} estado="borrador" fechaInforme={null} />);
    expect(container).toBeEmptyDOMElement();
  });
});

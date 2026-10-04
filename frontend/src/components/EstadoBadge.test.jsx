import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import EstadoBadge from './EstadoBadge';

describe('EstadoBadge', () => {
  it('muestra "Borrador" en amarillo', () => {
    render(<EstadoBadge estado="borrador" />);
    expect(screen.getByText('Borrador')).toHaveClass('badge', 'badge-warning');
  });

  it('muestra "Finalizado" en verde', () => {
    render(<EstadoBadge estado="finalizado" />);
    expect(screen.getByText('Finalizado')).toHaveClass('badge', 'badge-success');
  });

  it('un estado desconocido se muestra tal cual, sin color', () => {
    // Antes, cualquier estado que no fuera "borrador" se mostraba como "Finalizado".
    render(<EstadoBadge estado="anulado" />);
    expect(screen.getByText('anulado')).toHaveClass('badge');
  });
});

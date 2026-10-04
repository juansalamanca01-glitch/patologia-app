// Configuración común de las pruebas del frontend (Vitest).
// Agrega comprobaciones como toBeInTheDocument() y limpia el DOM entre pruebas.
import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

afterEach(() => {
  cleanup();
});

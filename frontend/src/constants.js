// Valores compartidos por varias páginas (auditoría M-3: antes estaban copiados en cada una).

// Nombre visible de cada rol de usuario.
export const ROL_LABELS = {
  admin: 'Administrador',
  patologo: 'Patólogo',
  auditor: 'Auditor',
};

// Texto y clase CSS de cada estado de un informe.
export const ESTADOS_INFORME = {
  borrador: { texto: 'Borrador', clase: 'badge-warning' },
  finalizado: { texto: 'Finalizado', clase: 'badge-success' },
};

import { ESTADOS_INFORME } from '../constants';

// Etiqueta de color con el estado de un informe ("Borrador" o "Finalizado").
export default function EstadoBadge({ estado }) {
  const { texto, clase } = ESTADOS_INFORME[estado] || { texto: estado, clase: '' };
  return <span className={`badge ${clase}`}>{texto}</span>;
}

import { useEffect, useState } from 'react';
import client from '../api/client';

// Listas fijas del backend (sexos, tipos de documento, tipos de estudio), sacadas
// de GET /api/opciones/ (docs/propuesta-informe-v2.md, 3.3). No se copian en
// constants.js para no tener los mismos valores en dos sitios.
const SIN_OPCIONES = { sexos: [], tipos_documento: [], tipos_estudio: [] };

// Se piden una sola vez por sesión del navegador; si la petición falla, se vuelve
// a intentar la próxima vez que una pantalla las necesite.
let peticion = null;
// Las opciones ya recibidas: un componente que se monta después (p. ej. el
// formulario de paciente) las tiene desde el primer render, sin listas vacías.
let recibidas = null;

export function reiniciarOpciones() {
  peticion = null;
  recibidas = null;
}

export default function useOpciones() {
  const [opciones, setOpciones] = useState(() => ({ ...SIN_OPCIONES, ...recibidas }));
  const [error, setError] = useState('');

  useEffect(() => {
    let montado = true;
    if (!peticion) {
      peticion = client.get('/opciones/').then(({ data }) => { recibidas = data; return data; });
      peticion.catch(() => { peticion = null; });
    }
    peticion
      .then((data) => { if (montado) setOpciones({ ...SIN_OPCIONES, ...data }); })
      .catch(() => { if (montado) setError('No se pudieron cargar las listas de opciones.'); });
    return () => { montado = false; };
  }, []);

  return { opciones, error };
}

// Etiqueta de un valor de una lista de opciones, p. ej. 'femenino' → 'Femenino'.
export function etiquetaDe(lista, valor) {
  return lista.find((o) => o.valor === valor)?.etiqueta ?? valor;
}

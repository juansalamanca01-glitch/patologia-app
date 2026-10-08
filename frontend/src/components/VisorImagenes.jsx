import { useCallback, useEffect, useState } from 'react';

// Miniaturas de las imágenes de una publicación del foro y visor para verlas en grande.
// Cada miniatura es un botón; el visor se cierra con "Cerrar", con Escape o con un clic
// fuera de la imagen, y se recorre con "Imagen anterior" / "Imagen siguiente" o con las
// flechas del teclado. `imagenes` viene de la API: [{ id, imagen, descripcion }].
export default function VisorImagenes({ imagenes }) {
  const [abierta, setAbierta] = useState(null); // índice de la imagen ampliada
  const total = imagenes.length;

  const cerrar = useCallback(() => setAbierta(null), []);
  const mover = useCallback((paso) => setAbierta((i) => (i + paso + total) % total), [total]);

  useEffect(() => {
    if (abierta === null) return undefined;
    const alPresionar = (e) => {
      if (e.key === 'Escape') cerrar();
      if (total > 1 && e.key === 'ArrowRight') mover(1);
      if (total > 1 && e.key === 'ArrowLeft') mover(-1);
    };
    document.addEventListener('keydown', alPresionar);
    return () => document.removeEventListener('keydown', alPresionar);
  }, [abierta, total, cerrar, mover]);

  if (total === 0) return null;
  const actual = abierta === null ? null : imagenes[abierta];

  return (
    <>
      <div className="foro-imagenes-grid">
        {imagenes.map((img, i) => (
          <button
            key={img.id}
            type="button"
            className="foro-miniatura"
            onClick={() => setAbierta(i)}
            aria-label={`Ampliar imagen ${i + 1} de ${total}`}
          >
            <img src={img.imagen} alt={img.descripcion || ''} />
          </button>
        ))}
      </div>

      {actual && (
        // Un clic en el fondo (fuera de la imagen y de los botones) cierra el visor.
        <div
          className="visor-imagen"
          role="dialog"
          aria-modal="true"
          aria-label={`Imagen ampliada ${abierta + 1} de ${total}`}
          onClick={(e) => {
            if (e.target === e.currentTarget) cerrar();
          }}
        >
          <button type="button" className="visor-cerrar" onClick={cerrar}>
            Cerrar
          </button>
          {total > 1 && (
            <button
              type="button"
              className="visor-flecha visor-anterior"
              onClick={() => mover(-1)}
              aria-label="Imagen anterior"
            >
              ‹
            </button>
          )}
          <figure>
            <img src={actual.imagen} alt={actual.descripcion || `Imagen ${abierta + 1} de ${total}`} />
            <figcaption>
              {actual.descripcion && <span>{actual.descripcion}</span>}
              <span>
                {abierta + 1} de {total}
              </span>
            </figcaption>
          </figure>
          {total > 1 && (
            <button
              type="button"
              className="visor-flecha visor-siguiente"
              onClick={() => mover(1)}
              aria-label="Imagen siguiente"
            >
              ›
            </button>
          )}
        </div>
      )}
    </>
  );
}

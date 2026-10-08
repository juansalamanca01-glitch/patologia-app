// Tarjeta "Diagnósticos" del informe (informe v2, etapa 5). Cada fila tiene una
// descripción y un código CIE-10 opcional; el orden de la lista es el del informe.
// El backend valida y normaliza el código ("c443" → "C44.3") y admite hasta 20.

let siguienteClave = 1;

// Cada fila lleva una `clave` propia para que React no confunda las filas al
// reordenarlas. La clave no se envía a la API.
export const conClaves = (diagnosticos = []) =>
  diagnosticos.map(({ descripcion, codigo_cie10 }) => ({
    clave: siguienteClave++,
    descripcion,
    codigo_cie10: codigo_cie10 || '',
  }));

export const sinClaves = (diagnosticos) =>
  diagnosticos.map(({ descripcion, codigo_cie10 }) => ({
    descripcion,
    codigo_cie10,
  }));

// `error` es un texto (error de toda la lista) o un arreglo con los errores de
// cada fila, como los devuelve DRF: [{}, { codigo_cie10: ['...'] }].
export default function ListaDiagnosticos({ diagnosticos, onCambiar, disabled = false, error }) {
  const erroresFila = Array.isArray(error) ? error : [];
  const errorGeneral = typeof error === 'string' ? error : '';

  const cambiar = (indice, campo, valor) =>
    onCambiar(diagnosticos.map((d, i) => (i === indice ? { ...d, [campo]: valor } : d)));

  const mover = (indice, destino) => {
    const nueva = [...diagnosticos];
    [nueva[indice], nueva[destino]] = [nueva[destino], nueva[indice]];
    onCambiar(nueva);
  };

  const quitar = (indice) => onCambiar(diagnosticos.filter((_, i) => i !== indice));

  const agregar = () => onCambiar([...diagnosticos, ...conClaves([{ descripcion: '', codigo_cie10: '' }])]);

  const mensaje = (fila, campo) => {
    const valor = erroresFila[fila]?.[campo];
    return Array.isArray(valor) ? valor.join(' ') : valor;
  };

  return (
    <div className="card">
      <div className="card-header">
        <h2>Diagnósticos</h2>
      </div>
      <div className="card-body">
        {diagnosticos.length === 0 && (
          <p className="text-muted">Todavía no hay diagnósticos. Para finalizar el informe se necesita al menos uno.</p>
        )}

        <ol className="lista-diagnosticos">
          {diagnosticos.map((d, i) => {
            const numero = i + 1;
            const errorDescripcion = mensaje(i, 'descripcion');
            const errorCodigo = mensaje(i, 'codigo_cie10');
            return (
              <li key={d.clave} className="diagnostico-fila">
                <div className="form-row">
                  <div className={`form-group flex-2 ${errorDescripcion ? 'has-error' : ''}`}>
                    <label htmlFor={`diagnostico-${d.clave}-descripcion`}>Diagnóstico {numero}</label>
                    <textarea
                      id={`diagnostico-${d.clave}-descripcion`}
                      value={d.descripcion}
                      onChange={(e) => cambiar(i, 'descripcion', e.target.value)}
                      rows={2}
                      disabled={disabled}
                    />
                    {errorDescripcion && <span className="field-error">{errorDescripcion}</span>}
                  </div>
                  <div className={`form-group ${errorCodigo ? 'has-error' : ''}`}>
                    <label htmlFor={`diagnostico-${d.clave}-cie10`}>CIE-10 (opcional)</label>
                    <input
                      id={`diagnostico-${d.clave}-cie10`}
                      aria-label={`CIE-10 del diagnóstico ${numero}`}
                      type="text"
                      value={d.codigo_cie10}
                      onChange={(e) => cambiar(i, 'codigo_cie10', e.target.value)}
                      placeholder="Ej: C44.3"
                      maxLength={8}
                      disabled={disabled}
                    />
                    {errorCodigo && <span className="field-error">{errorCodigo}</span>}
                  </div>
                </div>
                {!disabled && (
                  <div className="diagnostico-acciones">
                    <button
                      type="button"
                      className="btn btn-outline btn-xs"
                      onClick={() => mover(i, i - 1)}
                      disabled={i === 0}
                      aria-label={`Subir diagnóstico ${numero}`}
                    >
                      ↑ Subir
                    </button>
                    <button
                      type="button"
                      className="btn btn-outline btn-xs"
                      onClick={() => mover(i, i + 1)}
                      disabled={i === diagnosticos.length - 1}
                      aria-label={`Bajar diagnóstico ${numero}`}
                    >
                      ↓ Bajar
                    </button>
                    <button
                      type="button"
                      className="btn btn-danger-outline btn-xs"
                      onClick={() => quitar(i)}
                      aria-label={`Quitar diagnóstico ${numero}`}
                    >
                      Quitar
                    </button>
                  </div>
                )}
              </li>
            );
          })}
        </ol>

        {errorGeneral && <span className="field-error">{errorGeneral}</span>}

        {!disabled && (
          <button type="button" className="btn btn-outline btn-sm" onClick={agregar}>
            + Agregar diagnóstico
          </button>
        )}
      </div>
    </div>
  );
}

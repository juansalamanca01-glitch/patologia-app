import { useState } from 'react';
import client, { resultados } from '../../api/client';
import useOpciones, { etiquetaDe } from '../../hooks/useOpciones';
import FormularioPaciente from '../FormularioPaciente';

// Convierte un paciente de /api/pacientes/ a la forma de `paciente_datos` del
// informe, que es la que muestra este selector. Conserva la EPS para que el
// informe la pueda precargar.
function datosDelPaciente(p) {
  return {
    id: p.id,
    nombre_completo: `${p.nombres} ${p.apellidos}`,
    tipo_documento: p.tipo_documento,
    numero_documento: p.numero_documento,
    fecha_nacimiento: p.fecha_nacimiento,
    sexo: p.sexo,
    edad: p.edad,
    eps: p.eps,
    eps_nombre: p.eps_nombre,
  };
}

// Tarjeta "Paciente" del informe (informe v2, etapa 4): busca por documento o
// nombre, o crea el paciente en el momento. `paciente` tiene la forma de
// `paciente_datos` (o null si el informe aún no tiene paciente).
export default function SelectorPaciente({ paciente, onSeleccionar, disabled = false, error }) {
  const { opciones } = useOpciones();
  const [cambiando, setCambiando] = useState(false);
  const [query, setQuery] = useState('');
  const [encontrados, setEncontrados] = useState(null); // null = todavía no se buscó
  const [buscando, setBuscando] = useState(false);
  const [errorBusqueda, setErrorBusqueda] = useState('');
  const [creando, setCreando] = useState(false);

  const buscar = async () => {
    const q = query.trim();
    if (!q) return;
    setBuscando(true);
    setErrorBusqueda('');
    try {
      const { data } = await client.get('/pacientes/', { params: { q } });
      setEncontrados(resultados(data));
    } catch {
      setErrorBusqueda('No se pudo buscar el paciente.');
    } finally {
      setBuscando(false);
    }
  };

  const seleccionar = (p) => {
    onSeleccionar(datosDelPaciente(p));
    setCambiando(false);
    setEncontrados(null);
    setQuery('');
  };

  const mostrarBusqueda = !disabled && (!paciente || cambiando);

  return (
    <div className="card">
      <div className="card-header"><h2>Paciente</h2></div>
      <div className="card-body">
        {paciente && !cambiando && (
          <div className="paciente-seleccionado">
            <div className="form-row">
              <div className="form-group">
                <span className="text-muted">Paciente</span>
                <strong>{paciente.nombre_completo}</strong>
              </div>
              <div className="form-group">
                <span className="text-muted">Identificación</span>
                <span>{paciente.tipo_documento} {paciente.numero_documento}</span>
              </div>
              <div className="form-group">
                <span className="text-muted">Edad</span>
                <span>{paciente.edad || '—'}</span>
              </div>
              <div className="form-group">
                <span className="text-muted">Sexo</span>
                <span>{paciente.sexo ? etiquetaDe(opciones.sexos, paciente.sexo) : '—'}</span>
              </div>
            </div>
            {!disabled && (
              <button type="button" className="btn btn-outline btn-sm" onClick={() => setCambiando(true)}>
                Cambiar
              </button>
            )}
          </div>
        )}

        {!paciente && disabled && <p className="text-muted">No registrado</p>}

        {mostrarBusqueda && (
          <>
            <div className="form-row">
              <div className={`form-group flex-2 ${error ? 'has-error' : ''}`}>
                <label htmlFor="buscar-paciente-informe">Buscar paciente</label>
                <input
                  id="buscar-paciente-informe"
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => {
                    // Enter busca el paciente; no debe enviar el formulario del informe.
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      buscar();
                    }
                  }}
                  placeholder="Número de documento, nombres o apellidos..."
                />
                {error && <span className="field-error">{error}</span>}
              </div>
            </div>
            <div className="header-actions">
              <button type="button" className="btn btn-primary btn-sm" onClick={buscar} disabled={buscando}>
                Buscar
              </button>
              <button type="button" className="btn btn-outline btn-sm" onClick={() => setCreando(true)}>
                Nuevo paciente
              </button>
              {paciente && (
                <button type="button" className="btn btn-outline btn-sm" onClick={() => setCambiando(false)}>
                  Cancelar
                </button>
              )}
            </div>

            {errorBusqueda && <div className="alert alert-error">{errorBusqueda}</div>}
            {encontrados && encontrados.length === 0 && (
              <p className="text-muted">No se encontraron pacientes. Puede crearlo con "Nuevo paciente".</p>
            )}
            {encontrados && encontrados.length > 0 && (
              <div className="table-responsive">
                <table>
                  <thead>
                    <tr><th>Documento</th><th>Paciente</th><th>Edad</th><th></th></tr>
                  </thead>
                  <tbody>
                    {encontrados.map((p) => (
                      <tr key={p.id}>
                        <td>{p.tipo_documento} {p.numero_documento}</td>
                        <td>{p.nombres} {p.apellidos}</td>
                        <td>{p.edad}</td>
                        <td>
                          <button type="button" className="btn btn-outline btn-xs" onClick={() => seleccionar(p)}>
                            Seleccionar
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}

        {creando && (
          <FormularioPaciente
            paciente={null}
            onGuardado={(nuevo) => { setCreando(false); seleccionar(nuevo); }}
            onCancelar={() => setCreando(false)}
          />
        )}
      </div>
    </div>
  );
}

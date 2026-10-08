import { hoyISO } from '../../utils/formularios';

// Tarjeta "Datos de la solicitud" del informe (informe v2, etapa 4): lo que pide
// el médico remitente. `valores` tiene los campos de la API; `onCambiar(campo, valor)`
// los actualiza. Las listas de EPS y servicios ya incluyen la actual si se desactivó.
export default function DatosSolicitud({ valores, onCambiar, epsOpciones, serviciosOpciones, disabled, errores }) {
  const cambiar = (campo) => (e) => onCambiar(campo, e.target.value);

  const grupo = (campo, etiqueta, control) => (
    <div className={`form-group ${errores[campo] ? 'has-error' : ''}`}>
      <label htmlFor={`solicitud-${campo}`}>{etiqueta}</label>
      {control}
      {errores[campo] && <span className="field-error">{errores[campo]}</span>}
    </div>
  );

  return (
    <div className="card">
      <div className="card-header">
        <h2>Datos de la solicitud</h2>
      </div>
      <div className="card-body">
        <div className="form-row">
          {grupo(
            'medico_tratante',
            'Médico tratante',
            <input
              id="solicitud-medico_tratante"
              type="text"
              value={valores.medico_tratante}
              onChange={cambiar('medico_tratante')}
              maxLength={200}
              disabled={disabled}
            />,
          )}
          {grupo(
            'fecha_ingreso',
            'Fecha de ingreso',
            <input
              id="solicitud-fecha_ingreso"
              type="date"
              value={valores.fecha_ingreso}
              onChange={cambiar('fecha_ingreso')}
              max={hoyISO()}
              disabled={disabled}
            />,
          )}
        </div>
        <div className="form-row">
          {grupo(
            'eps',
            'EPS',
            <select id="solicitud-eps" value={valores.eps} onChange={cambiar('eps')} disabled={disabled}>
              <option value="">Sin EPS</option>
              {epsOpciones.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.nombre}
                </option>
              ))}
            </select>,
          )}
          {grupo(
            'servicio',
            'Servicio',
            <select id="solicitud-servicio" value={valores.servicio} onChange={cambiar('servicio')} disabled={disabled}>
              <option value="">Sin servicio</option>
              {serviciosOpciones.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.nombre}
                </option>
              ))}
            </select>,
          )}
          {grupo(
            'numero_orden_externa',
            'N.º de orden externa (opcional)',
            <input
              id="solicitud-numero_orden_externa"
              type="text"
              value={valores.numero_orden_externa}
              onChange={cambiar('numero_orden_externa')}
              placeholder="Número de la institución remitente"
              maxLength={50}
              disabled={disabled}
            />,
          )}
        </div>
        {grupo(
          'estudios_solicitados',
          'Estudios solicitados',
          <textarea
            id="solicitud-estudios_solicitados"
            value={valores.estudios_solicitados}
            onChange={cambiar('estudios_solicitados')}
            rows={2}
            placeholder="Lo que pidió el médico remitente"
            disabled={disabled}
          />,
        )}
      </div>
    </div>
  );
}

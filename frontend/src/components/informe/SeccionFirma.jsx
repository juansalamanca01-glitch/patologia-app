// Tarjeta "Firma" del informe (informe v2, etapa 6). Es de solo lectura: la firma
// es siempre la del autor (decisión D-8) y el backend la congela al finalizar (D-10).
// `firma` viene de la API: { nombre, especialidad, registro_medico }.

const formatoFecha = new Intl.DateTimeFormat('es-CO', {
  day: '2-digit', month: '2-digit', year: 'numeric',
  hour: '2-digit', minute: '2-digit',
  timeZone: 'America/Bogota',
});

export default function SeccionFirma({ firma, estado, fechaInforme }) {
  if (!firma) return null;  // informe nuevo, todavía sin guardar
  const finalizado = estado === 'finalizado';

  return (
    <div className="card">
      <div className="card-header"><h2>Firma</h2></div>
      <div className="card-body">
        {!finalizado && (
          firma.registro_medico ? (
            <p className="text-muted">Al finalizar, el informe llevará la firma del patólogo autor:</p>
          ) : (
            <div className="alert alert-warning">
              El patólogo autor no tiene registro médico; un administrador debe registrarlo antes de finalizar el informe.
            </div>
          )
        )}
        <div className="firma-informe">
          <strong>{firma.nombre}</strong>
          {firma.especialidad && <span>{firma.especialidad}</span>}
          {firma.registro_medico && <span>Registro médico N.º {firma.registro_medico}</span>}
        </div>
        {finalizado && fechaInforme && (
          <p className="text-muted">Fecha de informe: {formatoFecha.format(new Date(fechaInforme))}</p>
        )}
      </div>
    </div>
  );
}

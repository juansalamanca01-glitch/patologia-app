// Celda "Paciente" de los listados de informes (informe v2, etapa 4): nombre y
// documento, o "No registrado" en los informes de antes de la etapa 4.
export default function CeldaPaciente({ informe }) {
  if (!informe.paciente_nombre) return <span className="text-muted">No registrado</span>;
  return (
    <>
      {informe.paciente_nombre}
      <br />
      <small className="text-muted">{informe.paciente_documento}</small>
    </>
  );
}

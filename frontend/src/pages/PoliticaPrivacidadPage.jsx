export default function PoliticaPrivacidadPage() {
  return (
    <div className="legal-page">
      <div className="card">
        <div className="card-body">
          <h1>Política de Privacidad</h1>
          <p className="text-muted">Última actualización: {new Date().toLocaleDateString('es-CO')}</p>

          <div className="alert alert-info">
            Este texto es una plantilla de referencia. Antes de usarlo en producción con
            datos clínicos reales, debe ser revisado y ajustado por un abogado, conforme a la
            Ley 1581 de 2012 y el Decreto 1377 de 2013 (protección de datos personales en Colombia),
            y a la normativa de historia clínica aplicable (Resolución 1995 de 1999 y demás vigentes).
          </div>

          <h2>1. Responsable del tratamiento</h2>
          <p>
            PathoLab actúa como responsable del tratamiento de los datos personales y clínicos
            registrados por los usuarios (patólogos, auditores y administradores) de la institución
            que opera esta plataforma.
          </p>

          <h2>2. Datos que se recopilan</h2>
          <ul>
            <li>Datos de cuenta: nombre, usuario, correo electrónico, teléfono, especialidad y rol.</li>
            <li>Datos clínicos de los informes de patología: número de petición, número de orden de la
              institución remitente, tipo de muestra, datos
              del formulario dinámico y observaciones asociadas.</li>
            <li>Contenido compartido voluntariamente en el foro (publicaciones, comentarios e imágenes).</li>
            <li>Metadatos técnicos: fecha y hora de creación/edición de registros, para trazabilidad.</li>
          </ul>

          <h2>3. Finalidad del tratamiento</h2>
          <p>
            Los datos se usan exclusivamente para: (a) generar, almacenar y auditar informes de
            patología clínica; (b) gestionar el acceso y los roles de los usuarios del sistema;
            (c) permitir el intercambio profesional de conocimiento en el foro interno; y
            (d) cumplir obligaciones legales de conservación de historia clínica.
          </p>

          <h2>4. Confidencialidad de la información clínica</h2>
          <p>
            La información clínica contenida en los informes tiene carácter confidencial y solo es
            accesible para el personal autorizado según su rol (patólogo, auditor o administrador).
            No se comparte con terceros sin el debido soporte legal o consentimiento del paciente,
            salvo requerimiento de autoridad competente.
          </p>

          <h2>5. Derechos de los titulares (Habeas Data)</h2>
          <p>
            Todo titular de datos personales puede solicitar conocer, actualizar, rectificar o
            solicitar la supresión de su información, así como revocar la autorización otorgada
            para su tratamiento, salvo que exista un deber legal de conservación (como ocurre con
            la historia clínica).
          </p>

          <h2>6. Seguridad de la información</h2>
          <p>
            Se aplican controles técnicos como autenticación mediante tokens (JWT), cifrado de
            contraseñas, control de acceso basado en roles, límites de solicitudes (rate limiting)
            para prevenir abuso, y restricciones de origen (CORS) para proteger la API contra accesos
            no autorizados.
          </p>

          <h2>7. Conservación de los datos</h2>
          <p>
            Los informes y registros asociados se conservan durante el tiempo exigido por la
            normativa de historia clínica vigente y las políticas internas de la institución.
          </p>

          <h2>8. Contacto</h2>
          <p>
            Para ejercer sus derechos o resolver dudas sobre el tratamiento de datos, comuníquese
            con el administrador del sistema en su institución.
          </p>
        </div>
      </div>
    </div>
  );
}

export default function TerminosCondicionesPage() {
  return (
    <div className="legal-page">
      <div className="card">
        <div className="card-body">
          <h1>Términos y Condiciones de Uso</h1>
          <p className="text-muted">Última actualización: {new Date().toLocaleDateString('es-CO')}</p>

          <div className="alert alert-info">
            Este texto es una plantilla de referencia y debe ser revisado por asesoría legal antes
            de su uso en un entorno de producción con pacientes reales.
          </div>

          <h2>1. Aceptación de los términos</h2>
          <p>
            El acceso y uso de PathoLab implica la aceptación plena de estos términos y de la
            Política de Privacidad. El acceso está restringido a personal autorizado por la
            institución (patólogos, auditores y administradores).
          </p>

          <h2>2. Cuentas y credenciales</h2>
          <p>
            Cada usuario es responsable de mantener la confidencialidad de su contraseña y de toda
            actividad realizada desde su cuenta. Las cuentas son creadas únicamente por un
            administrador; no se permite el autoregistro público, precisamente para evitar accesos
            no autorizados al sistema.
          </p>

          <h2>3. Uso adecuado del sistema</h2>
          <ul>
            <li>Los informes de patología deben registrarse con información veraz y completa.</li>
            <li>El foro es un espacio profesional para compartir investigaciones y observaciones
              clínicas entre patólogos; no debe usarse para publicar contenido ajeno a este fin,
              spam, ni información de pacientes que permita identificarlos indebidamente.</li>
            <li>Está prohibido intentar vulnerar los mecanismos de seguridad del sistema (autenticación,
              límites de solicitudes, permisos por rol, etc.).</li>
          </ul>

          <h2>4. Roles y permisos</h2>
          <p>
            El sistema define roles (administrador, patólogo, auditor) con distintos niveles de
            acceso. Los patólogos pueden crear y gestionar patologías, categorías e informes; los
            auditores tienen acceso de solo lectura; los administradores gestionan usuarios y
            moderan el contenido del foro.
          </p>

          <h2>5. Contenido publicado por los usuarios</h2>
          <p>
            Al publicar en el foro (texto e imágenes), el usuario declara que tiene derecho a
            compartir ese contenido y autoriza su visualización por otros usuarios autorizados
            de la plataforma. El administrador puede eliminar o fijar publicaciones con fines de
            moderación.
          </p>

          <h2>6. Disponibilidad del servicio</h2>
          <p>
            Se procura la disponibilidad continua del sistema, sin perjuicio de labores de
            mantenimiento programado o eventos de fuerza mayor.
          </p>

          <h2>7. Limitación de responsabilidad</h2>
          <p>
            PathoLab es una herramienta de apoyo para la generación y gestión de informes; la
            responsabilidad clínica y diagnóstica final corresponde al profesional de la salud
            que firma y finaliza cada informe.
          </p>

          <h2>8. Modificaciones</h2>
          <p>
            Estos términos pueden actualizarse periódicamente. El uso continuado del sistema tras
            una actualización implica la aceptación de los nuevos términos.
          </p>
        </div>
      </div>
    </div>
  );
}

// Fecha fija: cambia solo cuando cambia el texto (antes mostraba la fecha del día en que se abría).
const ULTIMA_ACTUALIZACION = '5 de octubre de 2026';

export default function PoliticaPrivacidadPage() {
  return (
    <div className="legal-page">
      <div className="card">
        <div className="card-body">
          <h1>Política de Privacidad</h1>
          <p className="text-muted">Última actualización: {ULTIMA_ACTUALIZACION}</p>

          <div className="alert alert-info">
            Este texto es una plantilla de referencia. Antes de usarlo en producción con datos clínicos reales, debe ser
            revisado y ajustado por un abogado, conforme a la Ley 1581 de 2012 y el Decreto 1377 de 2013 (protección de
            datos personales en Colombia), y a la normativa de historia clínica aplicable (Resolución 1995 de 1999 y
            demás vigentes).
          </div>

          <h2>1. Responsable del tratamiento</h2>
          <p>
            La institución que opera esta plataforma actúa como responsable del tratamiento de los datos personales y
            clínicos que registran sus usuarios (patólogos, auditores y administradores) en PathoLab.
          </p>

          <h2>2. Datos que se recopilan</h2>
          <ul>
            <li>
              <strong>Datos de los pacientes:</strong> tipo y número de documento, nombres, apellidos, fecha de
              nacimiento, sexo y EPS. La edad no se guarda: se calcula a partir de la fecha de nacimiento. No se piden
              dirección, teléfono ni correo del paciente, porque no aparecen en el informe.
            </li>
            <li>
              <strong>Contenido de los informes de anatomía patológica:</strong> número de petición, número de orden de
              la institución remitente, médico tratante, fecha de ingreso, servicio, estudios solicitados, tipo de
              estudio y de muestra, datos del formulario de la patología, descripciones macroscópica y microscópica,
              diagnósticos con su código CIE-10, comentarios y adendas.
            </li>
            <li>
              <strong>Datos de los usuarios:</strong> nombre, usuario, correo electrónico, teléfono, especialidad, rol y
              registro médico. El nombre, la especialidad y el registro médico aparecen en la firma de los informes y de
              las adendas.
            </li>
            <li>Contenido compartido voluntariamente en el foro (publicaciones, comentarios e imágenes).</li>
            <li>Metadatos técnicos: fecha y hora de creación y de modificación de los registros, para trazabilidad.</li>
          </ul>

          <h2>3. Datos sensibles</h2>
          <p>
            Los datos de salud de los pacientes son datos sensibles según el artículo 5 de la Ley 1581 de 2012, y los
            informes forman parte de la historia clínica (Resolución 1995 de 1999). Por eso se guardan solo los datos
            que aparecen en el informe, y solo los consultan usuarios con sesión iniciada y según su rol.
          </p>

          <h2>4. Finalidad del tratamiento</h2>
          <p>
            Los datos se usan exclusivamente para: (a) generar, almacenar y auditar informes de anatomía patológica; (b)
            identificar al paciente en sus informes y consultar su historial; (c) gestionar el acceso y los roles de los
            usuarios del sistema; (d) permitir el intercambio profesional de conocimiento en el foro interno; y (e)
            cumplir obligaciones legales de conservación de la historia clínica.
          </p>

          <h2>5. Confidencialidad de la información clínica</h2>
          <p>
            La información clínica tiene carácter confidencial y solo es accesible para el personal autorizado según su
            rol (patólogo, auditor o administrador). No se comparte con terceros sin el debido soporte legal o el
            consentimiento del paciente, salvo requerimiento de autoridad competente. En el foro no se deben publicar
            datos que permitan identificar a un paciente.
          </p>

          <h2>6. Integridad de los informes</h2>
          <p>
            Un informe finalizado no se modifica: si hay que corregirlo, se agrega una adenda con su motivo, fecha y
            firma, y el contenido original se conserva. Al finalizar, los datos del paciente, la EPS, el servicio y la
            firma que imprime el informe quedan guardados tal como estaban, de modo que una corrección posterior de esos
            datos no altera un informe ya entregado. El PDF de un borrador es solo una vista previa para su autor,
            marcada como &quot;BORRADOR&quot;, y no tiene validez.
          </p>

          <h2>7. Derechos de los titulares (Habeas Data)</h2>
          <p>
            Todo titular de datos personales puede solicitar conocer, actualizar, rectificar o solicitar la supresión de
            su información, así como revocar la autorización otorgada para su tratamiento, salvo que exista un deber
            legal de conservación (como ocurre con la historia clínica).
          </p>

          <h2>8. Seguridad de la información</h2>
          <p>
            Se aplican controles técnicos como autenticación mediante tokens (JWT) enviados en la cabecera de cada
            petición, contraseñas almacenadas con hash, control de acceso basado en roles, límites de solicitudes (rate
            limiting) para prevenir abusos y restricciones de origen (CORS). Los nombres de los archivos PDF solo llevan
            el número de petición, nunca datos del paciente.
          </p>

          <h2>9. Conservación de los datos</h2>
          <p>
            Los informes y registros asociados se conservan durante el tiempo exigido por la normativa de historia
            clínica vigente y las políticas internas de la institución. Un paciente con informes no se puede borrar de
            la plataforma.
          </p>

          <h2>10. Contacto</h2>
          <p>
            Para ejercer sus derechos o resolver dudas sobre el tratamiento de datos, comuníquese con el administrador
            del sistema en su institución.
          </p>
        </div>
      </div>
    </div>
  );
}

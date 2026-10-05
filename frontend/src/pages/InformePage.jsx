import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import client, { LISTA_COMPLETA, resultados } from '../api/client';
import EstadoBadge from '../components/EstadoBadge';
import SelectorPaciente from '../components/informe/SelectorPaciente';
import DatosSolicitud from '../components/informe/DatosSolicitud';
import ListaDiagnosticos, { conClaves, sinClaves } from '../components/informe/ListaDiagnosticos';
import useOpciones from '../hooks/useOpciones';
import { conOpcionActual, hoyISO } from '../utils/formularios';

// Datos de la solicitud (informe v2, etapa 4) con los nombres de campo de la API.
const solicitudVacia = () => ({
  medico_tratante: '',
  fecha_ingreso: hoyISO(),
  eps: '',
  servicio: '',
  numero_orden_externa: '',
  estudios_solicitados: '',
});

export default function InformePage() {
  const { id } = useParams();
  const isEditing = Boolean(id);
  const navigate = useNavigate();
  const { user, canWrite, isAdmin } = useAuth();
  const { opciones } = useOpciones();

  const [patologias, setPatologias] = useState([]);
  const [selectedPatologia, setSelectedPatologia] = useState(null);
  const [plantillas, setPlantillas] = useState([]);
  const [formData, setFormData] = useState({});
  const [paciente, setPaciente] = useState(null); // con la forma de paciente_datos
  const [solicitud, setSolicitud] = useState(solicitudVacia);
  const [tipoEstudio, setTipoEstudio] = useState('histologia');
  const [epsActivas, setEpsActivas] = useState([]);
  const [serviciosActivos, setServiciosActivos] = useState([]);
  const [tipoMuestra, setTipoMuestra] = useState('');
  // Contenido del informe (informe v2, etapa 5). `comentarios` era `notas` (P-5).
  const [microscopica, setMicroscopica] = useState('');
  const [diagnosticos, setDiagnosticos] = useState([]);
  const [comentarios, setComentarios] = useState('');
  const [informe, setInforme] = useState(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState({});
  const [successMsg, setSuccessMsg] = useState('');
  const [confirmFinalizar, setConfirmFinalizar] = useState(false);

  // Un informe nuevo lo puede crear cualquier patólogo o admin; uno existente solo
  // lo puede editar o finalizar su autor o un admin (decisión D-2).
  const puedeEditar = isEditing
    ? canWrite && Boolean(informe) && (isAdmin || informe.autor === user?.id)
    : canWrite;
  const soloLectura = informe?.estado === 'finalizado' || !puedeEditar;

  // Carga la lista de patologías
  useEffect(() => {
    // Al crear un informe solo se ofrecen las patologías activas (decisión D-4). Al editar se
    // piden todas, para que se vea la patología de un informe viejo aunque esté desactivada.
    const params = isEditing ? LISTA_COMPLETA : { ...LISTA_COMPLETA, activa: 'true' };
    client.get('/patologias/', { params })
      .then(({ data }) => setPatologias(resultados(data)))
      .catch(() => setErrors((prev) => ({ ...prev, general: 'No se pudieron cargar las patologías. Recarga la página.' })));
  }, []);

  // EPS y servicios activos (D-4). La EPS o el servicio de un informe guardado se
  // agregan aparte si ya se desactivaron (conOpcionActual).
  useEffect(() => {
    Promise.all([
      client.get('/pacientes/eps/', { params: { ...LISTA_COMPLETA, activa: 'true' } }),
      client.get('/servicios/', { params: { ...LISTA_COMPLETA, activo: 'true' } }),
    ]).then(([eps, servicios]) => {
      setEpsActivas(resultados(eps.data));
      setServiciosActivos(resultados(servicios.data));
    }).catch(() => setErrors((prev) => ({ ...prev, general: 'No se pudieron cargar las EPS y los servicios. Recarga la página.' })));
  }, []);

  // Carga el informe si se está editando uno existente
  useEffect(() => {
    if (isEditing) {
      setLoading(true);
      client.get(`/informes/${id}/`).then(({ data }) => {
        setInforme(data);
        setPaciente(data.paciente_datos);
        setSolicitud({
          medico_tratante: data.medico_tratante || '',
          fecha_ingreso: data.fecha_ingreso || '',
          eps: data.eps ?? '',
          servicio: data.servicio ?? '',
          numero_orden_externa: data.numero_orden_externa || '',
          estudios_solicitados: data.estudios_solicitados || '',
        });
        setTipoEstudio(data.tipo_estudio || 'histologia');
        setTipoMuestra(data.tipo_muestra || '');
        setMicroscopica(data.descripcion_microscopica || '');
        setDiagnosticos(conClaves(data.diagnosticos));
        setComentarios(data.comentarios || '');
        setFormData(data.datos_ingresados || {});
        setSelectedPatologia(data.patologia);
      }).catch(() => navigate('/')).finally(() => setLoading(false));
    }
  }, [id]);

  // Carga los campos de la plantilla al cambiar de patología
  useEffect(() => {
    if (selectedPatologia) {
      client.get(`/patologias/${selectedPatologia}/`).then(({ data }) => {
        setPlantillas(data.plantillas || []);
        // Valores por defecto de los campos
        if (!isEditing) {
          const defaults = {};
          (data.plantillas || []).forEach((p) => {
            if (p.valor_defecto) defaults[p.campo_nombre] = p.valor_defecto;
          });
          setFormData((prev) => ({ ...defaults, ...prev }));
        }
      }).catch(() => {
        setErrors((prev) => ({ ...prev, general: 'No se pudieron cargar los campos de la patología. Recarga la página.' }));
      });
    } else {
      setPlantillas([]);
    }
  }, [selectedPatologia]);

  const handleFieldChange = (fieldName, value) => {
    setFormData((prev) => ({ ...prev, [fieldName]: value }));
    setErrors((prev) => ({ ...prev, [fieldName]: null }));
  };

  const cambiarSolicitud = (campo, valor) => {
    setSolicitud((prev) => ({ ...prev, [campo]: valor }));
    setErrors((prev) => ({ ...prev, [campo]: null }));
  };

  // Al elegir el paciente se precarga su EPS actual, si sigue activa. La del
  // informe se puede cambiar: es la del momento del estudio.
  const seleccionarPaciente = (nuevo) => {
    setPaciente(nuevo);
    setSolicitud((prev) => ({
      ...prev,
      eps: epsActivas.some((e) => e.id === nuevo.eps) ? nuevo.eps : '',
    }));
    setErrors((prev) => ({ ...prev, paciente: null, eps: null }));
  };

  const validate = () => {
    const newErrors = {};
    if (!paciente) newErrors.paciente = 'Seleccione un paciente.';
    if (!selectedPatologia) newErrors.patologia = 'Seleccione una patología.';

    plantillas.filter(p => p.obligatorio).forEach((p) => {
      const val = formData[p.campo_nombre];
      if (!val || (typeof val === 'string' && !val.trim())) {
        newErrors[p.campo_nombre] = `${p.campo_label || p.campo_nombre} es obligatorio.`;
      }
    });

    // Errores por fila, con la misma forma que los del backend.
    const erroresDiagnosticos = diagnosticos.map((d) => (
      d.descripcion.trim() ? {} : { descripcion: 'Escriba la descripción del diagnóstico.' }
    ));
    if (erroresDiagnosticos.some((e) => e.descripcion)) newErrors.diagnosticos = erroresDiagnosticos;

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setSaving(true);
    setSuccessMsg('');

    // El número de petición no se envía: lo asigna el backend al crear el informe (decisión D-7).
    const payload = {
      paciente: paciente.id,
      ...solicitud,
      eps: solicitud.eps ? Number(solicitud.eps) : null,
      servicio: solicitud.servicio ? Number(solicitud.servicio) : null,
      tipo_estudio: tipoEstudio,
      patologia: selectedPatologia,
      tipo_muestra: tipoMuestra,
      datos_ingresados: formData,
      descripcion_microscopica: microscopica,
      diagnosticos: sinClaves(diagnosticos),
      comentarios,
    };

    try {
      if (isEditing) {
        const { data } = await client.put(`/informes/${id}/`, payload);
        setInforme(data);
        // El backend normaliza los códigos CIE-10 ("c443" → "C44.3").
        setDiagnosticos(conClaves(data.diagnosticos));
        setSuccessMsg('Informe actualizado correctamente.');
      } else {
        const { data } = await client.post('/informes/', payload);
        setSuccessMsg('Informe creado correctamente.');
        navigate(`/informes/${data.id}`);
      }
    } catch (err) {
      const detail = err.response?.data;
      if (typeof detail === 'object') {
        const flatErrors = {};
        Object.entries(detail).forEach(([key, val]) => {
          // Los errores de los diagnósticos vienen por fila ([{}, {codigo_cie10: [...]}]):
          // se conservan así para mostrarlos junto a cada fila.
          const porFila = Array.isArray(val) && val.some((v) => typeof v === 'object');
          flatErrors[key] = Array.isArray(val) && !porFila ? val.join(' ') : val;
        });
        setErrors(flatErrors);
      } else {
        setErrors({ general: 'Ocurrió un error al guardar el informe.' });
      }
    } finally {
      setSaving(false);
    }
  };

  const handleFinalizar = async () => {
    if (!confirmFinalizar) {
      setConfirmFinalizar(true);
      return;
    }
    setConfirmFinalizar(false);
    setSuccessMsg('');
    setErrors({});
    try {
      const { data } = await client.post(`/informes/${id}/finalizar/`);
      setInforme(data);
      setSuccessMsg('Informe finalizado correctamente.');
    } catch (err) {
      setErrors({ general: err.response?.data?.detail || 'Error al finalizar el informe.' });
    }
  };

  // Descarga el PDF con Axios, que envía el token en la cabecera Authorization.
  // Antes el token iba en la URL (?token=...) y quedaba en el historial (auditoría I-5).
  const downloadPDF = async () => {
    const safeName = (informe?.numero_peticion || id).toString().replace(/[^a-zA-Z0-9\-]/g, '_');
    try {
      const { data } = await client.get(`/informes/${id}/pdf/`, { responseType: 'blob' });
      // Enlace temporal "blob:" para que el navegador guarde el archivo con su nombre.
      const url = URL.createObjectURL(data);
      const enlace = document.createElement('a');
      enlace.href = url;
      enlace.download = `informe_${safeName}.pdf`;
      document.body.appendChild(enlace);
      enlace.click();
      enlace.remove();
      URL.revokeObjectURL(url);
    } catch {
      setErrors({ general: 'No se pudo descargar el PDF.' });
    }
  };

  const renderField = (plantilla) => {
    const { campo_nombre, campo_label, tipo_campo, opciones, obligatorio } = plantilla;
    const value = formData[campo_nombre] || '';
    const error = errors[campo_nombre];
    const disabled = informe?.estado === 'finalizado' || !puedeEditar;

    return (
      <div className={`form-group ${error ? 'has-error' : ''}`} key={campo_nombre}>
        <label htmlFor={campo_nombre}>
          {campo_label || campo_nombre}
          {obligatorio && <span className="required">*</span>}
        </label>

        {tipo_campo === 'texto' && (
          <input
            id={campo_nombre}
            type="text"
            value={value}
            onChange={(e) => handleFieldChange(campo_nombre, e.target.value)}
            disabled={disabled}
          />
        )}

        {tipo_campo === 'numero' && (
          <input
            id={campo_nombre}
            type="number"
            step="any"
            value={value}
            onChange={(e) => handleFieldChange(campo_nombre, e.target.value)}
            disabled={disabled}
          />
        )}

        {tipo_campo === 'lista' && (
          <select
            id={campo_nombre}
            value={value}
            onChange={(e) => handleFieldChange(campo_nombre, e.target.value)}
            disabled={disabled}
          >
            <option value="">— Seleccione —</option>
            {(opciones || []).map((opt) => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </select>
        )}

        {tipo_campo === 'textarea' && (
          <textarea
            id={campo_nombre}
            value={value}
            onChange={(e) => handleFieldChange(campo_nombre, e.target.value)}
            rows={3}
            disabled={disabled}
          />
        )}

        {tipo_campo === 'boolean' && (
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={value === true || value === 'true'}
              onChange={(e) => handleFieldChange(campo_nombre, e.target.checked)}
              disabled={disabled}
            />
            <span>{campo_label || campo_nombre}</span>
          </label>
        )}

        {error && <span className="field-error">{error}</span>}
      </div>
    );
  };

  if (loading) return <div className="loading-center"><span className="spinner"></span></div>;

  return (
    <div className="informe-page">
      <div className="page-header">
        <div>
          <h1>{isEditing ? `Informe ${informe?.numero_peticion || ''}` : 'Nuevo Informe'}</h1>
          {informe && (
            <EstadoBadge estado={informe.estado} />
          )}
        </div>
        <div className="header-actions">
          {isEditing && (
            <>
              <button className="btn btn-outline" onClick={downloadPDF}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
                  <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                  <polyline points="7,10 12,15 17,10"/>
                  <line x1="12" y1="15" x2="12" y2="3"/>
                </svg>
                Exportar PDF
              </button>
              {puedeEditar && informe?.estado === 'borrador' && (
                confirmFinalizar ? (
                  <>
                    <button className="btn btn-success" onClick={handleFinalizar}>
                      Si, Confirmar
                    </button>
                    <button className="btn btn-outline btn-sm" onClick={() => setConfirmFinalizar(false)}>
                      Cancelar
                    </button>
                  </>
                ) : (
                  <button className="btn btn-success" onClick={handleFinalizar}>
                    Finalizar Informe
                  </button>
                )
              )}
            </>
          )}
        </div>
      </div>

      {successMsg && <div className="alert alert-success">{successMsg}</div>}
      {(errors.general || errors.detail) && <div className="alert alert-error">{errors.general || errors.detail}</div>}

      <form onSubmit={handleSubmit}>
        {/* Orden del informe real (informe v2, etapa 4): Paciente, Datos de la solicitud y Estudio */}
        <SelectorPaciente
          paciente={paciente}
          onSeleccionar={seleccionarPaciente}
          disabled={soloLectura}
          error={errors.paciente}
        />

        <DatosSolicitud
          valores={solicitud}
          onCambiar={cambiarSolicitud}
          epsOpciones={conOpcionActual(epsActivas, solicitud.eps, informe?.eps_nombre)}
          serviciosOpciones={conOpcionActual(serviciosActivos, solicitud.servicio, informe?.servicio_nombre, 'desactivado')}
          disabled={soloLectura}
          errores={errors}
        />

        <div className="card">
          <div className="card-header"><h2>Estudio</h2></div>
          <div className="card-body">
            <div className="form-row">
              <div className={`form-group ${errors.tipo_estudio ? 'has-error' : ''}`}>
                <label htmlFor="tipoEstudio">Tipo de estudio</label>
                <select
                  id="tipoEstudio"
                  value={tipoEstudio}
                  onChange={(e) => setTipoEstudio(e.target.value)}
                  disabled={soloLectura}
                >
                  {opciones.tipos_estudio.map((o) => (
                    <option key={o.valor} value={o.valor}>{o.etiqueta}</option>
                  ))}
                </select>
                {errors.tipo_estudio && <span className="field-error">{errors.tipo_estudio}</span>}
              </div>

              <div className={`form-group ${errors.patologia ? 'has-error' : ''}`}>
                <label htmlFor="patologia">Tipo de Patología <span className="required">*</span></label>
                <select
                  id="patologia"
                  value={selectedPatologia || ''}
                  onChange={(e) => {
                    const val = e.target.value ? parseInt(e.target.value) : null;
                    setSelectedPatologia(val);
                    if (!isEditing) setFormData({});
                    setErrors(p => ({...p, patologia: null}));
                  }}
                  disabled={isEditing || !puedeEditar}
                >
                  <option value="">— Seleccione patología —</option>
                  {patologias.map((p) => (
                    <option key={p.id} value={p.id}>{p.nombre}</option>
                  ))}
                </select>
                {errors.patologia && <span className="field-error">{errors.patologia}</span>}
              </div>

              <div className="form-group">
                <label htmlFor="tipoMuestra">Tipo de Muestra</label>
                <input
                  id="tipoMuestra"
                  type="text"
                  value={tipoMuestra}
                  onChange={(e) => setTipoMuestra(e.target.value)}
                  placeholder="Ej: Biopsia escisional"
                  disabled={soloLectura}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Contenido en el orden del informe real (informe v2, etapa 5): macroscópica
            (campos dinámicos y texto generado), microscópica, diagnósticos y comentarios */}
        {(plantillas.length > 0 || informe?.texto_generado) && (
          <div className="card">
            <div className="card-header"><h2>Descripción macroscópica</h2></div>
            <div className="card-body">
              {plantillas.length > 0 && (
                <div className="dynamic-fields">
                  {plantillas.map(renderField)}
                </div>
              )}
              {informe?.texto_generado && (
                <>
                  <h3 className="texto-generado-titulo">Texto generado</h3>
                  <div className="generated-text">
                    {informe.texto_generado}
                  </div>
                </>
              )}
            </div>
          </div>
        )}

        <div className="card">
          <div className="card-header"><h2>Descripción microscópica</h2></div>
          <div className="card-body">
            <div className={`form-group ${errors.descripcion_microscopica ? 'has-error' : ''}`}>
              <textarea
                id="descripcionMicroscopica"
                aria-label="Descripción microscópica"
                value={microscopica}
                onChange={(e) => setMicroscopica(e.target.value)}
                rows={5}
                placeholder="Hallazgos al microscopio..."
                disabled={soloLectura}
              />
              {errors.descripcion_microscopica && <span className="field-error">{errors.descripcion_microscopica}</span>}
            </div>
          </div>
        </div>

        <ListaDiagnosticos
          diagnosticos={diagnosticos}
          onCambiar={(lista) => {
            setDiagnosticos(lista);
            setErrors((prev) => ({ ...prev, diagnosticos: null }));
          }}
          disabled={soloLectura}
          error={errors.diagnosticos}
        />

        <div className="card">
          <div className="card-header"><h2>Comentarios</h2></div>
          <div className="card-body">
            <div className={`form-group ${errors.comentarios ? 'has-error' : ''}`}>
              <textarea
                id="comentarios"
                aria-label="Comentarios"
                value={comentarios}
                onChange={(e) => setComentarios(e.target.value)}
                rows={3}
                placeholder="Comentarios para el médico tratante..."
                disabled={soloLectura}
              />
              {errors.comentarios && <span className="field-error">{errors.comentarios}</span>}
            </div>
          </div>
        </div>

        {puedeEditar && informe?.estado !== 'finalizado' && (
          <div className="form-actions">
            <button type="button" className="btn btn-outline" onClick={() => navigate('/')}>
              Cancelar
            </button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? <span className="spinner"></span> : isEditing ? 'Actualizar Informe' : 'Guardar Informe'}
            </button>
          </div>
        )}
      </form>
    </div>
  );
}

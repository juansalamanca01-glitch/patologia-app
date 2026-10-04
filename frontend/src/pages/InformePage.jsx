import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import client, { LISTA_COMPLETA, resultados } from '../api/client';
import EstadoBadge from '../components/EstadoBadge';

export default function InformePage() {
  const { id } = useParams();
  const isEditing = Boolean(id);
  const navigate = useNavigate();
  const { user, canWrite, isAdmin } = useAuth();

  const [patologias, setPatologias] = useState([]);
  const [selectedPatologia, setSelectedPatologia] = useState(null);
  const [plantillas, setPlantillas] = useState([]);
  const [formData, setFormData] = useState({});
  const [numeroCaso, setNumeroCaso] = useState('');
  const [tipoMuestra, setTipoMuestra] = useState('');
  const [notas, setNotas] = useState('');
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

  // Carga la lista de patologías
  useEffect(() => {
    // Al crear un informe solo se ofrecen las patologías activas (decisión D-4). Al editar se
    // piden todas, para que se vea la patología de un informe viejo aunque esté desactivada.
    const params = isEditing ? LISTA_COMPLETA : { ...LISTA_COMPLETA, activa: 'true' };
    client.get('/patologias/', { params }).then(({ data }) => {
      setPatologias(resultados(data));
    });
  }, []);

  // Carga el informe si se está editando uno existente
  useEffect(() => {
    if (isEditing) {
      setLoading(true);
      client.get(`/informes/${id}/`).then(({ data }) => {
        setInforme(data);
        setNumeroCaso(data.numero_caso);
        setTipoMuestra(data.tipo_muestra || '');
        setNotas(data.notas || '');
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
      });
    } else {
      setPlantillas([]);
    }
  }, [selectedPatologia]);

  const handleFieldChange = (fieldName, value) => {
    setFormData((prev) => ({ ...prev, [fieldName]: value }));
    setErrors((prev) => ({ ...prev, [fieldName]: null }));
  };

  const validate = () => {
    const newErrors = {};
    if (!numeroCaso.trim()) newErrors.numeroCaso = 'El número de caso es obligatorio.';
    if (!selectedPatologia) newErrors.patologia = 'Seleccione una patología.';

    plantillas.filter(p => p.obligatorio).forEach((p) => {
      const val = formData[p.campo_nombre];
      if (!val || (typeof val === 'string' && !val.trim())) {
        newErrors[p.campo_nombre] = `${p.campo_label || p.campo_nombre} es obligatorio.`;
      }
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setSaving(true);
    setSuccessMsg('');

    const payload = {
      numero_caso: numeroCaso,
      patologia: selectedPatologia,
      tipo_muestra: tipoMuestra,
      datos_ingresados: formData,
      notas,
    };

    try {
      if (isEditing) {
        const { data } = await client.put(`/informes/${id}/`, payload);
        setInforme(data);
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
          flatErrors[key] = Array.isArray(val) ? val.join(' ') : val;
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
      console.error('Error al finalizar:', err.response?.data || err);
      setErrors({ general: err.response?.data?.detail || 'Error al finalizar el informe.' });
    }
  };

  // Descarga el PDF con Axios, que envía el token en la cabecera Authorization.
  // Antes el token iba en la URL (?token=...) y quedaba en el historial (auditoría I-5).
  const downloadPDF = async () => {
    const safeName = (numeroCaso || id).toString().replace(/[^a-zA-Z0-9\-]/g, '_');
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
          <h1>{isEditing ? `Informe ${numeroCaso}` : 'Nuevo Informe'}</h1>
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
        <div className="card">
          <div className="card-header"><h2>Datos Generales</h2></div>
          <div className="card-body">
            <div className="form-row">
              <div className={`form-group ${errors.numeroCaso ? 'has-error' : ''}`}>
                <label htmlFor="numeroCaso">Número de Caso <span className="required">*</span></label>
                <input
                  id="numeroCaso"
                  type="text"
                  value={numeroCaso}
                  onChange={(e) => { setNumeroCaso(e.target.value); setErrors(p => ({...p, numeroCaso: null})); }}
                  placeholder="Ej: PAT-2026-0001"
                  disabled={informe?.estado === 'finalizado' || !puedeEditar}
                />
                {errors.numeroCaso && <span className="field-error">{errors.numeroCaso}</span>}
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
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="tipoMuestra">Tipo de Muestra</label>
                <input
                  id="tipoMuestra"
                  type="text"
                  value={tipoMuestra}
                  onChange={(e) => setTipoMuestra(e.target.value)}
                  placeholder="Ej: Biopsia escisional"
                  disabled={informe?.estado === 'finalizado' || !puedeEditar}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Campos dinámicos */}
        {plantillas.length > 0 && (
          <div className="card">
            <div className="card-header"><h2>Descripción Macroscópica</h2></div>
            <div className="card-body">
              <div className="dynamic-fields">
                {plantillas.map(renderField)}
              </div>
            </div>
          </div>
        )}

        {/* Notas */}
        <div className="card">
          <div className="card-header"><h2>Notas Adicionales</h2></div>
          <div className="card-body">
            <div className="form-group">
              <textarea
                id="notas"
                value={notas}
                onChange={(e) => setNotas(e.target.value)}
                rows={3}
                placeholder="Observaciones o notas adicionales..."
                disabled={informe?.estado === 'finalizado' || !puedeEditar}
              />
            </div>
          </div>
        </div>

        {/* Vista previa del texto generado */}
        {informe?.texto_generado && (
          <div className="card">
            <div className="card-header"><h2>Texto Generado</h2></div>
            <div className="card-body">
              <div className="generated-text">
                {informe.texto_generado}
              </div>
            </div>
          </div>
        )}

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

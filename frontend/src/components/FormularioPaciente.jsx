import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import client, { LISTA_COMPLETA, resultados } from '../api/client';
import useOpciones from '../hooks/useOpciones';
import { conOpcionActual, hoyISO } from '../utils/formularios';

const PACIENTE_VACIO = {
  tipo_documento: 'CC', numero_documento: '', nombres: '', apellidos: '',
  fecha_nacimiento: '', sexo: '', eps: '',
};

// Ventana para crear o editar un paciente. La usan PacientesPage y el selector de
// paciente del informe. Se dibuja en document.body (portal) porque el informe ya
// es un <form> y un formulario no puede ir dentro de otro.
export default function FormularioPaciente({ paciente, onGuardado, onCancelar }) {
  const { opciones } = useOpciones();
  const [form, setForm] = useState(() => (
    paciente ? { ...paciente, eps: paciente.eps ?? '' } : { ...PACIENTE_VACIO }
  ));
  const [errores, setErrores] = useState({});
  const [epsActivas, setEpsActivas] = useState([]);

  useEffect(() => {
    client.get('/pacientes/eps/', { params: { ...LISTA_COMPLETA, activa: true } })
      .then(({ data }) => setEpsActivas(resultados(data)))
      .catch(() => setErrores({ detail: 'No se pudo cargar la lista de EPS.' }));
  }, []);

  const cambiar = (campo) => (e) => setForm({ ...form, [campo]: e.target.value });

  // Las EPS activas, más la actual del paciente si ya no está activa: la conserva (D-4).
  const opcionesEps = conOpcionActual(epsActivas, form.eps, form.eps_nombre ?? 'EPS actual');

  const guardar = async (e) => {
    e.preventDefault();
    // Los eventos de React atraviesan el portal: sin esto, también se enviaría el informe.
    e.stopPropagation();
    setErrores({});
    const payload = {
      tipo_documento: form.tipo_documento,
      numero_documento: form.numero_documento,
      nombres: form.nombres,
      apellidos: form.apellidos,
      fecha_nacimiento: form.fecha_nacimiento,
      sexo: form.sexo,
      eps: form.eps ? Number(form.eps) : null,
    };
    try {
      const { data } = form.id
        ? await client.put(`/pacientes/${form.id}/`, payload)
        : await client.post('/pacientes/', payload);
      onGuardado(data);
    } catch (err) {
      const datos = err.response?.data;
      if (datos && typeof datos === 'object' && !datos.detail) {
        setErrores(datos);
      } else {
        setErrores({ detail: datos?.detail || 'Error al guardar el paciente.' });
      }
    }
  };

  const errorDe = (campo) => {
    const valor = errores[campo];
    if (!valor) return null;
    return <span className="field-error">{Array.isArray(valor) ? valor[0] : valor}</span>;
  };

  return createPortal(
    <div className="modal-overlay" onClick={onCancelar}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <h2>{form.id ? 'Editar paciente' : 'Nuevo paciente'}</h2>
        {errores.detail && <div className="alert alert-error">{errores.detail}</div>}
        {errorDe('non_field_errors')}
        <form onSubmit={guardar}>
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="paciente-tipo-documento">Tipo de documento</label>
              <select id="paciente-tipo-documento" value={form.tipo_documento} onChange={cambiar('tipo_documento')} required>
                {opciones.tipos_documento.map((o) => (
                  <option key={o.valor} value={o.valor}>{o.etiqueta}</option>
                ))}
              </select>
              {errorDe('tipo_documento')}
            </div>
            <div className="form-group">
              <label htmlFor="paciente-numero-documento">Número de documento</label>
              <input id="paciente-numero-documento" value={form.numero_documento} onChange={cambiar('numero_documento')} maxLength={20} required />
              {errorDe('numero_documento')}
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="paciente-nombres">Nombres</label>
              <input id="paciente-nombres" value={form.nombres} onChange={cambiar('nombres')} maxLength={150} required />
              {errorDe('nombres')}
            </div>
            <div className="form-group">
              <label htmlFor="paciente-apellidos">Apellidos</label>
              <input id="paciente-apellidos" value={form.apellidos} onChange={cambiar('apellidos')} maxLength={150} required />
              {errorDe('apellidos')}
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="paciente-fecha-nacimiento">Fecha de nacimiento</label>
              <input id="paciente-fecha-nacimiento" type="date" value={form.fecha_nacimiento} onChange={cambiar('fecha_nacimiento')} max={hoyISO()} required />
              {errorDe('fecha_nacimiento')}
            </div>
            <div className="form-group">
              <label htmlFor="paciente-sexo">Sexo</label>
              <select id="paciente-sexo" value={form.sexo} onChange={cambiar('sexo')} required>
                <option value="">Seleccione...</option>
                {opciones.sexos.map((o) => (
                  <option key={o.valor} value={o.valor}>{o.etiqueta}</option>
                ))}
              </select>
              {errorDe('sexo')}
            </div>
          </div>
          <div className="form-group">
            <label htmlFor="paciente-eps">EPS</label>
            <select id="paciente-eps" value={form.eps} onChange={cambiar('eps')}>
              <option value="">Sin EPS</option>
              {opcionesEps.map((e) => (
                <option key={e.id} value={e.id}>{e.nombre}</option>
              ))}
            </select>
            {errorDe('eps')}
          </div>
          <div className="form-actions">
            <button type="button" className="btn btn-outline" onClick={onCancelar}>Cancelar</button>
            <button type="submit" className="btn btn-primary">Guardar</button>
          </div>
        </form>
      </div>
    </div>,
    document.body,
  );
}

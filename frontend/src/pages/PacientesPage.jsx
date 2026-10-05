import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import client, { LISTA_COMPLETA, resultados } from '../api/client';
import useOpciones, { etiquetaDe } from '../hooks/useOpciones';

const TAMANO_PAGINA = 20; // Debe coincidir con PAGE_SIZE de backend/config/settings.py

const PACIENTE_VACIO = {
  tipo_documento: 'CC', numero_documento: '', nombres: '', apellidos: '',
  fecha_nacimiento: '', sexo: '', eps: '',
};

// Fecha local de hoy en formato AAAA-MM-DD, para que el calendario no ofrezca fechas futuras.
const hoyISO = () => new Date().toLocaleDateString('en-CA');

// Pacientes (informe v2, etapa 3). Todos leen; patólogo y admin crean y editan;
// solo el admin borra (decisión D-11). La autorización real la hace el backend.
export default function PacientesPage() {
  const { canWrite, isAdmin } = useAuth();
  const { opciones } = useOpciones();

  const [pacientes, setPacientes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [query, setQuery] = useState('');
  // Búsqueda aplicada: al cambiar de página se usa esta, no lo que se haya escrito después.
  const [consulta, setConsulta] = useState('');
  const [pagina, setPagina] = useState(1);
  const [total, setTotal] = useState(0);
  const [hayAnterior, setHayAnterior] = useState(false);
  const [haySiguiente, setHaySiguiente] = useState(false);

  const [form, setForm] = useState(null); // null = cerrado, {...} = nuevo o editar
  const [erroresForm, setErroresForm] = useState({});
  const [epsActivas, setEpsActivas] = useState([]);
  const [confirmDelete, setConfirmDelete] = useState(null); // paciente a borrar

  const buscar = async (q, numeroPagina) => {
    setLoading(true);
    const params = {};
    if (q) params.q = q;
    if (numeroPagina > 1) params.page = numeroPagina;
    try {
      const { data } = await client.get('/pacientes/', { params });
      const lista = resultados(data);
      setPacientes(lista);
      setTotal(data.count ?? lista.length);
      setHayAnterior(Boolean(data.previous));
      setHaySiguiente(Boolean(data.next));
      setPagina(numeroPagina);
      setConsulta(q);
    } catch {
      setError('No se pudieron cargar los pacientes.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { buscar('', 1); }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    setError('');
    buscar(query.trim(), 1);
  };

  const abrirFormulario = async (paciente) => {
    setErroresForm({});
    setForm(paciente ? { ...paciente, eps: paciente.eps ?? '' } : { ...PACIENTE_VACIO });
    try {
      const { data } = await client.get('/pacientes/eps/', { params: { ...LISTA_COMPLETA, activa: true } });
      setEpsActivas(resultados(data));
    } catch {
      setError('No se pudo cargar la lista de EPS.');
    }
  };

  const cambiar = (campo) => (e) => setForm({ ...form, [campo]: e.target.value });

  // Las EPS activas, más la actual del paciente si ya no está activa: la conserva (D-4).
  const opcionesEps = form?.eps && !epsActivas.some((e) => e.id === Number(form.eps))
    ? [{ id: Number(form.eps), nombre: `${form.eps_nombre ?? 'EPS actual'} (desactivada)` }, ...epsActivas]
    : epsActivas;

  const guardar = async (e) => {
    e.preventDefault();
    setErroresForm({});
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
      if (form.id) {
        await client.put(`/pacientes/${form.id}/`, payload);
      } else {
        await client.post('/pacientes/', payload);
      }
      setForm(null);
      buscar(consulta, form.id ? pagina : 1);
    } catch (err) {
      const datos = err.response?.data;
      if (datos && typeof datos === 'object' && !datos.detail) {
        setErroresForm(datos);
      } else {
        setErroresForm({ detail: datos?.detail || 'Error al guardar el paciente.' });
      }
    }
  };

  const eliminar = async () => {
    try {
      await client.delete(`/pacientes/${confirmDelete.id}/`);
      // Si se borra el único paciente de la última página, se vuelve a la anterior.
      buscar(consulta, pacientes.length === 1 && pagina > 1 ? pagina - 1 : pagina);
    } catch (err) {
      setError(err.response?.data?.detail || 'No se pudo eliminar el paciente.');
    } finally {
      setConfirmDelete(null);
    }
  };

  const errorDe = (campo) => {
    const valor = erroresForm[campo];
    if (!valor) return null;
    return <span className="field-error">{Array.isArray(valor) ? valor[0] : valor}</span>;
  };

  const desde = (pagina - 1) * TAMANO_PAGINA + 1;
  const hasta = desde + pacientes.length - 1;

  return (
    <div className="pacientes-page">
      <div className="page-header">
        <div>
          <h1>Pacientes</h1>
          <p className="text-muted">Datos del paciente que aparecen en el informe</p>
        </div>
        {canWrite && (
          <div className="header-actions">
            <button className="btn btn-primary" onClick={() => abrirFormulario(null)}>+ Paciente</button>
          </div>
        )}
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="card">
        <div className="card-body">
          <form onSubmit={handleSearch} className="search-form">
            <div className="form-row">
              <div className="form-group flex-2">
                <label htmlFor="buscar-paciente">Buscar</label>
                <input
                  id="buscar-paciente"
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Número de documento, nombres o apellidos..."
                />
              </div>
            </div>
            <button type="submit" className="btn btn-primary" disabled={loading}>Buscar</button>
          </form>
        </div>
      </div>

      <div className="card">
        <div className="card-header"><h2>Pacientes ({total})</h2></div>
        <div className="card-body">
          {loading ? (
            <div className="loading-center"><span className="spinner"></span></div>
          ) : pacientes.length === 0 ? (
            <div className="empty-state">
              <p>{consulta ? 'No se encontraron pacientes con esa búsqueda.' : 'Aún no hay pacientes registrados.'}</p>
            </div>
          ) : (
            <div className="table-responsive">
              <table>
                <thead>
                  <tr>
                    <th>Documento</th><th>Paciente</th><th>Edad</th><th>Sexo</th><th>EPS</th>
                    {canWrite && <th>Acciones</th>}
                  </tr>
                </thead>
                <tbody>
                  {pacientes.map((p) => (
                    <tr key={p.id}>
                      <td>{p.tipo_documento} {p.numero_documento}</td>
                      <td><strong>{p.nombres} {p.apellidos}</strong></td>
                      <td>{p.edad}</td>
                      <td>{etiquetaDe(opciones.sexos, p.sexo)}</td>
                      <td>{p.eps_nombre || <span className="text-muted">Sin EPS</span>}</td>
                      {canWrite && (
                        <td>
                          <div className="table-actions">
                            <button className="btn btn-outline btn-xs" onClick={() => abrirFormulario(p)}>Editar</button>
                            {isAdmin && (
                              <button className="btn btn-danger-outline btn-xs" onClick={() => setConfirmDelete(p)}>
                                Eliminar
                              </button>
                            )}
                          </div>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {!loading && pacientes.length > 0 && (
            <div className="paginacion">
              <button className="btn btn-outline btn-sm" onClick={() => buscar(consulta, pagina - 1)} disabled={!hayAnterior}>
                ← Anterior
              </button>
              <span className="text-muted">Mostrando {desde}–{hasta} de {total}</span>
              <button className="btn btn-outline btn-sm" onClick={() => buscar(consulta, pagina + 1)} disabled={!haySiguiente}>
                Siguiente →
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Crear o editar paciente */}
      {form && (
        <div className="modal-overlay" onClick={() => setForm(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <h2>{form.id ? 'Editar paciente' : 'Nuevo paciente'}</h2>
            {erroresForm.detail && <div className="alert alert-error">{erroresForm.detail}</div>}
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
                <button type="button" className="btn btn-outline" onClick={() => setForm(null)}>Cancelar</button>
                <button type="submit" className="btn btn-primary">Guardar</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Confirmar eliminación (solo admin) */}
      {confirmDelete && (
        <div className="modal-overlay" onClick={() => setConfirmDelete(null)}>
          <div className="modal-card modal-card-sm" onClick={(e) => e.stopPropagation()}>
            <h2>¿Eliminar paciente?</h2>
            <p className="text-muted">
              Se eliminará a {confirmDelete.nombres} {confirmDelete.apellidos}. Esta acción no se puede deshacer.
            </p>
            <div className="form-actions">
              <button className="btn btn-outline" onClick={() => setConfirmDelete(null)}>Cancelar</button>
              <button className="btn btn-danger" onClick={eliminar}>Eliminar</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

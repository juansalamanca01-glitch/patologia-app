import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import client, { LISTA_COMPLETA, resultados } from '../api/client';
import useOpciones, { etiquetaDe } from '../hooks/useOpciones';
import EstadoBadge from '../components/EstadoBadge';
import FormularioPaciente from '../components/FormularioPaciente';

const TAMANO_PAGINA = 20; // Debe coincidir con PAGE_SIZE de backend/config/settings.py

// Pacientes (informe v2, etapa 3). Todos leen y ven el historial de informes de
// cada paciente (etapa 4); patólogo y admin crean y editan; solo el admin borra, y
// solo si el paciente no tiene informes (decisión D-11). La autorización real la
// hace el backend.
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

  // undefined = cerrado, null = paciente nuevo, {...} = paciente a editar
  const [editando, setEditando] = useState(undefined);
  const [confirmDelete, setConfirmDelete] = useState(null); // paciente a borrar
  const [historial, setHistorial] = useState(null); // { paciente, informes, cargando, error }

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

  const guardado = () => {
    // Un paciente nuevo se busca desde la primera página; uno editado, en la misma.
    const paginaDestino = editando ? pagina : 1;
    setEditando(undefined);
    buscar(consulta, paginaDestino);
  };

  const verHistorial = async (paciente) => {
    setHistorial({ paciente, informes: [], cargando: true, error: '' });
    try {
      const { data } = await client.get(`/pacientes/${paciente.id}/informes/`, { params: LISTA_COMPLETA });
      setHistorial({ paciente, informes: resultados(data), cargando: false, error: '' });
    } catch {
      setHistorial({ paciente, informes: [], cargando: false, error: 'No se pudieron cargar los informes del paciente.' });
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
            <button className="btn btn-primary" onClick={() => setEditando(null)}>+ Paciente</button>
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
                    <th>Documento</th><th>Paciente</th><th>Edad</th><th>Sexo</th><th>EPS</th><th>Acciones</th>
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
                      <td>
                        <div className="table-actions">
                          <button className="btn btn-outline btn-xs" onClick={() => verHistorial(p)}>Informes</button>
                          {canWrite && (
                            <button className="btn btn-outline btn-xs" onClick={() => setEditando(p)}>Editar</button>
                          )}
                          {isAdmin && (
                            <button className="btn btn-danger-outline btn-xs" onClick={() => setConfirmDelete(p)}>
                              Eliminar
                            </button>
                          )}
                        </div>
                      </td>
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
      {editando !== undefined && (
        <FormularioPaciente paciente={editando} onGuardado={guardado} onCancelar={() => setEditando(undefined)} />
      )}

      {/* Historial de informes del paciente (etapa 4) */}
      {historial && (
        <div className="modal-overlay" onClick={() => setHistorial(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <h2>Informes de {historial.paciente.nombres} {historial.paciente.apellidos}</h2>
            {historial.error && <div className="alert alert-error">{historial.error}</div>}
            {historial.cargando ? (
              <div className="loading-center"><span className="spinner"></span></div>
            ) : !historial.error && historial.informes.length === 0 ? (
              <p className="text-muted">Este paciente no tiene informes.</p>
            ) : historial.informes.length > 0 && (
              <div className="table-responsive">
                <table>
                  <thead>
                    <tr><th>N.º de petición</th><th>Tipo de estudio</th><th>Patología</th><th>Fecha</th><th>Estado</th></tr>
                  </thead>
                  <tbody>
                    {historial.informes.map((inf) => (
                      <tr key={inf.id}>
                        <td><Link to={`/informes/${inf.id}`}>{inf.numero_peticion}</Link></td>
                        <td>{etiquetaDe(opciones.tipos_estudio, inf.tipo_estudio)}</td>
                        <td>{inf.patologia_nombre}</td>
                        <td>{inf.fecha}</td>
                        <td><EstadoBadge estado={inf.estado} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <div className="form-actions">
              <button className="btn btn-outline" onClick={() => setHistorial(null)}>Cerrar</button>
            </div>
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

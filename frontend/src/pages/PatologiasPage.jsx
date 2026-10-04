import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import client, { LISTA_COMPLETA, resultados } from '../api/client';

const CATEGORIA_VACIA = { nombre: '', descripcion: '', color: '#2563eb' };
const PATOLOGIA_VACIA = { nombre: '', categoria: '', descripcion: '', protocolo_medico: '', activa: true };

export default function PatologiasPage() {
  const { canWrite } = useAuth();
  const [categorias, setCategorias] = useState([]);
  const [patologias, setPatologias] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filtroCategoria, setFiltroCategoria] = useState('');

  const [formCategoria, setFormCategoria] = useState(null); // null = cerrado, {} = nuevo, {...} = editar
  const [formPatologia, setFormPatologia] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null); // { tipo, id }

  const fetchData = async () => {
    setLoading(true);
    try {
      const [catRes, patRes] = await Promise.all([
        client.get('/categorias/', { params: LISTA_COMPLETA }),
        client.get('/patologias/', {
          params: filtroCategoria ? { ...LISTA_COMPLETA, categoria: filtroCategoria } : LISTA_COMPLETA,
        }),
      ]);
      setCategorias(resultados(catRes.data));
      setPatologias(resultados(patRes.data));
    } catch (err) {
      setError('No se pudieron cargar las patologías y categorías.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [filtroCategoria]);

  const guardarCategoria = async (e) => {
    e.preventDefault();
    try {
      if (formCategoria.id) {
        await client.patch(`/categorias/${formCategoria.id}/`, formCategoria);
      } else {
        await client.post('/categorias/', formCategoria);
      }
      setFormCategoria(null);
      fetchData();
    } catch (err) {
      setError(err.response?.data?.nombre?.[0] || err.response?.data?.detail || 'Error al guardar la categoría.');
    }
  };

  const guardarPatologia = async (e) => {
    e.preventDefault();
    try {
      const payload = { ...formPatologia, categoria: formPatologia.categoria || null };
      if (formPatologia.id) {
        await client.patch(`/patologias/${formPatologia.id}/`, payload);
      } else {
        await client.post('/patologias/', payload);
      }
      setFormPatologia(null);
      fetchData();
    } catch (err) {
      setError(err.response?.data?.nombre?.[0] || err.response?.data?.detail || 'Error al guardar la patología.');
    }
  };

  const eliminar = async () => {
    const { tipo, id } = confirmDelete;
    try {
      await client.delete(`/${tipo}/${id}/`);
      setConfirmDelete(null);
      fetchData();
    } catch (err) {
      setError(err.response?.data?.detail || 'No se pudo eliminar.');
      setConfirmDelete(null);
    }
  };

  return (
    <div className="patologias-page">
      <div className="page-header">
        <div>
          <h1>Patologías y Categorías</h1>
          <p className="text-muted">Catálogo clínico usado para generar informes</p>
        </div>
        {canWrite && (
          <div className="header-actions">
            <button className="btn btn-outline" onClick={() => setFormCategoria({ ...CATEGORIA_VACIA })}>
              + Categoría
            </button>
            <button className="btn btn-primary" onClick={() => setFormPatologia({ ...PATOLOGIA_VACIA })}>
              + Patología
            </button>
          </div>
        )}
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {/* Categorías */}
      <div className="card">
        <div className="card-header"><h2>Categorías</h2></div>
        <div className="card-body">
          {categorias.length === 0 ? (
            <p className="text-muted">Aún no hay categorías registradas.</p>
          ) : (
            <div className="categoria-chip-list">
              <button
                className={`categoria-chip ${filtroCategoria === '' ? 'categoria-chip-activo' : ''}`}
                onClick={() => setFiltroCategoria('')}
              >
                Todas
              </button>
              {categorias.map((c) => (
                <button
                  key={c.id}
                  className={`categoria-chip ${filtroCategoria === String(c.id) ? 'categoria-chip-activo' : ''}`}
                  style={{ borderColor: c.color }}
                  onClick={() => setFiltroCategoria(String(c.id))}
                >
                  <span className="categoria-dot" style={{ background: c.color }}></span>
                  {c.nombre} <span className="text-muted">({c.total_patologias})</span>
                  {canWrite && (
                    <span className="categoria-chip-actions">
                      <span onClick={(e) => { e.stopPropagation(); setFormCategoria(c); }}>✎</span>
                      <span onClick={(e) => { e.stopPropagation(); setConfirmDelete({ tipo: 'categorias', id: c.id }); }}>✕</span>
                    </span>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Patologías */}
      <div className="card">
        <div className="card-header"><h2>Patologías</h2></div>
        <div className="card-body">
          {loading ? (
            <div className="loading-center"><span className="spinner"></span></div>
          ) : patologias.length === 0 ? (
            <div className="empty-state"><p>No hay patologías registradas.</p></div>
          ) : (
            <div className="table-responsive">
              <table>
                <thead>
                  <tr><th>Nombre</th><th>Categoría</th><th>Estado</th>{canWrite && <th>Acciones</th>}</tr>
                </thead>
                <tbody>
                  {patologias.map((p) => (
                    <tr key={p.id}>
                      <td><strong>{p.nombre}</strong></td>
                      <td>{p.categoria_nombre || <span className="text-muted">Sin categoría</span>}</td>
                      <td>
                        <span className={`badge ${p.activa ? 'badge-success' : 'badge-warning'}`}>
                          {p.activa ? 'Activa' : 'Inactiva'}
                        </span>
                      </td>
                      {canWrite && (
                        <td>
                          <div className="table-actions">
                            <button className="btn btn-outline btn-xs" onClick={() => setFormPatologia(p)}>Editar</button>
                            <button
                              className="btn btn-danger-outline btn-xs"
                              onClick={() => setConfirmDelete({ tipo: 'patologias', id: p.id })}
                            >
                              Eliminar
                            </button>
                          </div>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Modal Categoría */}
      {formCategoria && (
        <div className="modal-overlay" onClick={() => setFormCategoria(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <h2>{formCategoria.id ? 'Editar categoría' : 'Nueva categoría'}</h2>
            <form onSubmit={guardarCategoria}>
              <div className="form-group">
                <label>Nombre</label>
                <input
                  value={formCategoria.nombre}
                  onChange={(e) => setFormCategoria({ ...formCategoria, nombre: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Descripción</label>
                <textarea
                  value={formCategoria.descripcion}
                  onChange={(e) => setFormCategoria({ ...formCategoria, descripcion: e.target.value })}
                  rows={3}
                />
              </div>
              <div className="form-group">
                <label>Color</label>
                <input
                  type="color"
                  value={formCategoria.color}
                  onChange={(e) => setFormCategoria({ ...formCategoria, color: e.target.value })}
                />
              </div>
              <div className="form-actions">
                <button type="button" className="btn btn-outline" onClick={() => setFormCategoria(null)}>Cancelar</button>
                <button type="submit" className="btn btn-primary">Guardar</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Patología */}
      {formPatologia && (
        <div className="modal-overlay" onClick={() => setFormPatologia(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <h2>{formPatologia.id ? 'Editar patología' : 'Nueva patología'}</h2>
            <form onSubmit={guardarPatologia}>
              <div className="form-group">
                <label>Nombre</label>
                <input
                  value={formPatologia.nombre}
                  onChange={(e) => setFormPatologia({ ...formPatologia, nombre: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Categoría</label>
                <select
                  value={formPatologia.categoria || ''}
                  onChange={(e) => setFormPatologia({ ...formPatologia, categoria: e.target.value })}
                >
                  <option value="">Sin categoría</option>
                  {categorias.map((c) => (
                    <option key={c.id} value={c.id}>{c.nombre}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Descripción</label>
                <textarea
                  value={formPatologia.descripcion}
                  onChange={(e) => setFormPatologia({ ...formPatologia, descripcion: e.target.value })}
                  rows={3}
                />
              </div>
              <div className="form-group">
                <label>Protocolo médico</label>
                <textarea
                  value={formPatologia.protocolo_medico}
                  onChange={(e) => setFormPatologia({ ...formPatologia, protocolo_medico: e.target.value })}
                  rows={3}
                />
              </div>
              {/* Desactivar en lugar de borrar (decisión D-4): una patología con informes no se puede borrar. */}
              <div className="form-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={formPatologia.activa !== false}
                    onChange={(e) => setFormPatologia({ ...formPatologia, activa: e.target.checked })}
                  />
                  <span>Activa (se ofrece al crear informes)</span>
                </label>
              </div>
              <div className="form-actions">
                <button type="button" className="btn btn-outline" onClick={() => setFormPatologia(null)}>Cancelar</button>
                <button type="submit" className="btn btn-primary">Guardar</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Confirmar eliminación */}
      {confirmDelete && (
        <div className="modal-overlay" onClick={() => setConfirmDelete(null)}>
          <div className="modal-card modal-card-sm" onClick={(e) => e.stopPropagation()}>
            <h2>¿Eliminar?</h2>
            <p className="text-muted">Esta acción no se puede deshacer.</p>
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

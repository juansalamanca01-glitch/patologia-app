import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import client from '../api/client';

export default function DashboardPage() {
  const { user, canWrite } = useAuth();
  const [stats, setStats] = useState({ total: 0, borradores: 0, finalizados: 0 });
  const [recientes, setRecientes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [confirmDeleteId, setConfirmDeleteId] = useState(null);

  const fetchData = async () => {
    try {
      const { data } = await client.get('/informes/');
      const informes = data.results || data;
      setRecientes(Array.isArray(informes) ? informes.slice(0, 10) : []);
      setStats({
        total: Array.isArray(informes) ? informes.length : (data.count || 0),
        borradores: Array.isArray(informes) ? informes.filter(i => i.estado === 'borrador').length : 0,
        finalizados: Array.isArray(informes) ? informes.filter(i => i.estado === 'finalizado').length : 0,
      });
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const handleDelete = async (id) => {
    if (confirmDeleteId !== id) {
      setConfirmDeleteId(id);
      return;
    }
    try {
      await client.delete(`/informes/${id}/`);
      setConfirmDeleteId(null);
      fetchData();
    } catch (err) {
      console.error('Error eliminando informe:', err);
    }
  };

  const ROL_LABELS = { admin: 'Administrador', patologo: 'Patólogo', auditor: 'Auditor' };
  const ESTADO_CLASS = { borrador: 'badge-warning', finalizado: 'badge-success' };

  return (
    <div className="dashboard">
      <div className="page-header">
        <div>
          <h1>Bienvenido, {user?.nombre_completo || user?.username}</h1>
          <p className="text-muted">Panel de control — {ROL_LABELS[user?.rol] || user?.rol}</p>
        </div>
        {canWrite && (
          <Link to="/informes/nuevo" className="btn btn-primary">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="18" height="18">
              <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            Nuevo Informe
          </Link>
        )}
      </div>

      {/* Stats cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon stat-icon-blue">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="24" height="24">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
              <polyline points="14,2 14,8 20,8"/>
            </svg>
          </div>
          <div className="stat-info">
            <span className="stat-number">{stats.total}</span>
            <span className="stat-label">Total Informes</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon stat-icon-yellow">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="24" height="24">
              <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
          </div>
          <div className="stat-info">
            <span className="stat-number">{stats.borradores}</span>
            <span className="stat-label">Borradores</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon stat-icon-green">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="24" height="24">
              <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/>
              <polyline points="22,4 12,14.01 9,11.01"/>
            </svg>
          </div>
          <div className="stat-info">
            <span className="stat-number">{stats.finalizados}</span>
            <span className="stat-label">Finalizados</span>
          </div>
        </div>
      </div>

      {/* Recent reports */}
      <div className="card">
        <div className="card-header">
          <h2>Informes Recientes</h2>
          <Link to="/buscar" className="btn btn-outline btn-sm">Ver todos</Link>
        </div>
        <div className="card-body">
          {loading ? (
            <div className="loading-center"><span className="spinner"></span></div>
          ) : recientes.length === 0 ? (
            <div className="empty-state">
              <p>No hay informes registrados aún.</p>
              {canWrite && <Link to="/informes/nuevo" className="btn btn-primary btn-sm">Crear primer informe</Link>}
            </div>
          ) : (
            <div className="table-responsive">
              <table>
                <thead>
                  <tr>
                    <th>Nº Caso</th>
                    <th>Patología</th>
                    <th>Fecha</th>
                    <th>Estado</th>
                    <th>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {recientes.map((inf) => (
                    <tr key={inf.id}>
                      <td><strong>{inf.numero_caso}</strong></td>
                      <td>{inf.patologia_nombre}</td>
                      <td>{inf.fecha}</td>
                      <td>
                        <span className={`badge ${ESTADO_CLASS[inf.estado] || ''}`}>
                          {inf.estado === 'borrador' ? 'Borrador' : 'Finalizado'}
                        </span>
                      </td>
                      <td>
                        <div className="table-actions">
                          <Link to={`/informes/${inf.id}`} className="btn btn-outline btn-xs">Ver</Link>
                          {canWrite && inf.estado === 'borrador' && (
                            confirmDeleteId === inf.id ? (
                              <>
                                <button className="btn btn-danger btn-xs" onClick={() => handleDelete(inf.id)}>
                                  Confirmar
                                </button>
                                <button className="btn btn-outline btn-xs" onClick={() => setConfirmDeleteId(null)}>
                                  No
                                </button>
                              </>
                            ) : (
                              <button
                                className="btn btn-danger-outline btn-xs"
                                onClick={() => handleDelete(inf.id)}
                                title="Eliminar borrador"
                              >
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="14" height="14">
                                  <polyline points="3,6 5,6 21,6"/>
                                  <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
                                </svg>
                              </button>
                            )
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}


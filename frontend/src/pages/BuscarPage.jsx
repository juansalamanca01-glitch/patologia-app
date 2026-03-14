import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import client from '../api/client';

export default function BuscarPage() {
  const [query, setQuery] = useState('');
  const [fechaDesde, setFechaDesde] = useState('');
  const [fechaHasta, setFechaHasta] = useState('');
  const [estado, setEstado] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const handleSearch = async (e) => {
    e?.preventDefault();
    setLoading(true);
    setSearched(true);

    const params = new URLSearchParams();
    if (query) params.append('q', query);
    if (fechaDesde) params.append('fecha_desde', fechaDesde);
    if (fechaHasta) params.append('fecha_hasta', fechaHasta);
    if (estado) params.append('estado', estado);

    try {
      const { data } = await client.get(`/informes/?${params.toString()}`);
      setResults(data.results || data);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handleSearch();
  }, []);

  const ESTADO_CLASS = { borrador: 'badge-warning', finalizado: 'badge-success' };

  return (
    <div className="buscar-page">
      <div className="page-header">
        <h1>Buscar Informes</h1>
      </div>

      <div className="card">
        <div className="card-body">
          <form onSubmit={handleSearch} className="search-form">
            <div className="form-row">
              <div className="form-group flex-2">
                <label htmlFor="search-query">Buscar</label>
                <input
                  id="search-query"
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Número de caso, patología o tipo de muestra..."
                />
              </div>
              <div className="form-group">
                <label htmlFor="fecha-desde">Desde</label>
                <input
                  id="fecha-desde"
                  type="date"
                  value={fechaDesde}
                  onChange={(e) => setFechaDesde(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label htmlFor="fecha-hasta">Hasta</label>
                <input
                  id="fecha-hasta"
                  type="date"
                  value={fechaHasta}
                  onChange={(e) => setFechaHasta(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label htmlFor="estado-filter">Estado</label>
                <select
                  id="estado-filter"
                  value={estado}
                  onChange={(e) => setEstado(e.target.value)}
                >
                  <option value="">Todos</option>
                  <option value="borrador">Borrador</option>
                  <option value="finalizado">Finalizado</option>
                </select>
              </div>
            </div>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? <span className="spinner"></span> : 'Buscar'}
            </button>
          </form>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h2>Resultados {searched && `(${results.length})`}</h2>
        </div>
        <div className="card-body">
          {loading ? (
            <div className="loading-center"><span className="spinner"></span></div>
          ) : results.length === 0 ? (
            <div className="empty-state">
              <p>{searched ? 'No se encontraron informes con esos criterios.' : 'Ingrese criterios de búsqueda.'}</p>
            </div>
          ) : (
            <div className="table-responsive">
              <table>
                <thead>
                  <tr>
                    <th>Nº Caso</th>
                    <th>Patología</th>
                    <th>Tipo Muestra</th>
                    <th>Autor</th>
                    <th>Fecha</th>
                    <th>Estado</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((inf) => (
                    <tr key={inf.id}>
                      <td><strong>{inf.numero_caso}</strong></td>
                      <td>{inf.patologia_nombre}</td>
                      <td>{inf.tipo_muestra || '—'}</td>
                      <td>{inf.autor_nombre}</td>
                      <td>{inf.fecha}</td>
                      <td>
                        <span className={`badge ${ESTADO_CLASS[inf.estado] || ''}`}>
                          {inf.estado === 'borrador' ? 'Borrador' : 'Finalizado'}
                        </span>
                      </td>
                      <td>
                        <Link to={`/informes/${inf.id}`} className="btn btn-outline btn-xs">Ver</Link>
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

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import client, { resultados } from '../api/client';
import EstadoBadge from '../components/EstadoBadge';

const TAMANO_PAGINA = 20; // Debe coincidir con PAGE_SIZE de backend/config/settings.py

export default function BuscarPage() {
  const [query, setQuery] = useState('');
  const [fechaDesde, setFechaDesde] = useState('');
  const [fechaHasta, setFechaHasta] = useState('');
  const [estado, setEstado] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  // Paginación (auditoría I-4): la API devuelve los informes de 20 en 20.
  const [pagina, setPagina] = useState(1);
  const [total, setTotal] = useState(0);
  const [hayAnterior, setHayAnterior] = useState(false);
  const [haySiguiente, setHaySiguiente] = useState(false);
  // Filtros de la última búsqueda: al cambiar de página se usan estos, no lo
  // que el usuario haya escrito después sin pulsar "Buscar".
  const [filtrosAplicados, setFiltrosAplicados] = useState({});

  const buscar = async (filtros, numeroPagina) => {
    setLoading(true);
    setSearched(true);

    const params = new URLSearchParams();
    Object.entries(filtros).forEach(([clave, valor]) => {
      if (valor) params.append(clave, valor);
    });
    if (numeroPagina > 1) params.append('page', numeroPagina);

    try {
      const { data } = await client.get(`/informes/?${params.toString()}`);
      const informes = resultados(data);
      setResults(informes);
      setTotal(data.count ?? informes.length);
      setHayAnterior(Boolean(data.previous));
      setHaySiguiente(Boolean(data.next));
      setPagina(numeroPagina);
    } catch {
      setResults([]);
      setTotal(0);
      setHayAnterior(false);
      setHaySiguiente(false);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e?.preventDefault();
    const filtros = { q: query, fecha_desde: fechaDesde, fecha_hasta: fechaHasta, estado };
    setFiltrosAplicados(filtros);
    buscar(filtros, 1);
  };

  const cambiarPagina = (numeroPagina) => buscar(filtrosAplicados, numeroPagina);

  // Rango mostrado, p. ej. "21–25 de 25".
  const desde = (pagina - 1) * TAMANO_PAGINA + 1;
  const hasta = desde + results.length - 1;

  useEffect(() => {
    handleSearch();
  }, []);


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
          <h2>Resultados {searched && `(${total})`}</h2>
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
                        <EstadoBadge estado={inf.estado} />
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

          {!loading && results.length > 0 && (
            <div className="paginacion">
              <button
                className="btn btn-outline btn-sm"
                onClick={() => cambiarPagina(pagina - 1)}
                disabled={!hayAnterior}
              >
                ← Anterior
              </button>
              <span className="text-muted">Mostrando {desde}–{hasta} de {total}</span>
              <button
                className="btn btn-outline btn-sm"
                onClick={() => cambiarPagina(pagina + 1)}
                disabled={!haySiguiente}
              >
                Siguiente →
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

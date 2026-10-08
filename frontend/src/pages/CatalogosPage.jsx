import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import client, { LISTA_COMPLETA, resultados } from '../api/client';

// Mensaje de error de la API: `detail` o el primer error del campo `nombre`.
function mensajeDeError(err, porDefecto) {
  const datos = err.response?.data;
  const nombre = datos?.nombre;
  return { nombre: Array.isArray(nombre) ? nombre[0] : nombre, general: nombre ? '' : datos?.detail || porDefecto };
}

// Tabla de un catálogo editable (EPS o servicios). `campoActivo` es el nombre del
// campo en la API ('activa' en EPS, 'activo' en servicios).
function TablaCatalogo({ titulo, url, campoActivo, etiquetaNuevo, etiquetaActivo, etiquetaInactivo }) {
  const { canWrite } = useAuth();
  const [elementos, setElementos] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');
  const [nuevo, setNuevo] = useState('');
  const [errorNuevo, setErrorNuevo] = useState('');
  const [renombrando, setRenombrando] = useState(null); // { id, nombre, error }
  const [confirmarBorrar, setConfirmarBorrar] = useState(null); // id

  const cargar = async () => {
    try {
      const { data } = await client.get(url, { params: LISTA_COMPLETA });
      setElementos(resultados(data));
    } catch {
      setError(`No se pudo cargar la lista de ${titulo}.`);
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargar();
  }, []);

  const agregar = async (e) => {
    e.preventDefault();
    setError('');
    setErrorNuevo('');
    try {
      await client.post(url, { nombre: nuevo });
      setNuevo('');
      cargar();
    } catch (err) {
      const { nombre, general } = mensajeDeError(err, 'No se pudo agregar.');
      setErrorNuevo(nombre || '');
      setError(general);
    }
  };

  const guardarNombre = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await client.patch(`${url}${renombrando.id}/`, { nombre: renombrando.nombre });
      setRenombrando(null);
      cargar();
    } catch (err) {
      const { nombre, general } = mensajeDeError(err, 'No se pudo cambiar el nombre.');
      setRenombrando({ ...renombrando, error: nombre });
      setError(general);
    }
  };

  const cambiarActivo = async (elemento) => {
    setError('');
    try {
      await client.patch(`${url}${elemento.id}/`, { [campoActivo]: !elemento[campoActivo] });
      cargar();
    } catch (err) {
      setError(err.response?.data?.detail || 'No se pudo cambiar el estado.');
    }
  };

  const borrar = async (id) => {
    setError('');
    setConfirmarBorrar(null);
    try {
      await client.delete(`${url}${id}/`);
      cargar();
    } catch (err) {
      // En uso por un paciente o un informe: el backend responde 400 y pide desactivarlo (D-4).
      setError(err.response?.data?.detail || 'No se pudo eliminar.');
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <h2>
          {titulo} ({elementos.length})
        </h2>
      </div>
      <div className="card-body">
        {error && <div className="alert alert-error">{error}</div>}

        {canWrite && (
          <form onSubmit={agregar} className="search-form">
            <div className="form-row">
              <div className={`form-group flex-2 ${errorNuevo ? 'has-error' : ''}`}>
                <label htmlFor={`nuevo-${campoActivo}`}>{etiquetaNuevo}</label>
                <input
                  id={`nuevo-${campoActivo}`}
                  value={nuevo}
                  onChange={(e) => setNuevo(e.target.value)}
                  maxLength={150}
                  required
                />
                {errorNuevo && <span className="field-error">{errorNuevo}</span>}
              </div>
            </div>
            <button type="submit" className="btn btn-primary btn-sm">
              Agregar
            </button>
          </form>
        )}

        {cargando ? (
          <div className="loading-center">
            <span className="spinner"></span>
          </div>
        ) : (
          <div className="table-responsive">
            <table>
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>Estado</th>
                  {canWrite && <th>Acciones</th>}
                </tr>
              </thead>
              <tbody>
                {elementos.map((el) => (
                  <tr key={el.id}>
                    <td>
                      {renombrando?.id === el.id ? (
                        <form onSubmit={guardarNombre} className="table-actions">
                          <input
                            aria-label={`Nombre de ${el.nombre}`}
                            value={renombrando.nombre}
                            onChange={(e) => setRenombrando({ ...renombrando, nombre: e.target.value })}
                            maxLength={150}
                            required
                          />
                          <button type="submit" className="btn btn-primary btn-xs">
                            Guardar
                          </button>
                          <button type="button" className="btn btn-outline btn-xs" onClick={() => setRenombrando(null)}>
                            Cancelar
                          </button>
                          {renombrando.error && <span className="field-error">{renombrando.error}</span>}
                        </form>
                      ) : (
                        el.nombre
                      )}
                    </td>
                    <td>
                      <span className={`badge ${el[campoActivo] ? 'badge-success' : 'badge-warning'}`}>
                        {el[campoActivo] ? etiquetaActivo : etiquetaInactivo}
                      </span>
                    </td>
                    {canWrite && (
                      <td>
                        <div className="table-actions">
                          <button
                            className="btn btn-outline btn-xs"
                            aria-label={`Renombrar ${el.nombre}`}
                            onClick={() => setRenombrando({ id: el.id, nombre: el.nombre })}
                          >
                            Renombrar
                          </button>
                          <button
                            className="btn btn-outline btn-xs"
                            aria-label={`${el[campoActivo] ? 'Desactivar' : 'Activar'} ${el.nombre}`}
                            onClick={() => cambiarActivo(el)}
                          >
                            {el[campoActivo] ? 'Desactivar' : 'Activar'}
                          </button>
                          {confirmarBorrar === el.id ? (
                            <>
                              <button className="btn btn-danger btn-xs" onClick={() => borrar(el.id)}>
                                Confirmar
                              </button>
                              <button className="btn btn-outline btn-xs" onClick={() => setConfirmarBorrar(null)}>
                                No
                              </button>
                            </>
                          ) : (
                            <button
                              className="btn btn-danger-outline btn-xs"
                              aria-label={`Eliminar ${el.nombre}`}
                              onClick={() => setConfirmarBorrar(el.id)}
                            >
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
      </div>
    </div>
  );
}

// Catálogos de EPS y servicios (informe v2, etapa 4). Todos leen; patólogo y admin
// los administran (decisión D-11). Lo que ya no se usa se desactiva en lugar de
// borrarse (D-4): una EPS o un servicio en uso no se puede borrar.
export default function CatalogosPage() {
  return (
    <div className="catalogos-page">
      <div className="page-header">
        <div>
          <h1>Catálogos</h1>
          <p className="text-muted">
            EPS y servicios que se eligen en pacientes e informes. Lo que ya no se use se desactiva en lugar de
            borrarse.
          </p>
        </div>
      </div>
      <TablaCatalogo
        titulo="EPS"
        url="/pacientes/eps/"
        campoActivo="activa"
        etiquetaNuevo="Nueva EPS"
        etiquetaActivo="Activa"
        etiquetaInactivo="Inactiva"
      />
      <TablaCatalogo
        titulo="Servicios"
        url="/servicios/"
        campoActivo="activo"
        etiquetaNuevo="Nuevo servicio"
        etiquetaActivo="Activo"
        etiquetaInactivo="Inactivo"
      />
    </div>
  );
}

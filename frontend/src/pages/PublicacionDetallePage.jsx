import { useCallback, useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import client from '../api/client';
import VisorImagenes from '../components/VisorImagenes';

export default function PublicacionDetallePage() {
  const { id } = useParams();
  const { user, canWrite } = useAuth();
  const navigate = useNavigate();
  const [publicacion, setPublicacion] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [comentario, setComentario] = useState('');
  const [enviando, setEnviando] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const fetchPublicacion = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await client.get(`/foro/publicaciones/${id}/`);
      setPublicacion(data);
    } catch {
      setError('No se pudo cargar la publicación.');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchPublicacion();
  }, [fetchPublicacion]);

  const enviarComentario = async (e) => {
    e.preventDefault();
    if (!comentario.trim()) return;
    setEnviando(true);
    try {
      await client.post('/foro/comentarios/', { publicacion: id, contenido: comentario });
      setComentario('');
      fetchPublicacion();
    } catch (err) {
      setError(err.response?.data?.contenido?.[0] || 'No se pudo enviar el comentario.');
    } finally {
      setEnviando(false);
    }
  };

  const eliminarPublicacion = async () => {
    try {
      await client.delete(`/foro/publicaciones/${id}/`);
      navigate('/foro');
    } catch {
      setError('No se pudo eliminar la publicación.');
    }
  };

  const puedeModerar = (autorId) => user?.rol === 'admin' || user?.id === autorId;

  if (loading)
    return (
      <div className="loading-center">
        <span className="spinner"></span>
      </div>
    );
  if (!publicacion) return <div className="alert alert-error">{error || 'Publicación no encontrada.'}</div>;

  return (
    <div className="publicacion-detalle">
      <Link to="/foro" className="text-muted">
        ← Volver al foro
      </Link>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="card">
        <div className="card-body">
          <div className="foro-post-meta">
            {publicacion.fijado && <span className="badge badge-info">Fijado</span>}
            {publicacion.tema_nombre && <span className="badge">{publicacion.tema_nombre}</span>}
          </div>
          <h1>{publicacion.titulo}</h1>
          <p className="text-muted">
            {publicacion.autor_nombre} · {new Date(publicacion.fecha_creacion).toLocaleString('es-CO')}
          </p>
          <p className="publicacion-contenido">{publicacion.contenido}</p>

          {/* Miniaturas que se amplían al hacer clic (Pendientes, punto 2). */}
          <VisorImagenes imagenes={publicacion.imagenes || []} />

          {puedeModerar(publicacion.autor) && (
            <div className="form-actions">
              {confirmDelete ? (
                <>
                  <span className="text-muted">¿Seguro?</span>
                  <button className="btn btn-outline btn-sm" onClick={() => setConfirmDelete(false)}>
                    No
                  </button>
                  <button className="btn btn-danger btn-sm" onClick={eliminarPublicacion}>
                    Sí, eliminar
                  </button>
                </>
              ) : (
                <button className="btn btn-danger-outline btn-sm" onClick={() => setConfirmDelete(true)}>
                  Eliminar publicación
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h2>Comentarios ({publicacion.comentarios?.length || 0})</h2>
        </div>
        <div className="card-body">
          {/* El auditor solo lee: la API le rechaza los comentarios (auditoría M-7). */}
          {canWrite && (
            <form onSubmit={enviarComentario} className="comentario-form">
              <textarea
                value={comentario}
                onChange={(e) => setComentario(e.target.value)}
                placeholder="Escribe una observación o comentario…"
                rows={3}
                maxLength={3000}
              />
              <button type="submit" className="btn btn-primary btn-sm" disabled={enviando || !comentario.trim()}>
                {enviando ? <span className="spinner"></span> : 'Comentar'}
              </button>
            </form>
          )}

          {publicacion.comentarios?.length > 0 ? (
            <ul className="comentario-list">
              {publicacion.comentarios.map((c) => (
                <li key={c.id}>
                  <strong>{c.autor_nombre}</strong>
                  <span className="text-muted"> · {new Date(c.fecha_creacion).toLocaleString('es-CO')}</span>
                  <p>{c.contenido}</p>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-muted">Sé el primero en comentar.</p>
          )}
        </div>
      </div>
    </div>
  );
}

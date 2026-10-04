import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import client, { LISTA_COMPLETA, resultados } from '../api/client';

// Debe coincidir con FORO_MAX_TAMANO_IMAGEN de backend/config/settings.py.
const MAX_TAMANO_IMAGEN_MB = 10;

// Revisa las imágenes antes de publicar (auditoría I-6). La validación de verdad
// la hace el backend; esto evita crear la publicación si una imagen será rechazada.
function errorEnImagenes(archivos) {
  for (const archivo of archivos) {
    if (!archivo.type.startsWith('image/')) {
      return `«${archivo.name}» no es una imagen.`;
    }
    if (archivo.size > MAX_TAMANO_IMAGEN_MB * 1024 * 1024) {
      return `«${archivo.name}» supera el tamaño máximo de ${MAX_TAMANO_IMAGEN_MB} MB.`;
    }
  }
  return '';
}

export default function ForoPage() {
  const { canWrite } = useAuth();
  const [publicaciones, setPublicaciones] = useState([]);
  const [temas, setTemas] = useState([]);
  const [filtroTema, setFiltroTema] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [mostrarForm, setMostrarForm] = useState(false);
  const [nuevo, setNuevo] = useState({ titulo: '', contenido: '', tema: '' });
  const [archivos, setArchivos] = useState([]);
  const [guardando, setGuardando] = useState(false);
  // Errores del formulario: se muestran dentro del modal, no detrás de él.
  const [errorFormulario, setErrorFormulario] = useState('');

  const fetchData = async () => {
    setLoading(true);
    try {
      const [pubRes, temaRes] = await Promise.all([
        client.get('/foro/publicaciones/', { params: filtroTema ? { tema: filtroTema } : {} }),
        client.get('/foro/temas/', { params: LISTA_COMPLETA }),
      ]);
      setPublicaciones(resultados(pubRes.data));
      setTemas(resultados(temaRes.data));
    } catch (err) {
      setError('No se pudo cargar el foro.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [filtroTema]);

  const crearPublicacion = async (e) => {
    e.preventDefault();
    setError('');
    setErrorFormulario('');

    const errorImagenes = errorEnImagenes(archivos);
    if (errorImagenes) {
      setErrorFormulario(errorImagenes);
      return;
    }

    setGuardando(true);
    let publicacionCreada = false;
    try {
      const { data } = await client.post('/foro/publicaciones/', {
        titulo: nuevo.titulo,
        contenido: nuevo.contenido,
        tema: nuevo.tema || null,
      });
      publicacionCreada = true;
      if (archivos.length > 0) {
        const form = new FormData();
        archivos.forEach((f) => form.append('imagenes', f));
        await client.post(`/foro/publicaciones/${data.id}/imagenes/`, form, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
      }
      cerrarFormulario();
      fetchData();
    } catch (err) {
      const detalle = err.response?.data?.titulo?.[0] ||
        err.response?.data?.contenido?.[0] ||
        err.response?.data?.detail;
      if (publicacionCreada) {
        // La publicación ya existe: se cierra el formulario para que reintentar
        // no cree una publicación duplicada.
        cerrarFormulario();
        fetchData();
        setError(`La publicación se creó, pero las imágenes no se pudieron subir. ${detalle || ''}`.trim());
      } else {
        setErrorFormulario(detalle || 'No se pudo publicar. Intenta de nuevo.');
      }
    } finally {
      setGuardando(false);
    }
  };

  const cerrarFormulario = () => {
    setMostrarForm(false);
    setNuevo({ titulo: '', contenido: '', tema: '' });
    setArchivos([]);
    setErrorFormulario('');
  };

  return (
    <div className="foro-page">
      <div className="page-header">
        <div>
          <h1>Foro de Patólogos</h1>
          <p className="text-muted">Comparte investigaciones, observaciones y casos con tus colegas</p>
        </div>
        {canWrite && (
          <button className="btn btn-primary" onClick={() => { setErrorFormulario(''); setMostrarForm(true); }}>
            + Nueva publicación
          </button>
        )}
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="categoria-chip-list">
        <button
          className={`categoria-chip ${filtroTema === '' ? 'categoria-chip-activo' : ''}`}
          onClick={() => setFiltroTema('')}
        >
          Todos los temas
        </button>
        {temas.map((t) => (
          <button
            key={t.id}
            className={`categoria-chip ${filtroTema === String(t.id) ? 'categoria-chip-activo' : ''}`}
            onClick={() => setFiltroTema(String(t.id))}
          >
            {t.nombre}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="loading-center"><span className="spinner"></span></div>
      ) : publicaciones.length === 0 ? (
        <div className="empty-state"><p>Aún no hay publicaciones en el foro.</p></div>
      ) : (
        <div className="foro-feed">
          {publicaciones.map((p) => (
            <Link to={`/foro/${p.id}`} key={p.id} className="foro-post-card">
              {p.portada && <img src={p.portada} alt="" className="foro-post-thumb" />}
              <div className="foro-post-body">
                <div className="foro-post-meta">
                  {p.fijado && <span className="badge badge-info">Fijado</span>}
                  {p.tema_nombre && <span className="badge">{p.tema_nombre}</span>}
                </div>
                <h3>{p.titulo}</h3>
                <p className="text-muted">
                  {p.autor_nombre} · {new Date(p.fecha_creacion).toLocaleDateString('es-CO')}
                </p>
                <div className="foro-post-stats">
                  <span>💬 {p.total_comentarios}</span>
                  {p.total_imagenes > 0 && <span>🖼 {p.total_imagenes}</span>}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}

      {mostrarForm && (
        <div className="modal-overlay" onClick={() => setMostrarForm(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <h2>Nueva publicación</h2>
            {errorFormulario && <div className="alert alert-error">{errorFormulario}</div>}
            <form onSubmit={crearPublicacion}>
              <div className="form-group">
                <label>Tema</label>
                <select value={nuevo.tema} onChange={(e) => setNuevo({ ...nuevo, tema: e.target.value })}>
                  <option value="">Sin tema</option>
                  {temas.map((t) => <option key={t.id} value={t.id}>{t.nombre}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Título</label>
                <input
                  value={nuevo.titulo}
                  onChange={(e) => setNuevo({ ...nuevo, titulo: e.target.value })}
                  required
                  maxLength={250}
                />
              </div>
              <div className="form-group">
                <label>Contenido</label>
                <textarea
                  value={nuevo.contenido}
                  onChange={(e) => setNuevo({ ...nuevo, contenido: e.target.value })}
                  rows={6}
                  required
                />
              </div>
              <div className="form-group">
                <label>Imágenes (opcional, máx. 6)</label>
                <input
                  type="file"
                  accept="image/*"
                  multiple
                  onChange={(e) => setArchivos(Array.from(e.target.files).slice(0, 6))}
                />
              </div>
              <div className="form-actions">
                <button type="button" className="btn btn-outline" onClick={() => setMostrarForm(false)}>Cancelar</button>
                <button type="submit" className="btn btn-primary" disabled={guardando}>
                  {guardando ? <span className="spinner"></span> : 'Publicar'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

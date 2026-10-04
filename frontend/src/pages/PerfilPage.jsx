import { useState, useEffect } from 'react';
import client from '../api/client';
import { ROL_LABELS } from '../constants';


export default function PerfilPage() {
  const [perfil, setPerfil] = useState(null);
  const [loading, setLoading] = useState(true);
  const [guardando, setGuardando] = useState(false);
  const [mensaje, setMensaje] = useState('');
  const [error, setError] = useState('');

  const [passwords, setPasswords] = useState({ old_password: '', new_password: '', confirmar: '' });
  const [passwordMsg, setPasswordMsg] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [cambiandoPassword, setCambiandoPassword] = useState(false);
  const [errorCarga, setErrorCarga] = useState('');

  // Si la carga falla, se muestra un mensaje con "Reintentar" en lugar de
  // dibujar el formulario con perfil = null (auditoría M-8).
  const cargarPerfil = () => {
    setLoading(true);
    setErrorCarga('');
    client.get('/auth/perfil/')
      .then(({ data }) => setPerfil(data))
      .catch(() => setErrorCarga('No se pudo cargar tu perfil. Intenta de nuevo.'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { cargarPerfil(); }, []);

  const guardarPerfil = async (e) => {
    e.preventDefault();
    setGuardando(true);
    setMensaje('');
    setError('');
    try {
      const { data } = await client.patch('/auth/perfil/', {
        nombre_completo: perfil.nombre_completo,
        email: perfil.email,
        telefono: perfil.telefono,
        especialidad: perfil.especialidad,
      });
      setPerfil(data);
      const savedUser = JSON.parse(localStorage.getItem('user_data') || '{}');
      localStorage.setItem('user_data', JSON.stringify({ ...savedUser, ...data }));
      setMensaje('Perfil actualizado correctamente.');
    } catch (err) {
      setError(err.response?.data?.email?.[0] || 'No se pudo actualizar el perfil.');
    } finally {
      setGuardando(false);
    }
  };

  const cambiarPassword = async (e) => {
    e.preventDefault();
    setPasswordMsg('');
    setPasswordError('');
    if (passwords.new_password !== passwords.confirmar) {
      setPasswordError('Las contraseñas nuevas no coinciden.');
      return;
    }
    setCambiandoPassword(true);
    try {
      await client.post('/auth/cambiar-password/', {
        old_password: passwords.old_password,
        new_password: passwords.new_password,
      });
      setPasswordMsg('Contraseña actualizada correctamente.');
      setPasswords({ old_password: '', new_password: '', confirmar: '' });
    } catch (err) {
      setPasswordError(
        err.response?.data?.old_password?.[0] ||
        err.response?.data?.new_password?.[0] ||
        'No se pudo cambiar la contraseña.'
      );
    } finally {
      setCambiandoPassword(false);
    }
  };

  if (loading) return <div className="loading-center"><span className="spinner"></span></div>;

  if (!perfil) {
    return (
      <div className="perfil-page">
        <div className="alert alert-error">{errorCarga || 'No se pudo cargar tu perfil. Intenta de nuevo.'}</div>
        <button className="btn btn-primary" onClick={cargarPerfil}>Reintentar</button>
      </div>
    );
  }

  return (
    <div className="perfil-page">
      <div className="page-header">
        <div>
          <h1>Mi cuenta</h1>
          <p className="text-muted">{ROL_LABELS[perfil?.rol] || perfil?.rol} · @{perfil?.username}</p>
        </div>
      </div>

      <div className="card">
        <div className="card-header"><h2>Información personal</h2></div>
        <div className="card-body">
          {mensaje && <div className="alert alert-success">{mensaje}</div>}
          {error && <div className="alert alert-error">{error}</div>}
          <form onSubmit={guardarPerfil}>
            <div className="form-row">
              <div className="form-group">
                <label>Nombre completo</label>
                <input
                  value={perfil.nombre_completo || ''}
                  onChange={(e) => setPerfil({ ...perfil, nombre_completo: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Correo electrónico</label>
                <input
                  type="email"
                  value={perfil.email || ''}
                  onChange={(e) => setPerfil({ ...perfil, email: e.target.value })}
                />
              </div>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>Teléfono</label>
                <input
                  value={perfil.telefono || ''}
                  onChange={(e) => setPerfil({ ...perfil, telefono: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Especialidad</label>
                <input
                  value={perfil.especialidad || ''}
                  onChange={(e) => setPerfil({ ...perfil, especialidad: e.target.value })}
                />
              </div>
            </div>
            <div className="form-actions">
              <button type="submit" className="btn btn-primary" disabled={guardando}>
                {guardando ? <span className="spinner"></span> : 'Guardar cambios'}
              </button>
            </div>
          </form>
        </div>
      </div>

      <div className="card">
        <div className="card-header"><h2>Cambiar contraseña</h2></div>
        <div className="card-body">
          {passwordMsg && <div className="alert alert-success">{passwordMsg}</div>}
          {passwordError && <div className="alert alert-error">{passwordError}</div>}
          <form onSubmit={cambiarPassword}>
            <div className="form-group">
              <label>Contraseña actual</label>
              <input
                type="password"
                value={passwords.old_password}
                onChange={(e) => setPasswords({ ...passwords, old_password: e.target.value })}
                required
              />
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>Nueva contraseña</label>
                <input
                  type="password"
                  value={passwords.new_password}
                  onChange={(e) => setPasswords({ ...passwords, new_password: e.target.value })}
                  minLength={8}
                  required
                />
              </div>
              <div className="form-group">
                <label>Confirmar nueva contraseña</label>
                <input
                  type="password"
                  value={passwords.confirmar}
                  onChange={(e) => setPasswords({ ...passwords, confirmar: e.target.value })}
                  minLength={8}
                  required
                />
              </div>
            </div>
            <div className="form-actions">
              <button type="submit" className="btn btn-primary" disabled={cambiandoPassword}>
                {cambiandoPassword ? <span className="spinner"></span> : 'Actualizar contraseña'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

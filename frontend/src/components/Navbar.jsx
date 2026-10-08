import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ROL_LABELS } from '../constants';

export default function Navbar() {
  const { user, canWrite } = useAuth();
  const navigate = useNavigate();

  // La sesión se cierra en /salir (D-13): si hay un informe con cambios sin guardar,
  // su aviso aparece antes, con la sesión todavía abierta.
  const handleLogout = () => navigate('/salir');

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" width="28" height="28">
          <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
        </svg>
        <span>PathoLab</span>
      </div>

      <div className="navbar-links">
        <NavLink to="/" end>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
            <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
            <polyline points="9,22 9,12 15,12 15,22" />
          </svg>
          Inicio
        </NavLink>
        {canWrite && (
          <NavLink to="/informes/nuevo">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            Nuevo Informe
          </NavLink>
        )}
        <NavLink to="/buscar">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          Buscar
        </NavLink>
        <NavLink to="/pacientes">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
            <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
          Pacientes
        </NavLink>
        <NavLink to="/patologias">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
            <rect x="3" y="3" width="7" height="7" />
            <rect x="14" y="3" width="7" height="7" />
            <rect x="14" y="14" width="7" height="7" />
            <rect x="3" y="14" width="7" height="7" />
          </svg>
          Patologías
        </NavLink>
        <NavLink to="/catalogos">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
            <line x1="8" y1="6" x2="21" y2="6" />
            <line x1="8" y1="12" x2="21" y2="12" />
            <line x1="8" y1="18" x2="21" y2="18" />
            <line x1="3" y1="6" x2="3.01" y2="6" />
            <line x1="3" y1="12" x2="3.01" y2="12" />
            <line x1="3" y1="18" x2="3.01" y2="18" />
          </svg>
          Catálogos
        </NavLink>
        <NavLink to="/foro">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
            <path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z" />
          </svg>
          Foro
        </NavLink>
      </div>

      <div className="navbar-user">
        <NavLink to="/perfil" className="user-info" style={{ textDecoration: 'none' }}>
          <span className="user-name">{user?.nombre_completo || user?.username}</span>
          <span className="user-role">{ROL_LABELS[user?.rol] || user?.rol}</span>
        </NavLink>
        <button className="btn btn-outline btn-sm" onClick={handleLogout}>
          Salir
        </button>
      </div>
    </nav>
  );
}

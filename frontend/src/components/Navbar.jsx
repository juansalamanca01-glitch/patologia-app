import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const ROL_LABELS = { admin: 'Administrador', patologo: 'Patólogo', auditor: 'Auditor' };

export default function Navbar() {
  const { user, logout, canWrite } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" width="28" height="28">
          <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
        </svg>
        <span>PathoLab</span>
      </div>

      <div className="navbar-links">
        <NavLink to="/" end>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
            <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>
            <polyline points="9,22 9,12 15,12 15,22"/>
          </svg>
          Inicio
        </NavLink>
        {canWrite && (
          <NavLink to="/informes/nuevo">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
              <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            Nuevo Informe
          </NavLink>
        )}
        <NavLink to="/buscar">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          Buscar
        </NavLink>
      </div>

      <div className="navbar-user">
        <div className="user-info">
          <span className="user-name">{user?.nombre_completo || user?.username}</span>
          <span className="user-role">{ROL_LABELS[user?.rol] || user?.rol}</span>
        </div>
        <button className="btn btn-outline btn-sm" onClick={handleLogout}>
          Salir
        </button>
      </div>
    </nav>
  );
}

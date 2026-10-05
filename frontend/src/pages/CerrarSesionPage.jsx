import { useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

// Ruta /salir: aquí se cierra la sesión (decisión D-13). El botón "Salir" solo navega
// hasta aquí; así, si hay un informe con cambios sin guardar, su aviso aparece antes,
// mientras la sesión sigue abierta y "Guardar y salir" todavía puede guardar.
export default function CerrarSesionPage() {
  const { user, logout } = useAuth();

  useEffect(() => {
    logout();
  }, []);

  if (user) {
    return (
      <div className="loading-center">
        <h1 className="cerrando-sesion">Cerrando sesión</h1>
        <span className="spinner"></span>
      </div>
    );
  }
  return <Navigate to="/login" replace />;
}

import { useState } from 'react';
import { createBrowserRouter, createRoutesFromElements, RouterProvider, Route, Navigate, Link } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import InformePage from './pages/InformePage';
import BuscarPage from './pages/BuscarPage';
import PatologiasPage from './pages/PatologiasPage';
import PacientesPage from './pages/PacientesPage';
import CatalogosPage from './pages/CatalogosPage';
import ForoPage from './pages/ForoPage';
import PublicacionDetallePage from './pages/PublicacionDetallePage';
import PerfilPage from './pages/PerfilPage';
import PoliticaPrivacidadPage from './pages/PoliticaPrivacidadPage';
import TerminosCondicionesPage from './pages/TerminosCondicionesPage';
import CerrarSesionPage from './pages/CerrarSesionPage';

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading)
    return (
      <div className="loading-center">
        <span className="spinner"></span>
      </div>
    );
  if (!user) return <Navigate to="/login" replace />;
  return (
    <>
      <Navbar />
      <main className="main-content">{children}</main>
      <Footer />
    </>
  );
}

function PublicRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (user) return <Navigate to="/" replace />;
  return children;
}

// Las páginas legales son visibles tanto autenticado como sin autenticar.
// Sin sesión no hay Navbar: se ofrece volver al login y el pie con los enlaces legales.
function LegalRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) {
    return (
      <>
        <main className="main-content">
          <p className="legal-volver">
            <Link to="/login">← Volver al inicio de sesión</Link>
          </p>
          {children}
        </main>
        <Footer />
      </>
    );
  }
  return (
    <>
      <Navbar />
      <main className="main-content">{children}</main>
      <Footer />
    </>
  );
}

// Router de datos (createBrowserRouter): lo necesita useBlocker, con el que el informe
// avisa antes de salir si hay cambios sin guardar (decisión D-13).
const rutas = createRoutesFromElements(
  <>
    <Route
      path="/login"
      element={
        <PublicRoute>
          <LoginPage />
        </PublicRoute>
      }
    />
    <Route path="/salir" element={<CerrarSesionPage />} />
    <Route
      path="/"
      element={
        <ProtectedRoute>
          <DashboardPage />
        </ProtectedRoute>
      }
    />
    <Route
      path="/informes/nuevo"
      element={
        <ProtectedRoute>
          <InformePage />
        </ProtectedRoute>
      }
    />
    <Route
      path="/informes/:id"
      element={
        <ProtectedRoute>
          <InformePage />
        </ProtectedRoute>
      }
    />
    <Route
      path="/buscar"
      element={
        <ProtectedRoute>
          <BuscarPage />
        </ProtectedRoute>
      }
    />
    <Route
      path="/patologias"
      element={
        <ProtectedRoute>
          <PatologiasPage />
        </ProtectedRoute>
      }
    />
    <Route
      path="/pacientes"
      element={
        <ProtectedRoute>
          <PacientesPage />
        </ProtectedRoute>
      }
    />
    <Route
      path="/catalogos"
      element={
        <ProtectedRoute>
          <CatalogosPage />
        </ProtectedRoute>
      }
    />
    <Route
      path="/foro"
      element={
        <ProtectedRoute>
          <ForoPage />
        </ProtectedRoute>
      }
    />
    <Route
      path="/foro/:id"
      element={
        <ProtectedRoute>
          <PublicacionDetallePage />
        </ProtectedRoute>
      }
    />
    <Route
      path="/perfil"
      element={
        <ProtectedRoute>
          <PerfilPage />
        </ProtectedRoute>
      }
    />
    <Route
      path="/politica-privacidad"
      element={
        <LegalRoute>
          <PoliticaPrivacidadPage />
        </LegalRoute>
      }
    />
    <Route
      path="/terminos-condiciones"
      element={
        <LegalRoute>
          <TerminosCondicionesPage />
        </LegalRoute>
      }
    />
    <Route path="*" element={<Navigate to="/" replace />} />
  </>,
);

export default function App() {
  // Se crea al montar la app (y no al importar el módulo), para que lea la dirección actual.
  const [router] = useState(() => createBrowserRouter(rutas));
  return (
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  );
}

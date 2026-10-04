import { Link } from 'react-router-dom';

export default function Footer() {
  return (
    <footer className="app-footer">
      <span>© {new Date().getFullYear()} PathoLab</span>
      <Link to="/politica-privacidad">Política de Privacidad</Link>
      <Link to="/terminos-condiciones">Términos y Condiciones</Link>
    </footer>
  );
}

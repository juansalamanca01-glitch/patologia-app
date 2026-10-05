// Ayudantes compartidos por los formularios (pacientes e informes).

// Fecha local de hoy en formato AAAA-MM-DD, para los campos de fecha: el calendario
// no ofrece fechas futuras y un informe nuevo empieza con la fecha de hoy.
export const hoyISO = () => new Date().toLocaleDateString('en-CA');

// Opciones de un catálogo (EPS, servicios): las activas y, si el registro ya tenía
// uno que se desactivó, también ese, marcado como desactivado. Así lo conserva al
// guardar (decisión D-4).
export function conOpcionActual(activas, id, nombre, desactivada = 'desactivada') {
  if (!id || activas.some((o) => o.id === Number(id))) return activas;
  return [{ id: Number(id), nombre: `${nombre ?? 'Actual'} (${desactivada})` }, ...activas];
}

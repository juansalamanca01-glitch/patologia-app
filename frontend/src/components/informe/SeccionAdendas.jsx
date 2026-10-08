import { useState } from 'react';
import client from '../../api/client';
import { LineasFirma, formatoFechaHora } from './SeccionFirma';

// Tarjeta "Adendas" del informe (informe v2, etapa 8; decisión D-9). Solo en informes
// finalizados: un borrador se corrige editándolo. Las adendas no se editan ni se
// borran, así que antes de guardar se pide confirmación. Se envían con su propia
// petición (POST /informes/{id}/adendas/), no con el formulario del informe; por eso
// InformePage dibuja esta tarjeta fuera de su <form>.

const vacia = { motivo: '', texto: '' };

export default function SeccionAdendas({ informeId, estado, adendas = [], puedeAgregar, onAgregada }) {
  const [abierto, setAbierto] = useState(false);
  const [valores, setValores] = useState(vacia);
  const [confirmar, setConfirmar] = useState(false);
  const [guardando, setGuardando] = useState(false);
  const [errores, setErrores] = useState({});
  const [exito, setExito] = useState('');

  if (estado !== 'finalizado' || (adendas.length === 0 && !puedeAgregar)) return null;

  const cambiar = (campo, valor) => {
    setValores((prev) => ({ ...prev, [campo]: valor }));
    setErrores((prev) => ({ ...prev, [campo]: null }));
  };

  const cerrar = () => {
    setAbierto(false);
    setConfirmar(false);
    setValores(vacia);
    setErrores({});
  };

  // Primer paso: revisa lo escrito y pide confirmación.
  const revisar = (e) => {
    e.preventDefault();
    const nuevos = {};
    if (!valores.motivo.trim()) nuevos.motivo = 'Escriba el motivo de la adenda.';
    if (!valores.texto.trim()) nuevos.texto = 'Escriba el texto de la adenda.';
    setErrores(nuevos);
    if (Object.keys(nuevos).length === 0) setConfirmar(true);
  };

  const guardar = async () => {
    setConfirmar(false);
    setGuardando(true);
    try {
      const { data } = await client.post(`/informes/${informeId}/adendas/`, valores);
      onAgregada(data);
      cerrar();
      setExito('Adenda agregada correctamente.');
    } catch (err) {
      const datos = err.response?.data;
      if (datos && typeof datos === 'object') {
        const nuevos = {};
        Object.entries(datos).forEach(([campo, valor]) => {
          nuevos[campo === 'detail' ? 'general' : campo] = Array.isArray(valor) ? valor.join(' ') : valor;
        });
        setErrores(nuevos);
      } else {
        setErrores({ general: 'No se pudo guardar la adenda.' });
      }
    } finally {
      setGuardando(false);
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <h2>Adendas</h2>
        {puedeAgregar && !abierto && (
          <button
            type="button"
            className="btn btn-outline btn-sm"
            onClick={() => {
              setAbierto(true);
              setExito('');
            }}
          >
            + Agregar adenda
          </button>
        )}
      </div>
      <div className="card-body">
        {exito && <div className="alert alert-success">{exito}</div>}

        {adendas.map((adenda) => (
          <div className="adenda" key={adenda.id}>
            <h3>
              Adenda N.º {adenda.numero} — {formatoFechaHora.format(new Date(adenda.fecha))}
            </h3>
            <p>
              <strong>Motivo:</strong> <span>{adenda.motivo}</span>
            </p>
            <p className="adenda-texto">{adenda.texto}</p>
            <LineasFirma firma={adenda.firma} />
          </div>
        ))}

        {abierto && (
          <form className="adenda-formulario" onSubmit={revisar} noValidate>
            {errores.general && <div className="alert alert-error">{errores.general}</div>}
            <div className={`form-group ${errores.motivo ? 'has-error' : ''}`}>
              <label htmlFor="adendaMotivo">
                Motivo <span className="required">*</span>
              </label>
              <input
                id="adendaMotivo"
                type="text"
                maxLength={300}
                value={valores.motivo}
                onChange={(e) => cambiar('motivo', e.target.value)}
                placeholder="Ej: Resultado de inmunohistoquímica"
                disabled={confirmar || guardando}
              />
              {errores.motivo && <span className="field-error">{errores.motivo}</span>}
            </div>
            <div className={`form-group ${errores.texto ? 'has-error' : ''}`}>
              <label htmlFor="adendaTexto">
                Texto <span className="required">*</span>
              </label>
              <textarea
                id="adendaTexto"
                rows={4}
                value={valores.texto}
                onChange={(e) => cambiar('texto', e.target.value)}
                disabled={confirmar || guardando}
              />
              {errores.texto && <span className="field-error">{errores.texto}</span>}
            </div>

            {confirmar ? (
              <div className="alert alert-warning">
                <p>
                  Las adendas no se pueden modificar ni borrar. Llevarán su firma y la fecha de hoy. ¿Guardar la adenda?
                </p>
                <div className="form-actions">
                  <button type="button" className="btn btn-outline" onClick={() => setConfirmar(false)}>
                    Volver
                  </button>
                  <button type="button" className="btn btn-primary" onClick={guardar}>
                    Sí, guardar adenda
                  </button>
                </div>
              </div>
            ) : (
              <div className="form-actions">
                <button type="button" className="btn btn-outline" onClick={cerrar} disabled={guardando}>
                  Cancelar
                </button>
                <button type="submit" className="btn btn-primary" disabled={guardando}>
                  {guardando ? <span className="spinner"></span> : 'Guardar adenda'}
                </button>
              </div>
            )}
          </form>
        )}
      </div>
    </div>
  );
}

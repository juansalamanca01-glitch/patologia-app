import importlib.util
import os
from pathlib import Path
from unittest import mock

import decouple
from django.test import SimpleTestCase

RUTA_SETTINGS = Path(__file__).resolve().parent / 'settings.py'


def cargar_settings(variables_entorno):
    """
    Carga config/settings.py como un módulo nuevo, simulando que NO existe el
    archivo .env y que el entorno solo tiene las variables indicadas.
    No afecta a la configuración con la que corren las demás pruebas.
    """
    sin_env = decouple.Config(decouple.RepositoryEmpty())
    entorno = {k: v for k, v in os.environ.items() if k not in ('SECRET_KEY', 'DEBUG')}
    entorno.update(variables_entorno)
    with mock.patch.object(decouple, 'config', sin_env), mock.patch.dict(os.environ, entorno, clear=True):
        spec = importlib.util.spec_from_file_location('settings_prueba', RUTA_SETTINGS)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
    return modulo


class ValoresPorDefectoSegurosTests(SimpleTestCase):
    """
    Hallazgo C-3 de docs/auditoria-inicial.md: si falta el .env, la app no debe
    arrancar con DEBUG=True ni con una SECRET_KEY escrita en el código.
    """

    def test_sin_secret_key_la_app_no_arranca(self):
        with self.assertRaises(Exception) as contexto:
            cargar_settings({})
        self.assertIn('SECRET_KEY', str(contexto.exception))

    def test_debug_es_false_si_no_se_define(self):
        settings = cargar_settings({'SECRET_KEY': 'clave-de-prueba-solo-para-tests'})
        self.assertFalse(settings.DEBUG)

    def test_sin_debug_no_se_permite_cors_desde_cualquier_origen(self):
        settings = cargar_settings({'SECRET_KEY': 'clave-de-prueba-solo-para-tests'})
        self.assertFalse(settings.CORS_ALLOW_ALL_ORIGINS)

    def test_usa_la_secret_key_del_entorno(self):
        # Control: si la variable existe, se usa tal cual.
        settings = cargar_settings({'SECRET_KEY': 'clave-de-prueba-solo-para-tests', 'DEBUG': 'True'})
        self.assertEqual(settings.SECRET_KEY, 'clave-de-prueba-solo-para-tests')
        self.assertTrue(settings.DEBUG)


class EncabezadoLaboratorioTests(SimpleTestCase):
    """
    Tarea previa 2 de docs/plan-calidad-y-diseno.md: el encabezado del PDF se lee
    de backend/.env (LABORATORIO_NOMBRE, LABORATORIO_DIRECCION, LABORATORIO_TELEFONO).
    Sin esas variables queda el encabezado de demostración de siempre (P-9).
    """

    CLAVE = {'SECRET_KEY': 'clave-de-prueba-solo-para-tests'}

    def test_sin_variables_usa_el_encabezado_de_demostracion(self):
        settings = cargar_settings(self.CLAVE)
        self.assertEqual(settings.LABORATORIO_NOMBRE, 'PathoLab — Laboratorio de Patología (demostración)')
        self.assertEqual(settings.LABORATORIO_DIRECCION, 'Santiago de Cali, Colombia')
        self.assertEqual(settings.LABORATORIO_TELEFONO, '')

    def test_usa_las_variables_definidas(self):
        settings = cargar_settings(
            {
                **self.CLAVE,
                'LABORATORIO_NOMBRE': 'Laboratorio Ficticio de Prueba',
                'LABORATORIO_DIRECCION': 'Calle Falsa 123, Ciudad Ficticia',
                'LABORATORIO_TELEFONO': '000 000 0000',
            }
        )
        self.assertEqual(settings.LABORATORIO_NOMBRE, 'Laboratorio Ficticio de Prueba')
        self.assertEqual(settings.LABORATORIO_DIRECCION, 'Calle Falsa 123, Ciudad Ficticia')
        self.assertEqual(settings.LABORATORIO_TELEFONO, '000 000 0000')

    def test_lee_tildes_y_raya_del_archivo_env(self):
        # El .env se escribe a mano: las tildes y la raya (—) deben llegar intactas al PDF.
        import tempfile

        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / '.env'
            ruta.write_text(
                'SECRET_KEY=clave-de-prueba-solo-para-tests\n'
                'LABORATORIO_NOMBRE=Laboratorio Ficticio — Anatomía Patológica\n'
                'LABORATORIO_DIRECCION=Carrera Ficticia 1 # 2-3, Bogotá\n',
                encoding='utf-8',
            )
            desde_archivo = decouple.Config(decouple.RepositoryEnv(str(ruta)))
            entorno = {k: v for k, v in os.environ.items() if not k.startswith('LABORATORIO_')}
            with mock.patch.object(decouple, 'config', desde_archivo), mock.patch.dict(os.environ, entorno, clear=True):
                spec = importlib.util.spec_from_file_location('settings_prueba_env', RUTA_SETTINGS)
                settings = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(settings)
        self.assertEqual(settings.LABORATORIO_NOMBRE, 'Laboratorio Ficticio — Anatomía Patológica')
        self.assertEqual(settings.LABORATORIO_DIRECCION, 'Carrera Ficticia 1 # 2-3, Bogotá')

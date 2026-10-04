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

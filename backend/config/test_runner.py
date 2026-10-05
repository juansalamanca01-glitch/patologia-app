"""
Ejecutor de las pruebas (TEST_RUNNER en settings.py).

Los límites de peticiones (throttles de DRF) guardan su cuenta en la caché, que
no se limpia entre pruebas. Con SQLite, los ids de usuario se repiten de una
prueba a otra, así que todas las peticiones de un minuto se sumaban al mismo
usuario y las pruebas fallaban con 429 según cuántas hubiera. Durante las
pruebas se usa una caché que no guarda nada (DummyCache): los límites no cuentan.
"""
from django.test.runner import DiscoverRunner
from django.test.utils import override_settings


class PathoLabTestRunner(DiscoverRunner):
    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        self._sin_cache = override_settings(
            CACHES={'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}},
        )
        self._sin_cache.enable()

    def teardown_test_environment(self, **kwargs):
        self._sin_cache.disable()
        super().teardown_test_environment(**kwargs)

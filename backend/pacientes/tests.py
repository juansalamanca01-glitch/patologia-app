from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Usuario


class CatalogoEPSTests(APITestCase):
    """
    Informe v2, etapa 2 (docs/propuesta-informe-v2.md, sección 3.1): catálogo de
    EPS. Lo administran patólogos y admin (decisión D-11); el auditor solo lee.
    Se desactiva en lugar de borrarse (D-4) y se filtra con ?activa=.
    """

    URL = '/api/pacientes/eps/'

    def setUp(self):
        self.patologo = Usuario.objects.create_user(username='eps_pat', password='x', rol=Usuario.Rol.PATOLOGO)
        self.auditor = Usuario.objects.create_user(username='eps_aud', password='x', rol=Usuario.Rol.AUDITOR)

    def crear(self, nombre, usuario=None, **extra):
        self.client.force_authenticate(usuario or self.patologo)
        return self.client.post(self.URL, {'nombre': nombre, **extra}, format='json')

    def nombres(self, **params):
        return [e['nombre'] for e in self.client.get(self.URL, params).data['results']]

    def test_patologo_crea_y_auditor_lee(self):
        self.assertEqual(self.crear('Particular').status_code, status.HTTP_201_CREATED)
        self.client.force_authenticate(self.auditor)
        self.assertEqual(self.nombres(), ['Particular'])

    def test_auditor_no_crea(self):
        self.assertEqual(self.crear('Particular', usuario=self.auditor).status_code, status.HTTP_403_FORBIDDEN)

    def test_filtro_activa(self):
        self.crear('Particular')
        self.crear('EPS Liquidada', activa=False)
        self.assertEqual(self.nombres(activa='true'), ['Particular'])
        self.assertEqual(self.nombres(activa='false'), ['EPS Liquidada'])
        self.assertEqual(self.nombres(), ['EPS Liquidada', 'Particular'])

    def test_se_puede_desactivar(self):
        eps_id = self.crear('Particular').data['id']
        respuesta = self.client.patch(f'{self.URL}{eps_id}/', {'activa': False}, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertFalse(respuesta.data['activa'])

    def test_nombre_repetido_sin_importar_mayusculas_ni_espacios(self):
        self.crear('Particular')
        respuesta = self.crear(' PARTICULAR  ')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('nombre', respuesta.data)

    def test_seed_data_carga_las_eps(self):
        # Lista corta de EPS reales más "Particular" y "Otra" (P-8).
        from io import StringIO
        from django.core.management import call_command
        call_command('seed_data', stdout=StringIO())
        call_command('seed_data', stdout=StringIO())  # dos veces: no duplica
        self.client.force_authenticate(self.auditor)
        nombres = self.nombres()
        self.assertIn('Particular', nombres)
        self.assertIn('Otra', nombres)
        self.assertEqual(len(nombres), len(set(nombres)))
        self.assertGreater(len(nombres), 2)

from rest_framework import status
from rest_framework.test import APITestCase

from .models import Usuario


class PerfilCamposProtegidosTests(APITestCase):
    """
    Hallazgo C-1 de docs/auditoria-inicial.md: un usuario no debe poder cambiar
    su propio rol, su estado "activo" ni su nombre de usuario desde /api/auth/perfil/.
    """

    url = '/api/auth/perfil/'

    def setUp(self):
        self.auditor = Usuario.objects.create_user(
            username='auditor_prueba',
            password='ClaveSegura-2026',
            rol=Usuario.Rol.AUDITOR,
        )
        self.client.force_authenticate(self.auditor)

    def test_no_puede_cambiar_su_rol(self):
        self.client.patch(self.url, {'rol': 'admin'}, format='json')
        self.auditor.refresh_from_db()
        self.assertEqual(self.auditor.rol, Usuario.Rol.AUDITOR)

    def test_no_puede_cambiar_su_estado_activo(self):
        self.client.patch(self.url, {'activo': False}, format='json')
        self.auditor.refresh_from_db()
        self.assertTrue(self.auditor.activo)

    def test_no_puede_cambiar_su_username(self):
        self.client.patch(self.url, {'username': 'otro_nombre'}, format='json')
        self.auditor.refresh_from_db()
        self.assertEqual(self.auditor.username, 'auditor_prueba')

    def test_si_puede_editar_sus_datos_personales(self):
        # Control: el arreglo no debe impedir editar los campos permitidos.
        respuesta = self.client.patch(
            self.url,
            {'nombre_completo': 'Lic. Prueba', 'telefono': '3001234567'},
            format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.auditor.refresh_from_db()
        self.assertEqual(self.auditor.nombre_completo, 'Lic. Prueba')
        self.assertEqual(self.auditor.telefono, '3001234567')

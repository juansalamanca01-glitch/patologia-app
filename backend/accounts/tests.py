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


class ValidacionContrasenasTests(APITestCase):
    """
    Hallazgo I-11 de docs/auditoria-inicial.md: settings.py define validadores de
    contraseña (comunes, solo números, parecidas al usuario), pero ni el cambio de
    contraseña ni el registro los aplicaban. Se aceptaba "12345678".
    """

    CLAVE_ACTUAL = 'ClaveSegura-2026'

    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            username='patologo_claves', password=self.CLAVE_ACTUAL, rol=Usuario.Rol.PATOLOGO,
        )
        self.admin = Usuario.objects.create_user(
            username='admin_claves', password=self.CLAVE_ACTUAL, rol=Usuario.Rol.ADMIN,
        )

    def cambiar_clave(self, nueva):
        self.client.force_authenticate(self.usuario)
        return self.client.post(
            '/api/auth/cambiar-password/',
            {'old_password': self.CLAVE_ACTUAL, 'new_password': nueva},
            format='json',
        )

    def registrar(self, clave):
        self.client.force_authenticate(self.admin)
        return self.client.post('/api/auth/registro/', {
            'username': 'nuevo_patologo', 'email': 'nuevo@patologia.local',
            'password': clave, 'password_confirm': clave, 'rol': 'patologo',
        }, format='json')

    # ── Cambio de contraseña ───────────────────────────────────────

    def test_rechaza_contrasena_solo_numerica_y_comun(self):
        respuesta = self.cambiar_clave('12345678')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('new_password', respuesta.data)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password(self.CLAVE_ACTUAL))

    def test_rechaza_contrasena_parecida_al_usuario(self):
        respuesta = self.cambiar_clave('patologo_claves1')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password(self.CLAVE_ACTUAL))

    def test_acepta_contrasena_segura(self):
        # Control: una contraseña fuerte se sigue aceptando.
        respuesta = self.cambiar_clave('Histologia-Segura-2026')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('Histologia-Segura-2026'))

    # ── Registro de usuarios (solo admin) ──────────────────────────

    def test_registro_rechaza_contrasena_comun(self):
        respuesta = self.registrar('password123')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', respuesta.data)
        self.assertFalse(Usuario.objects.filter(username='nuevo_patologo').exists())

    def test_registro_acepta_contrasena_segura(self):
        # Control.
        respuesta = self.registrar('Histologia-Segura-2026')
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Usuario.objects.get(username='nuevo_patologo').check_password('Histologia-Segura-2026'))

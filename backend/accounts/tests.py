from django import forms
from django.test import TestCase
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
            username='patologo_claves',
            password=self.CLAVE_ACTUAL,
            rol=Usuario.Rol.PATOLOGO,
        )
        self.admin = Usuario.objects.create_user(
            username='admin_claves',
            password=self.CLAVE_ACTUAL,
            rol=Usuario.Rol.ADMIN,
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
        return self.client.post(
            '/api/auth/registro/',
            {
                'username': 'nuevo_patologo',
                'email': 'nuevo@patologia.local',
                'password': clave,
                'password_confirm': clave,
                'rol': 'patologo',
            },
            format='json',
        )

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


class CierreDeSesionTests(APITestCase):
    """
    Decisión D-6 (auditoría M-11): al cerrar sesión o cambiar la contraseña, el
    token de renovación (refresh) deja de servir. Antes seguía valiendo 7 días.
    """

    CLAVE = 'ClaveSegura-2026'

    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            username='sesiones',
            password=self.CLAVE,
            rol=Usuario.Rol.PATOLOGO,
        )

    def login(self):
        respuesta = self.client.post(
            '/api/auth/login/', {'username': 'sesiones', 'password': self.CLAVE}, format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        return respuesta.data

    def renovar(self, refresh):
        return self.client.post('/api/auth/refresh/', {'refresh': refresh}, format='json')

    def test_logout_invalida_el_token_de_renovacion(self):
        tokens = self.login()
        respuesta = self.client.post('/api/auth/logout/', {'refresh': tokens['refresh']}, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(self.renovar(tokens['refresh']).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_funciona_aunque_el_token_de_acceso_haya_vencido(self):
        tokens = self.login()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer token-de-acceso-vencido')
        respuesta = self.client.post('/api/auth/logout/', {'refresh': tokens['refresh']}, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)

    def test_logout_con_token_invalido_responde_400(self):
        respuesta = self.client.post('/api/auth/logout/', {'refresh': 'no-es-un-token'}, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_un_token_ya_renovado_no_se_puede_reutilizar(self):
        tokens = self.login()
        self.assertEqual(self.renovar(tokens['refresh']).status_code, status.HTTP_200_OK)
        self.assertEqual(self.renovar(tokens['refresh']).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cambiar_contrasena_invalida_las_sesiones_anteriores(self):
        sesion_1 = self.login()
        sesion_2 = self.login()  # por ejemplo, otro computador
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {sesion_1["access"]}')
        respuesta = self.client.post(
            '/api/auth/cambiar-password/',
            {'old_password': self.CLAVE, 'new_password': 'Histologia-Segura-2026'},
            format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.client.credentials()
        self.assertEqual(self.renovar(sesion_1['refresh']).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(self.renovar(sesion_2['refresh']).status_code, status.HTTP_401_UNAUTHORIZED)
        # La sesión desde la que se cambió la contraseña sigue abierta con tokens nuevos.
        self.assertEqual(self.renovar(respuesta.data['refresh']).status_code, status.HTTP_200_OK)


class RegistroMedicoTests(APITestCase):
    """
    Informe v2, etapa 6 (decisión D-8): el registro médico firma los informes, así
    que solo lo asigna un administrador. En el perfil es de solo lectura, como el rol (C-1).
    """

    CLAVE = 'Histologia-Segura-2026'

    def setUp(self):
        self.patologo = Usuario.objects.create_user(
            username='patologo_registro',
            password=self.CLAVE,
            rol=Usuario.Rol.PATOLOGO,
            registro_medico='RM-PRUEBA-0001',
        )
        self.admin = Usuario.objects.create_user(
            username='admin_registro',
            password=self.CLAVE,
            rol=Usuario.Rol.ADMIN,
        )

    def test_el_perfil_muestra_el_registro_medico(self):
        self.client.force_authenticate(self.patologo)
        respuesta = self.client.get('/api/auth/perfil/')
        self.assertEqual(respuesta.data['registro_medico'], 'RM-PRUEBA-0001')

    def test_no_puede_cambiar_su_registro_medico_desde_el_perfil(self):
        self.client.force_authenticate(self.patologo)
        self.client.patch('/api/auth/perfil/', {'registro_medico': 'RM-FALSO'}, format='json')
        self.patologo.refresh_from_db()
        self.assertEqual(self.patologo.registro_medico, 'RM-PRUEBA-0001')

    def test_el_login_devuelve_el_registro_medico(self):
        respuesta = self.client.post(
            '/api/auth/login/',
            {'username': 'patologo_registro', 'password': self.CLAVE},
            format='json',
        )
        self.assertEqual(respuesta.data['user']['registro_medico'], 'RM-PRUEBA-0001')

    def test_el_admin_asigna_el_registro_medico_al_crear_el_usuario(self):
        self.client.force_authenticate(self.admin)
        respuesta = self.client.post(
            '/api/auth/registro/',
            {
                'username': 'patologo_nuevo',
                'email': 'nuevo@patologia.local',
                'password': self.CLAVE,
                'password_confirm': self.CLAVE,
                'rol': 'patologo',
                'registro_medico': 'RM-PRUEBA-0002',
            },
            format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED, respuesta.data)
        self.assertEqual(Usuario.objects.get(username='patologo_nuevo').registro_medico, 'RM-PRUEBA-0002')

    def test_seed_data_da_registro_medico_a_patologo1(self):
        # También si patologo1 ya existía sin registro (bases creadas antes de la etapa 6).
        from io import StringIO
        from django.core.management import call_command

        Usuario.objects.create_user(username='patologo1', password=self.CLAVE, rol=Usuario.Rol.PATOLOGO)
        call_command('seed_data', stdout=StringIO())
        self.assertEqual(Usuario.objects.get(username='patologo1').registro_medico, 'RM-PRUEBA-0001')

    def test_seed_data_no_cambia_un_registro_medico_ya_asignado(self):
        from io import StringIO
        from django.core.management import call_command

        Usuario.objects.create_user(
            username='patologo1',
            password=self.CLAVE,
            rol=Usuario.Rol.PATOLOGO,
            registro_medico='RM-PRUEBA-0777',
        )
        call_command('seed_data', stdout=StringIO())
        self.assertEqual(Usuario.objects.get(username='patologo1').registro_medico, 'RM-PRUEBA-0777')

    # patologo2 sirve para probar que un patólogo no modifica informes de otro (D-2).

    def test_seed_data_crea_patologo2_con_su_registro_medico(self):
        from io import StringIO
        from django.core.management import call_command

        call_command('seed_data', stdout=StringIO())
        patologo2 = Usuario.objects.get(username='patologo2')
        self.assertEqual(patologo2.rol, Usuario.Rol.PATOLOGO)
        self.assertEqual(patologo2.registro_medico, 'RM-PRUEBA-0002')
        self.assertTrue(patologo2.check_password('patologo2345'))

    def test_seed_data_no_duplica_a_patologo2(self):
        from io import StringIO
        from django.core.management import call_command

        call_command('seed_data', stdout=StringIO())
        call_command('seed_data', stdout=StringIO())
        self.assertEqual(Usuario.objects.filter(username='patologo2').count(), 1)

    def test_seed_data_no_cambia_a_un_patologo2_que_ya_existia(self):
        # Como el que se creó a mano para la prueba manual del 2026-10-05.
        from io import StringIO
        from django.core.management import call_command

        Usuario.objects.create_user(
            username='patologo2',
            password=self.CLAVE,
            rol=Usuario.Rol.PATOLOGO,
            registro_medico='RM-PRUEBA-0888',
        )
        call_command('seed_data', stdout=StringIO())
        patologo2 = Usuario.objects.get(username='patologo2')
        self.assertEqual(patologo2.registro_medico, 'RM-PRUEBA-0888')
        self.assertTrue(patologo2.check_password(self.CLAVE))


class AdminUsuariosTests(TestCase):
    """
    Hallazgo del 2026-10-05: /admin/ registraba Usuario con un ModelAdmin común, así
    que al crear un usuario la contraseña no se cifraba y ese usuario no podía entrar.
    Con el UserAdmin de Django la contraseña se cifra, y se siguen editando el rol,
    la especialidad y el registro médico (D-8: solo un admin lo asigna).
    """

    def setUp(self):
        self.superusuario = Usuario.objects.create_superuser(
            username='super_admin_usuarios',
            password='ClaveSegura-2026',
            rol=Usuario.Rol.ADMIN,
        )
        self.client.force_login(self.superusuario)

    def test_crear_un_usuario_en_admin_cifra_la_contrasena(self):
        respuesta = self.client.post(
            '/admin/accounts/usuario/add/',
            {
                'username': 'patologo_desde_admin',
                'password1': 'ClaveSegura-2026',
                'password2': 'ClaveSegura-2026',
                'rol': Usuario.Rol.PATOLOGO,
                'registro_medico': 'RM-PRUEBA-0003',
            },
        )
        self.assertEqual(respuesta.status_code, 302)  # redirige: el usuario se creó
        usuario = Usuario.objects.get(username='patologo_desde_admin')
        self.assertTrue(usuario.password.startswith('pbkdf2_sha256$'))
        self.assertTrue(usuario.check_password('ClaveSegura-2026'))
        self.assertEqual(usuario.rol, Usuario.Rol.PATOLOGO)
        self.assertEqual(usuario.registro_medico, 'RM-PRUEBA-0003')

    def test_el_usuario_creado_en_admin_puede_iniciar_sesion(self):
        self.test_crear_un_usuario_en_admin_cifra_la_contrasena()
        respuesta = self.client.post(
            '/api/auth/login/',
            {
                'username': 'patologo_desde_admin',
                'password': 'ClaveSegura-2026',
            },
            content_type='application/json',
        )
        self.assertEqual(respuesta.status_code, 200)

    def test_la_ficha_del_usuario_no_muestra_la_contrasena_editable_y_si_los_campos_propios(self):
        usuario = Usuario.objects.create_user(username='patologo_ficha', password='ClaveSegura-2026')
        respuesta = self.client.get(f'/admin/accounts/usuario/{usuario.id}/change/')
        self.assertEqual(respuesta.status_code, 200)
        formulario = respuesta.context['adminform'].form
        for campo in ('rol', 'especialidad', 'registro_medico', 'telefono', 'nombre_completo'):
            self.assertIn(campo, formulario.fields)
        # El hash se muestra en solo lectura; la contraseña se cambia con el formulario de Django.
        self.assertNotIsInstance(formulario.fields['password'].widget, forms.TextInput)

from datetime import date, timedelta
from unittest import mock

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Usuario
from .models import EPS, Paciente


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


class EdadTests(TestCase):
    """
    Etapa 3 (sección 3.1): la edad no se guarda; se calcula a una fecha dada. En
    años cumplidos; si es menor de 1 año, en meses; si es menor de 1 mes, en días.
    """

    def paciente(self, nacimiento):
        return Paciente(fecha_nacimiento=nacimiento)

    def test_anios_cumplidos(self):
        p = self.paciente(date(1980, 10, 5))
        self.assertEqual(p.edad_en(date(2026, 10, 4)), '45 años')
        self.assertEqual(p.edad_en(date(2026, 10, 5)), '46 años')

    def test_un_anio_en_singular(self):
        self.assertEqual(self.paciente(date(2025, 3, 1)).edad_en(date(2026, 3, 1)), '1 año')

    def test_menor_de_un_anio_en_meses(self):
        p = self.paciente(date(2026, 1, 15))
        self.assertEqual(p.edad_en(date(2026, 10, 4)), '8 meses')
        self.assertEqual(p.edad_en(date(2026, 2, 15)), '1 mes')

    def test_menor_de_un_mes_en_dias(self):
        p = self.paciente(date(2026, 1, 31))
        self.assertEqual(p.edad_en(date(2026, 2, 28)), '28 días')
        self.assertEqual(p.edad_en(date(2026, 2, 1)), '1 día')
        self.assertEqual(p.edad_en(date(2026, 1, 31)), '0 días')

    def test_nacido_un_29_de_febrero(self):
        p = self.paciente(date(2024, 2, 29))
        self.assertEqual(p.edad_en(date(2027, 2, 28)), '2 años')
        self.assertEqual(p.edad_en(date(2027, 3, 1)), '3 años')

    def test_fecha_anterior_al_nacimiento(self):
        self.assertIsNone(self.paciente(date(2026, 1, 1)).edad_en(date(2025, 12, 31)))


class PacienteAPITests(APITestCase):
    """
    Etapa 3 (secciones 3.1 y 4, decisión D-11): CRUD de pacientes. Todos leen;
    patólogo y admin crean y editan; solo el admin borra. Solo datos ficticios
    (sección 8).
    """

    URL = '/api/pacientes/'

    def setUp(self):
        self.admin = Usuario.objects.create_user(username='pac_admin', password='x', rol=Usuario.Rol.ADMIN)
        self.patologo = Usuario.objects.create_user(username='pac_pat', password='x', rol=Usuario.Rol.PATOLOGO)
        self.auditor = Usuario.objects.create_user(username='pac_aud', password='x', rol=Usuario.Rol.AUDITOR)
        self.eps = EPS.objects.create(nombre='Particular')

    def datos(self, **extra):
        return {
            'tipo_documento': 'CC', 'numero_documento': 'PRUEBA0001',
            'nombres': 'Paciente Ficticio', 'apellidos': 'Uno',
            'fecha_nacimiento': '1980-10-05', 'sexo': 'femenino', 'eps': self.eps.id,
            **extra,
        }

    def crear(self, usuario=None, **extra):
        self.client.force_authenticate(usuario or self.patologo)
        return self.client.post(self.URL, self.datos(**extra), format='json')

    # --- Permisos (D-11) ---

    def test_patologo_crea_y_auditor_lee(self):
        respuesta = self.crear()
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED, respuesta.data)
        self.client.force_authenticate(self.auditor)
        listado = self.client.get(self.URL).data
        self.assertEqual(listado['count'], 1)
        self.assertEqual(listado['results'][0]['numero_documento'], 'PRUEBA0001')

    def test_sin_sesion_no_ve_pacientes(self):
        self.assertEqual(self.client.get(self.URL).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_auditor_no_crea_ni_edita(self):
        self.assertEqual(self.crear(usuario=self.auditor).status_code, status.HTTP_403_FORBIDDEN)
        paciente_id = self.crear().data['id']
        self.client.force_authenticate(self.auditor)
        respuesta = self.client.patch(f'{self.URL}{paciente_id}/', {'nombres': 'Otro'}, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    def test_patologo_edita_pero_no_borra(self):
        paciente_id = self.crear().data['id']
        respuesta = self.client.patch(f'{self.URL}{paciente_id}/', {'apellidos': 'Dos'}, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['apellidos'], 'Dos')
        self.assertEqual(self.client.delete(f'{self.URL}{paciente_id}/').status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Paciente.objects.filter(pk=paciente_id).exists())

    def test_admin_borra(self):
        paciente_id = self.crear().data['id']
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.delete(f'{self.URL}{paciente_id}/').status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Paciente.objects.filter(pk=paciente_id).exists())

    # --- Datos que devuelve ---

    def test_devuelve_edad_de_hoy_y_nombre_de_la_eps(self):
        with mock.patch('pacientes.models.timezone.localdate', return_value=date(2026, 10, 4)):
            datos = self.crear().data
        self.assertEqual(datos['edad'], '45 años')
        self.assertEqual(datos['eps_nombre'], 'Particular')

    def test_eps_es_opcional(self):
        respuesta = self.crear(eps=None)
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED, respuesta.data)
        self.assertIsNone(respuesta.data['eps_nombre'])

    # --- Validaciones (3.1) ---

    def test_documento_se_guarda_sin_espacios_ni_puntos(self):
        respuesta = self.crear(numero_documento=' prueba.00 01 ')
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED, respuesta.data)
        self.assertEqual(respuesta.data['numero_documento'], 'PRUEBA0001')

    def test_documento_repetido_responde_400(self):
        self.crear()
        respuesta = self.crear(numero_documento='prueba.0001', nombres='Otro')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('numero_documento', respuesta.data)
        self.assertEqual(Paciente.objects.count(), 1)

    def test_mismo_numero_con_otro_tipo_de_documento_es_otro_paciente(self):
        self.crear()
        self.assertEqual(self.crear(tipo_documento='TI').status_code, status.HTTP_201_CREATED)

    def test_editar_sin_cambiar_el_documento_no_cuenta_como_repetido(self):
        paciente_id = self.crear().data['id']
        respuesta = self.client.put(f'{self.URL}{paciente_id}/', self.datos(nombres='Corregido'), format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK, respuesta.data)

    def test_fecha_de_nacimiento_en_el_futuro(self):
        manana = timezone.localdate() + timedelta(days=1)
        respuesta = self.crear(fecha_nacimiento=manana.isoformat())
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('fecha_nacimiento', respuesta.data)

    def test_fecha_de_nacimiento_de_hace_mas_de_130_anios(self):
        respuesta = self.crear(fecha_nacimiento='1850-01-01')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('fecha_nacimiento', respuesta.data)

    def test_nombres_sin_espacios_sobrantes(self):
        datos = self.crear(nombres='  Paciente   Ficticio ', apellidos=' Uno ').data
        self.assertEqual((datos['nombres'], datos['apellidos']), ('Paciente Ficticio', 'Uno'))

    def test_eps_inactiva_no_se_asigna(self):
        inactiva = EPS.objects.create(nombre='EPS Liquidada', activa=False)
        respuesta = self.crear(eps=inactiva.id)
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('eps', respuesta.data)

    def test_paciente_conserva_su_eps_aunque_se_desactive(self):
        # Desactivar una EPS (D-4) no debe impedir corregir otros datos del paciente.
        paciente_id = self.crear().data['id']
        EPS.objects.filter(pk=self.eps.id).update(activa=False)
        respuesta = self.client.put(f'{self.URL}{paciente_id}/', self.datos(nombres='Corregido'), format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK, respuesta.data)

    # --- Búsqueda ?q= ---

    def test_busqueda_por_documento_nombres_y_apellidos(self):
        self.crear()
        self.crear(numero_documento='PRUEBA0002', nombres='Prueba', apellidos='Apellido Dos')
        self.client.force_authenticate(self.auditor)

        def documentos(q):
            return [p['numero_documento'] for p in self.client.get(self.URL, {'q': q}).data['results']]

        self.assertEqual(documentos('0002'), ['PRUEBA0002'])
        self.assertEqual(documentos('ficticio'), ['PRUEBA0001'])
        self.assertEqual(documentos('apellido dos'), ['PRUEBA0002'])
        self.assertEqual(documentos('ficticio uno'), ['PRUEBA0001'])  # nombres + apellidos
        self.assertEqual(sorted(documentos('prueba')), ['PRUEBA0001', 'PRUEBA0002'])
        self.assertEqual(documentos('nadie'), [])

    def test_seed_data_crea_dos_pacientes_ficticios(self):
        from io import StringIO
        from django.core.management import call_command
        call_command('seed_data', stdout=StringIO())
        call_command('seed_data', stdout=StringIO())  # dos veces: no duplica
        documentos = list(Paciente.objects.values_list('numero_documento', flat=True))
        self.assertEqual(len(documentos), 2)
        self.assertTrue(all(d.startswith('PRUEBA') for d in documentos))


class BorrarEPSConPacientesTests(APITestCase):
    """Etapa 3: una EPS que usa un paciente no se borra (PROTECT); se responde 400, como en I-1."""

    def setUp(self):
        self.client.force_authenticate(
            Usuario.objects.create_user(username='eps_admin', password='x', rol=Usuario.Rol.ADMIN)
        )

    def test_borrar_eps_en_uso_responde_400(self):
        eps = EPS.objects.create(nombre='Particular')
        Paciente.objects.create(
            tipo_documento='CC', numero_documento='PRUEBA0001', nombres='Paciente Ficticio',
            apellidos='Uno', fecha_nacimiento=date(1980, 10, 5), sexo='femenino', eps=eps,
        )
        respuesta = self.client.delete(f'/api/pacientes/eps/{eps.id}/')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Desactívela', respuesta.data['detail'])
        self.assertTrue(EPS.objects.filter(pk=eps.id).exists())

    def test_borrar_eps_sin_uso_sigue_funcionando(self):
        eps = EPS.objects.create(nombre='Sin uso')
        self.assertEqual(self.client.delete(f'/api/pacientes/eps/{eps.id}/').status_code, status.HTTP_204_NO_CONTENT)

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Usuario
from .models import Informe, Patologia


class PermisosInformeTests(APITestCase):
    """
    Hallazgo C-2 de docs/auditoria-inicial.md y decisión D-2 de docs/decisiones.md:
    - un informe finalizado no se puede editar ni borrar;
    - solo el autor o un admin puede editar, borrar o finalizar un informe.
    """

    def setUp(self):
        self.autor = Usuario.objects.create_user(
            username='patologo_autor', password='ClaveSegura-2026', rol=Usuario.Rol.PATOLOGO,
        )
        self.otro_patologo = Usuario.objects.create_user(
            username='patologo_otro', password='ClaveSegura-2026', rol=Usuario.Rol.PATOLOGO,
        )
        self.admin = Usuario.objects.create_user(
            username='admin_prueba', password='ClaveSegura-2026', rol=Usuario.Rol.ADMIN,
        )
        self.auditor = Usuario.objects.create_user(
            username='auditor_prueba', password='ClaveSegura-2026', rol=Usuario.Rol.AUDITOR,
        )
        self.patologia = Patologia.objects.create(nombre='Patología de prueba')

    def crear_informe(self, estado=Informe.Estado.BORRADOR):
        return Informe.objects.create(
            numero_caso=f'PRUEBA-{Informe.objects.count() + 1}',
            patologia=self.patologia,
            autor=self.autor,
            notas='original',
            estado=estado,
        )

    def url(self, informe, accion=''):
        return f'/api/informes/{informe.id}/{accion}'

    # ── Informe finalizado: nadie puede modificarlo ───────────────

    def test_autor_no_puede_editar_informe_finalizado(self):
        informe = self.crear_informe(Informe.Estado.FINALIZADO)
        self.client.force_authenticate(self.autor)
        respuesta = self.client.patch(self.url(informe), {'notas': 'cambiado'}, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        informe.refresh_from_db()
        self.assertEqual(informe.notas, 'original')

    def test_autor_no_puede_borrar_informe_finalizado(self):
        informe = self.crear_informe(Informe.Estado.FINALIZADO)
        self.client.force_authenticate(self.autor)
        respuesta = self.client.delete(self.url(informe))
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Informe.objects.filter(id=informe.id).exists())

    def test_admin_tampoco_puede_editar_ni_borrar_informe_finalizado(self):
        # Decisión D-3: el bloqueo de informes finalizados también aplica al admin.
        informe = self.crear_informe(Informe.Estado.FINALIZADO)
        self.client.force_authenticate(self.admin)
        respuesta = self.client.patch(self.url(informe), {'notas': 'cambiado'}, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        respuesta = self.client.delete(self.url(informe))
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        informe.refresh_from_db()
        self.assertEqual(informe.notas, 'original')

    # ── Informe ajeno: otro patólogo no puede tocarlo (D-2) ───────

    def test_otro_patologo_no_puede_editar_informe_ajeno(self):
        informe = self.crear_informe()
        self.client.force_authenticate(self.otro_patologo)
        respuesta = self.client.patch(self.url(informe), {'notas': 'cambiado'}, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)
        informe.refresh_from_db()
        self.assertEqual(informe.notas, 'original')

    def test_otro_patologo_no_puede_borrar_informe_ajeno(self):
        informe = self.crear_informe()
        self.client.force_authenticate(self.otro_patologo)
        respuesta = self.client.delete(self.url(informe))
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Informe.objects.filter(id=informe.id).exists())

    def test_otro_patologo_no_puede_finalizar_informe_ajeno(self):
        informe = self.crear_informe()
        self.client.force_authenticate(self.otro_patologo)
        respuesta = self.client.post(self.url(informe, 'finalizar/'))
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)
        informe.refresh_from_db()
        self.assertEqual(informe.estado, Informe.Estado.BORRADOR)

    def test_otro_patologo_si_puede_ver_informe_ajeno(self):
        informe = self.crear_informe()
        self.client.force_authenticate(self.otro_patologo)
        self.assertEqual(self.client.get(self.url(informe)).status_code, status.HTTP_200_OK)

    # ── Controles: lo permitido debe seguir funcionando ──────────

    def test_autor_puede_editar_y_finalizar_su_borrador(self):
        informe = self.crear_informe()
        self.client.force_authenticate(self.autor)
        respuesta = self.client.patch(self.url(informe), {'notas': 'cambiado'}, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        respuesta = self.client.post(self.url(informe, 'finalizar/'))
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        informe.refresh_from_db()
        self.assertEqual(informe.notas, 'cambiado')
        self.assertEqual(informe.estado, Informe.Estado.FINALIZADO)

    def test_autor_puede_borrar_su_borrador(self):
        informe = self.crear_informe()
        self.client.force_authenticate(self.autor)
        respuesta = self.client.delete(self.url(informe))
        self.assertEqual(respuesta.status_code, status.HTTP_204_NO_CONTENT)

    def test_admin_puede_editar_y_finalizar_borrador_ajeno(self):
        informe = self.crear_informe()
        self.client.force_authenticate(self.admin)
        respuesta = self.client.patch(self.url(informe), {'notas': 'revisado'}, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        respuesta = self.client.post(self.url(informe, 'finalizar/'))
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)

    def test_listado_incluye_id_del_autor(self):
        # El frontend lo usa para mostrar los botones solo al autor o al admin.
        informe = self.crear_informe()
        self.client.force_authenticate(self.otro_patologo)
        resultados = self.client.get('/api/informes/').data['results']
        self.assertEqual(resultados[0]['autor'], self.autor.id)
        self.assertEqual(resultados[0]['id'], informe.id)

    def test_auditor_no_puede_editar(self):
        informe = self.crear_informe()
        self.client.force_authenticate(self.auditor)
        respuesta = self.client.patch(self.url(informe), {'notas': 'cambiado'}, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)


class BorrarPatologiaTests(APITestCase):
    """
    Hallazgo I-1 de docs/auditoria-inicial.md: borrar una patología que ya tiene
    informes debe responder 400 con un mensaje claro, no un error 500.
    """

    def setUp(self):
        self.patologo = Usuario.objects.create_user(
            username='patologo_prueba', password='ClaveSegura-2026', rol=Usuario.Rol.PATOLOGO,
        )
        self.client.force_authenticate(self.patologo)
        self.patologia = Patologia.objects.create(nombre='Patología con informes')

    def test_no_se_puede_borrar_patologia_con_informes(self):
        Informe.objects.create(numero_caso='I1-1', patologia=self.patologia, autor=self.patologo)
        respuesta = self.client.delete(f'/api/patologias/{self.patologia.id}/')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('informe', respuesta.data['detail'])
        self.assertTrue(Patologia.objects.filter(id=self.patologia.id).exists())

    def test_si_se_puede_borrar_patologia_sin_informes(self):
        # Control: sin informes asociados, el borrado funciona como antes.
        respuesta = self.client.delete(f'/api/patologias/{self.patologia.id}/')
        self.assertEqual(respuesta.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Patologia.objects.filter(id=self.patologia.id).exists())

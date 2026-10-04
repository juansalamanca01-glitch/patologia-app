from unittest import mock

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Usuario
from .models import Informe, Patologia, Plantilla


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


class PdfConTextoDelUsuarioTests(APITestCase):
    """
    Hallazgo I-3 de docs/auditoria-inicial.md: ReportLab interpreta el texto de
    Paragraph como marcado (<b>, <font>...). El texto que escribe el usuario debe
    salir tal cual en el PDF: sin romper la generación y sin cambiar el formato.
    """

    def setUp(self):
        self.patologo = Usuario.objects.create_user(
            username='patologo_pdf', password='ClaveSegura-2026', rol=Usuario.Rol.PATOLOGO,
        )
        self.client.force_authenticate(self.patologo)
        self.informe = Informe.objects.create(
            numero_caso='PDF-1',
            patologia=Patologia.objects.create(nombre='Patología PDF'),
            autor=self.patologo,
            datos_ingresados={'hallazgos': 'ver <i>H. pylori', 'campo<br>raro': 'tejido <br> pardo'},
            texto_generado='Lesión <b>grande',
            notas='<font size=40>ENORME</font> & margen < 2 mm',
        )

    def descargar_pdf(self):
        return self.client.get(f'/api/informes/{self.informe.id}/pdf/')

    def test_pdf_se_genera_con_texto_que_parece_marcado(self):
        respuesta = self.descargar_pdf()
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta['Content-Type'], 'application/pdf')

    def test_el_marcado_del_usuario_no_se_interpreta(self):
        from reportlab.platypus import Paragraph
        with mock.patch('informes.utils.Paragraph', wraps=Paragraph) as espia:
            self.descargar_pdf()
        textos = ' '.join(str(llamada.args[0]) for llamada in espia.call_args_list)
        # El texto del usuario llega escapado: se verá literal en el PDF.
        self.assertIn('&lt;font size=40&gt;ENORME&lt;/font&gt; &amp; margen &lt; 2 mm', textos)
        self.assertIn('Lesión &lt;b&gt;grande', textos)
        self.assertIn('ver &lt;i&gt;H. pylori', textos)
        self.assertNotIn('<font size=40>', textos)

    def test_los_saltos_de_linea_de_las_notas_se_respetan(self):
        from reportlab.platypus import Paragraph
        self.informe.notas = 'Primera línea\r\nSegunda línea\nTercera < línea'
        self.informe.save()
        with mock.patch('informes.utils.Paragraph', wraps=Paragraph) as espia:
            respuesta = self.descargar_pdf()
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        textos = [str(llamada.args[0]) for llamada in espia.call_args_list]
        self.assertIn('Primera línea<br/>Segunda línea<br/>Tercera &lt; línea', textos)


class EstadisticasYPaginacionTests(APITestCase):
    """
    Hallazgo I-4 de docs/auditoria-inicial.md: el dashboard y el buscador solo
    veían la primera página (20 informes). Con 25 informes, el dashboard decía
    "total 20" y el buscador no permitía ver los otros 5.
    """

    def setUp(self):
        self.patologo = Usuario.objects.create_user(
            username='patologo_stats', password='ClaveSegura-2026', rol=Usuario.Rol.PATOLOGO,
        )
        patologia = Patologia.objects.create(nombre='Patología estadísticas')
        for i in range(25):
            Informe.objects.create(
                numero_caso=f'I4-{i}',
                patologia=patologia,
                autor=self.patologo,
                estado=Informe.Estado.FINALIZADO if i < 15 else Informe.Estado.BORRADOR,
            )
        self.client.force_authenticate(self.patologo)

    def test_estadisticas_cuentan_todos_los_informes(self):
        respuesta = self.client.get('/api/informes/estadisticas/')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data, {'total': 25, 'borradores': 10, 'finalizados': 15})

    def test_auditor_puede_ver_estadisticas(self):
        auditor = Usuario.objects.create_user(
            username='auditor_stats', password='ClaveSegura-2026', rol=Usuario.Rol.AUDITOR,
        )
        self.client.force_authenticate(auditor)
        self.assertEqual(self.client.get('/api/informes/estadisticas/').status_code, status.HTTP_200_OK)

    def test_estadisticas_requieren_autenticacion(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get('/api/informes/estadisticas/').status_code, status.HTTP_401_UNAUTHORIZED)

    def test_la_segunda_pagina_trae_los_informes_restantes(self):
        # Lo que usa la paginación del buscador: count, next y previous.
        primera = self.client.get('/api/informes/').data
        self.assertEqual(primera['count'], 25)
        self.assertEqual(len(primera['results']), 20)
        self.assertIsNotNone(primera['next'])
        segunda = self.client.get('/api/informes/', {'page': 2}).data
        self.assertEqual(len(segunda['results']), 5)
        self.assertIsNone(segunda['next'])
        self.assertIsNotNone(segunda['previous'])

    def test_la_paginacion_respeta_los_filtros(self):
        respuesta = self.client.get('/api/informes/', {'estado': 'borrador', 'page': 1}).data
        self.assertEqual(respuesta['count'], 10)
        self.assertTrue(all(i['estado'] == 'borrador' for i in respuesta['results']))


class DescargaPdfTests(APITestCase):
    """
    Hallazgo I-5 de docs/auditoria-inicial.md: el token de sesión no debe viajar
    en la URL (queda en el historial y en los registros del servidor). El PDF se
    descarga solo por /api/informes/{id}/pdf/ con la cabecera Authorization.
    """

    def setUp(self):
        self.patologo = Usuario.objects.create_user(
            username='patologo_descarga', password='ClaveSegura-2026', rol=Usuario.Rol.PATOLOGO,
        )
        self.informe = Informe.objects.create(
            numero_caso='PAT-1',
            patologia=Patologia.objects.create(nombre='Patología descarga'),
            autor=self.patologo,
        )
        self.url = f'/api/informes/{self.informe.id}/pdf/'

    def test_descarga_con_cabecera_authorization(self):
        self.client.force_authenticate(self.patologo)
        respuesta = self.client.get(self.url)
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta['Content-Type'], 'application/pdf')
        self.assertEqual(respuesta['Content-Disposition'], 'attachment; filename="informe_PAT-1.pdf"')

    def test_auditor_puede_descargar(self):
        auditor = Usuario.objects.create_user(
            username='auditor_descarga', password='ClaveSegura-2026', rol=Usuario.Rol.AUDITOR,
        )
        self.client.force_authenticate(auditor)
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_200_OK)

    def test_sin_autenticacion_no_descarga(self):
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_ya_no_existe_la_descarga_con_token_en_la_url(self):
        from rest_framework_simplejwt.tokens import AccessToken
        token = str(AccessToken.for_user(self.patologo))
        respuesta = self.client.get(f'/api/descargar-pdf/{self.informe.id}/informe.pdf', {'token': token})
        self.assertEqual(respuesta.status_code, status.HTTP_404_NOT_FOUND)

    def test_nombre_de_archivo_sin_caracteres_peligrosos(self):
        # Las comillas o el punto y coma del número de caso podrían romper la cabecera.
        self.informe.numero_caso = 'PAT 1"x";y'
        self.informe.save()
        self.client.force_authenticate(self.patologo)
        respuesta = self.client.get(self.url)
        self.assertEqual(respuesta['Content-Disposition'], 'attachment; filename="informe_PAT_1_x__y.pdf"')


class CamposObligatoriosTests(APITestCase):
    """
    Hallazgo I-2 de docs/auditoria-inicial.md: la validación de los campos
    obligatorios de la plantilla se saltaba si datos_ingresados llegaba vacío.
    """

    def setUp(self):
        self.patologo = Usuario.objects.create_user(
            username='patologo_obligatorios', password='ClaveSegura-2026', rol=Usuario.Rol.PATOLOGO,
        )
        self.client.force_authenticate(self.patologo)
        self.patologia = Patologia.objects.create(nombre='Patología con obligatorios')
        Plantilla.objects.create(patologia=self.patologia, campo_nombre='localizacion',
                                 campo_label='Localización', tipo_campo='texto', obligatorio=True)
        Plantilla.objects.create(patologia=self.patologia, campo_nombre='num_ganglios',
                                 campo_label='Número de ganglios', tipo_campo='numero', obligatorio=True)
        Plantilla.objects.create(patologia=self.patologia, campo_nombre='color',
                                 campo_label='Color', tipo_campo='texto', obligatorio=False)
        self.datos_completos = {'localizacion': 'Axila izquierda', 'num_ganglios': 3}

    def crear(self, **extra):
        cuerpo = {'numero_caso': f'I2-{Informe.objects.count() + 1}', 'patologia': self.patologia.id, **extra}
        return self.client.post('/api/informes/', cuerpo, format='json')

    def test_rechaza_datos_vacios(self):
        respuesta = self.crear(datos_ingresados={})
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Localización', str(respuesta.data['datos_ingresados']))
        self.assertEqual(Informe.objects.count(), 0)

    def test_rechaza_si_no_se_envian_datos(self):
        respuesta = self.crear()
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Informe.objects.count(), 0)

    def test_rechaza_obligatorio_en_blanco(self):
        respuesta = self.crear(datos_ingresados={'localizacion': '   ', 'num_ganglios': 3})
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cero_es_un_valor_valido(self):
        # "0 ganglios" es un dato clínico real, no un campo vacío.
        respuesta = self.crear(datos_ingresados={'localizacion': 'Axila izquierda', 'num_ganglios': 0})
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)

    def test_acepta_datos_completos(self):
        # Control.
        self.assertEqual(self.crear(datos_ingresados=self.datos_completos).status_code, status.HTTP_201_CREATED)

    def test_patch_de_solo_notas_no_exige_reenviar_los_datos(self):
        # Control: editar solo las notas no debe fallar por "faltan campos".
        informe_id = self.crear(datos_ingresados=self.datos_completos).data['id']
        respuesta = self.client.patch(f'/api/informes/{informe_id}/', {'notas': 'Revisado'}, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)

    def test_patch_que_vacia_un_obligatorio_se_rechaza(self):
        informe_id = self.crear(datos_ingresados=self.datos_completos).data['id']
        respuesta = self.client.patch(
            f'/api/informes/{informe_id}/', {'datos_ingresados': {'num_ganglios': 3}}, format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

import threading
from datetime import date, datetime, timedelta
from unittest import mock

from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from accounts.models import Usuario
from pacientes.models import EPS, Paciente
from .models import Categoria, Diagnostico, Informe, Patologia, Plantilla, Servicio


def paciente_ficticio(numero='PRUEBA0001', **extra):
    """Paciente con datos ficticios (docs/propuesta-informe-v2.md, sección 8)."""
    datos = {
        'tipo_documento': 'CC', 'numero_documento': numero,
        'nombres': 'Paciente Ficticio', 'apellidos': 'Uno',
        'fecha_nacimiento': date(1980, 10, 5), 'sexo': 'femenino',
        **extra,
    }
    return Paciente.objects.create(**datos)


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
        # Lo que exige finalizar (D-8): el autor tiene registro médico y el informe,
        # paciente, diagnóstico y descripción microscópica.
        self.autor.registro_medico = 'RM-PRUEBA-0001'
        self.autor.save()
        self.patologia = Patologia.objects.create(nombre='Patología de prueba')
        self.paciente = paciente_ficticio()

    def crear_informe(self, estado=Informe.Estado.BORRADOR):
        informe = Informe.objects.create(
            patologia=self.patologia,
            autor=self.autor,
            paciente=self.paciente,
            descripcion_microscopica='Hallazgos de prueba.',
            comentarios='original',
            estado=estado,
        )
        Diagnostico.objects.create(informe=informe, orden=1, descripcion='Diagnóstico de prueba')
        return informe

    def url(self, informe, accion=''):
        return f'/api/informes/{informe.id}/{accion}'

    # ── Informe finalizado: nadie puede modificarlo ───────────────

    def test_autor_no_puede_editar_informe_finalizado(self):
        informe = self.crear_informe(Informe.Estado.FINALIZADO)
        self.client.force_authenticate(self.autor)
        respuesta = self.client.patch(self.url(informe), {'comentarios': 'cambiado'}, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        informe.refresh_from_db()
        self.assertEqual(informe.comentarios, 'original')

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
        respuesta = self.client.patch(self.url(informe), {'comentarios': 'cambiado'}, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        respuesta = self.client.delete(self.url(informe))
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        informe.refresh_from_db()
        self.assertEqual(informe.comentarios, 'original')

    # ── Informe ajeno: otro patólogo no puede tocarlo (D-2) ───────

    def test_otro_patologo_no_puede_editar_informe_ajeno(self):
        informe = self.crear_informe()
        self.client.force_authenticate(self.otro_patologo)
        respuesta = self.client.patch(self.url(informe), {'comentarios': 'cambiado'}, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)
        informe.refresh_from_db()
        self.assertEqual(informe.comentarios, 'original')

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
        respuesta = self.client.patch(self.url(informe), {'comentarios': 'cambiado'}, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        respuesta = self.client.post(self.url(informe, 'finalizar/'))
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        informe.refresh_from_db()
        self.assertEqual(informe.comentarios, 'cambiado')
        self.assertEqual(informe.estado, Informe.Estado.FINALIZADO)

    def test_autor_puede_borrar_su_borrador(self):
        informe = self.crear_informe()
        self.client.force_authenticate(self.autor)
        respuesta = self.client.delete(self.url(informe))
        self.assertEqual(respuesta.status_code, status.HTTP_204_NO_CONTENT)

    def test_admin_puede_editar_y_finalizar_borrador_ajeno(self):
        informe = self.crear_informe()
        self.client.force_authenticate(self.admin)
        respuesta = self.client.patch(self.url(informe), {'comentarios': 'revisado'}, format='json')
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
        respuesta = self.client.patch(self.url(informe), {'comentarios': 'cambiado'}, format='json')
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
        Informe.objects.create(patologia=self.patologia, autor=self.patologo)
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
            patologia=Patologia.objects.create(nombre='Patología PDF'),
            autor=self.patologo,
            datos_ingresados={'hallazgos': 'ver <i>H. pylori', 'campo<br>raro': 'tejido <br> pardo'},
            texto_generado='Lesión <b>grande',
            comentarios='<font size=40>ENORME</font> & margen < 2 mm',
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

    def test_los_saltos_de_linea_de_los_comentarios_se_respetan(self):
        from reportlab.platypus import Paragraph
        self.informe.comentarios = 'Primera línea\r\nSegunda línea\nTercera < línea'
        self.informe.save()
        with mock.patch('informes.utils.Paragraph', wraps=Paragraph) as espia:
            respuesta = self.descargar_pdf()
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        textos = [str(llamada.args[0]) for llamada in espia.call_args_list]
        self.assertIn('Primera línea<br/>Segunda línea<br/>Tercera &lt; línea', textos)

    def test_la_hora_del_pie_usa_la_zona_horaria_de_bogota(self):
        # Hallazgo M-10: el pie usaba la hora del servidor (datetime.now()), no TIME_ZONE.
        from datetime import datetime, timezone as tz
        from reportlab.platypus import Paragraph
        ahora_utc = datetime(2026, 10, 4, 3, 30, tzinfo=tz.utc)  # en Bogotá: 3 de octubre, 22:30
        with mock.patch('django.utils.timezone.now', return_value=ahora_utc),                 mock.patch('informes.utils.Paragraph', wraps=Paragraph) as espia:
            self.descargar_pdf()
        textos = ' '.join(str(llamada.args[0]) for llamada in espia.call_args_list)
        self.assertIn('Generado el 03/10/2026 22:30', textos)


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
            patologia=Patologia.objects.create(nombre='Patología descarga'),
            autor=self.patologo,
        )
        self.url = f'/api/informes/{self.informe.id}/pdf/'

    def test_descarga_con_cabecera_authorization(self):
        self.client.force_authenticate(self.patologo)
        respuesta = self.client.get(self.url)
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta['Content-Type'], 'application/pdf')
        self.assertEqual(
            respuesta['Content-Disposition'], f'attachment; filename="informe_{self.informe.numero_peticion}.pdf"',
        )

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
        # Las comillas o el punto y coma romperían la cabecera. El número de petición
        # lo genera el sistema (D-7), pero la limpieza se mantiene como defensa.
        self.informe.numero_peticion = 'PAT 1"x";y'
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
        self.paciente = paciente_ficticio()

    def crear(self, **extra):
        cuerpo = {'patologia': self.patologia.id, 'paciente': self.paciente.id, **extra}
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

    def test_patch_de_solo_comentarios_no_exige_reenviar_los_datos(self):
        # Control: editar solo los comentarios no debe fallar por "faltan campos".
        informe_id = self.crear(datos_ingresados=self.datos_completos).data['id']
        respuesta = self.client.patch(f'/api/informes/{informe_id}/', {'comentarios': 'Revisado'}, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)

    def test_patch_que_vacia_un_obligatorio_se_rechaza(self):
        informe_id = self.crear(datos_ingresados=self.datos_completos).data['id']
        respuesta = self.client.patch(
            f'/api/informes/{informe_id}/', {'datos_ingresados': {'num_ganglios': 3}}, format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)


class NombreVisibleAutorTests(APITestCase):
    """
    Auditoría M-3: "nombre_completo o, si está vacío, username" estaba repetido en
    8 lugares. Ahora lo calcula Usuario.nombre_visible. La API debe responder igual.
    """

    def setUp(self):
        self.con_nombre = Usuario.objects.create_user(
            username='dr_mendez', password='ClaveSegura-2026', rol=Usuario.Rol.PATOLOGO,
            nombre_completo='Dr. Carlos Méndez',
        )
        self.sin_nombre = Usuario.objects.create_user(
            username='patologo_sin_nombre', password='ClaveSegura-2026', rol=Usuario.Rol.PATOLOGO,
        )
        patologia = Patologia.objects.create(nombre='Patología nombres')
        for autor in (self.con_nombre, self.sin_nombre):
            Informe.objects.create(patologia=patologia, autor=autor)
        self.client.force_authenticate(self.con_nombre)

    def test_informes_muestran_nombre_completo_o_username(self):
        nombres = {i['autor']: i['autor_nombre'] for i in self.client.get('/api/informes/').data['results']}
        self.assertEqual(nombres[self.con_nombre.id], 'Dr. Carlos Méndez')
        self.assertEqual(nombres[self.sin_nombre.id], 'patologo_sin_nombre')
        informe = Informe.objects.get(autor=self.sin_nombre)
        self.assertEqual(self.client.get(f'/api/informes/{informe.id}/').data['autor_nombre'], 'patologo_sin_nombre')

    def test_foro_muestra_nombre_completo_o_username(self):
        from foro.models import Comentario, Publicacion
        publicacion = Publicacion.objects.create(autor=self.sin_nombre, titulo='Caso', contenido='Texto')
        Comentario.objects.create(publicacion=publicacion, autor=self.con_nombre, contenido='Hola')
        self.assertEqual(self.client.get('/api/foro/publicaciones/').data['results'][0]['autor_nombre'], 'patologo_sin_nombre')
        detalle = self.client.get(f'/api/foro/publicaciones/{publicacion.id}/').data
        self.assertEqual(detalle['autor_nombre'], 'patologo_sin_nombre')
        self.assertEqual(detalle['comentarios'][0]['autor_nombre'], 'Dr. Carlos Méndez')


class ConsultasPorListadoTests(APITestCase):
    """
    Hallazgo M-4 de docs/auditoria-inicial.md: algunos listados hacían una consulta
    extra por cada fila (problema "N+1"). El número de consultas no debe crecer
    con la cantidad de elementos.
    """

    def setUp(self):
        from foro.models import Comentario, ImagenPublicacion, Publicacion, TemaForo
        self.modelos = (Comentario, ImagenPublicacion, Publicacion, TemaForo)
        self.usuario = Usuario.objects.create_user(username='consultas', password='x', rol=Usuario.Rol.ADMIN)
        self.client.force_authenticate(self.usuario)

    def crear_elementos(self, desde, hasta):
        Comentario, ImagenPublicacion, Publicacion, TemaForo = self.modelos
        for i in range(desde, hasta):
            categoria = Categoria.objects.create(nombre=f'Categoría {i}')
            Patologia.objects.create(nombre=f'Patología {i}', categoria=categoria)
            tema = TemaForo.objects.create(nombre=f'Tema {i}')
            publicacion = Publicacion.objects.create(autor=self.usuario, titulo='t', contenido='c', tema=tema)
            Comentario.objects.create(publicacion=publicacion, autor=self.usuario, contenido='c')
            ImagenPublicacion.objects.create(publicacion=publicacion, imagen=f'foro/prueba{i}.png')

    def contar_consultas(self, url):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        with CaptureQueriesContext(connection) as consultas:
            self.assertEqual(self.client.get(url).status_code, status.HTTP_200_OK)
        return len(consultas)

    def test_las_consultas_no_crecen_con_los_elementos(self):
        urls = ['/api/categorias/', '/api/patologias/', '/api/foro/temas/', '/api/foro/publicaciones/']
        self.crear_elementos(0, 5)
        con_5 = {url: self.contar_consultas(url) for url in urls}
        self.crear_elementos(5, 20)
        con_20 = {url: self.contar_consultas(url) for url in urls}
        self.assertEqual(con_20, con_5)

    def test_crear_categoria_y_tema_devuelve_su_total(self):
        respuesta = self.client.post('/api/categorias/', {'nombre': 'Nueva', 'color': '#123456'}, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(respuesta.data['total_patologias'], 0)
        respuesta = self.client.post('/api/foro/temas/', {'nombre': 'Nuevo tema'}, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(respuesta.data['total_publicaciones'], 0)

    def test_los_totales_y_la_portada_son_correctos(self):
        Comentario, ImagenPublicacion, Publicacion, TemaForo = self.modelos
        tema = TemaForo.objects.create(nombre='Con datos')
        publicacion = Publicacion.objects.create(autor=self.usuario, titulo='t', contenido='c', tema=tema)
        for i in range(3):
            Comentario.objects.create(publicacion=publicacion, autor=self.usuario, contenido=f'c{i}')
        primera = ImagenPublicacion.objects.create(publicacion=publicacion, imagen='foro/primera.png')
        ImagenPublicacion.objects.create(publicacion=publicacion, imagen='foro/segunda.png')
        fila = self.client.get('/api/foro/publicaciones/').data['results'][0]
        self.assertEqual((fila['total_comentarios'], fila['total_imagenes']), (3, 2))
        self.assertTrue(fila['portada'].endswith(primera.imagen.url))
        temas = {t['nombre']: t['total_publicaciones'] for t in self.client.get('/api/foro/temas/').data['results']}
        self.assertEqual(temas['Con datos'], 1)

    def test_los_listados_conservan_su_orden(self):
        # Con annotate(Count), Django ignora Meta.ordering si no se indica el orden.
        Comentario, ImagenPublicacion, Publicacion, TemaForo = self.modelos
        for nombre in ['Zeta', 'Alfa', 'Media']:
            Categoria.objects.create(nombre=nombre)
            TemaForo.objects.create(nombre=nombre)
        normal = Publicacion.objects.create(autor=self.usuario, titulo='Normal', contenido='c')
        Publicacion.objects.create(autor=self.usuario, titulo='Fijada', contenido='c', fijado=True)
        Publicacion.objects.create(autor=self.usuario, titulo='Reciente', contenido='c')
        Comentario.objects.create(publicacion=normal, autor=self.usuario, contenido='c')
        # Se crean en el mismo instante: se hace "Normal" un día más antigua para que no empaten.
        from datetime import timedelta
        from django.utils import timezone
        Publicacion.objects.filter(id=normal.id).update(fecha_creacion=timezone.now() - timedelta(days=1))
        nombres = lambda url, campo: [f[campo] for f in self.client.get(url).data['results']]
        self.assertEqual(nombres('/api/categorias/', 'nombre'), ['Alfa', 'Media', 'Zeta'])
        self.assertEqual(nombres('/api/foro/temas/', 'nombre'), ['Alfa', 'Media', 'Zeta'])
        self.assertEqual(nombres('/api/foro/publicaciones/', 'titulo'), ['Fijada', 'Reciente', 'Normal'])


class TamanoDePaginaTests(APITestCase):
    """
    Los listados vienen de 20 en 20. Los menús desplegables del frontend (patologías,
    categorías, temas) necesitan todos los elementos: con ?page_size= se puede pedir
    una página más grande, hasta un máximo de 1000.
    """

    def setUp(self):
        usuario = Usuario.objects.create_user(username='paginas', password='x', rol=Usuario.Rol.PATOLOGO)
        self.client.force_authenticate(usuario)
        for i in range(25):
            Patologia.objects.create(nombre=f'Patología {i:02d}')

    def test_por_defecto_trae_20(self):
        datos = self.client.get('/api/patologias/').data
        self.assertEqual((datos['count'], len(datos['results'])), (25, 20))

    def test_page_size_permite_traer_todas(self):
        datos = self.client.get('/api/patologias/', {'page_size': 100}).data
        self.assertEqual(len(datos['results']), 25)
        self.assertIsNone(datos['next'])

    def test_page_size_tiene_un_maximo(self):
        from django.conf import settings
        from django.utils.module_loading import import_string
        paginacion = import_string(settings.REST_FRAMEWORK['DEFAULT_PAGINATION_CLASS'])
        self.assertEqual(paginacion.max_page_size, 1000)


class PatologiasActivasTests(APITestCase):
    """
    Decisión D-4 (auditoría M-5): una patología se puede desactivar en lugar de
    borrarse, y al crear informes solo se ofrecen las activas.
    """

    def setUp(self):
        usuario = Usuario.objects.create_user(username='activas', password='x', rol=Usuario.Rol.PATOLOGO)
        self.client.force_authenticate(usuario)
        self.activa = Patologia.objects.create(nombre='Activa')
        self.inactiva = Patologia.objects.create(nombre='Inactiva', activa=False)

    def nombres(self, **params):
        return [p['nombre'] for p in self.client.get('/api/patologias/', params).data['results']]

    def test_filtro_activa(self):
        self.assertEqual(self.nombres(activa='true'), ['Activa'])
        self.assertEqual(self.nombres(activa='false'), ['Inactiva'])

    def test_sin_filtro_devuelve_todas(self):
        # Al editar un informe viejo hace falta ver también su patología inactiva.
        self.assertEqual(self.nombres(), ['Activa', 'Inactiva'])

    def test_se_puede_desactivar_una_patologia(self):
        respuesta = self.client.patch(f'/api/patologias/{self.activa.id}/', {'activa': False}, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.activa.refresh_from_db()
        self.assertFalse(self.activa.activa)


class NumeroPeticionTests(APITestCase):
    """
    Decisión D-7 (docs/decisiones.md): al crear un informe, el sistema le asigna
    un número de petición P-AÑO-NNNNN, que reemplaza al número de caso que
    escribía el usuario. Se agrega un número de orden externo opcional.
    """

    def setUp(self):
        self.patologo = Usuario.objects.create_user(
            username='patologo_np', password='ClaveSegura-2026', rol=Usuario.Rol.PATOLOGO,
        )
        self.patologia = Patologia.objects.create(nombre='Patología número de petición')
        self.paciente = paciente_ficticio()
        self.client.force_authenticate(self.patologo)
        self.anio = timezone.localdate().year

    def crear(self, **extra):
        return self.client.post(
            '/api/informes/',
            {'patologia': self.patologia.id, 'paciente': self.paciente.id, 'datos_ingresados': {}, **extra},
            format='json',
        )

    def numero(self, consecutivo, anio=None):
        return f'P-{anio or self.anio}-{consecutivo:05d}'

    def test_al_crear_se_asigna_el_numero_con_el_formato(self):
        respuesta = self.crear()
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED, respuesta.data)
        self.assertEqual(respuesta.data['numero_peticion'], self.numero(1))

    def test_los_numeros_son_consecutivos(self):
        numeros = [self.crear().data['numero_peticion'] for _ in range(3)]
        self.assertEqual(numeros, [self.numero(1), self.numero(2), self.numero(3)])

    def test_el_consecutivo_vuelve_a_empezar_cada_anio(self):
        with mock.patch('django.utils.timezone.localdate', return_value=date(2026, 12, 31)):
            diciembre = [self.crear().data['numero_peticion'] for _ in range(2)]
        with mock.patch('django.utils.timezone.localdate', return_value=date(2027, 1, 1)):
            enero = self.crear().data['numero_peticion']
        self.assertEqual(diciembre, ['P-2026-00001', 'P-2026-00002'])
        self.assertEqual(enero, 'P-2027-00001')

    def test_el_cliente_no_puede_elegir_ni_cambiar_el_numero(self):
        respuesta = self.crear(numero_peticion='P-1999-99999')
        self.assertEqual(respuesta.data['numero_peticion'], self.numero(1))
        id_informe = respuesta.data['id']
        cambio = self.client.patch(
            f'/api/informes/{id_informe}/', {'numero_peticion': 'P-1999-00001'}, format='json',
        )
        self.assertEqual(cambio.status_code, status.HTTP_200_OK)
        self.assertEqual(Informe.objects.get(id=id_informe).numero_peticion, self.numero(1))

    def test_ya_no_existe_el_numero_de_caso(self):
        respuesta = self.crear()
        self.assertNotIn('numero_caso', respuesta.data)
        fila = self.client.get('/api/informes/').data['results'][0]
        self.assertEqual(fila['numero_peticion'], self.numero(1))
        self.assertNotIn('numero_caso', fila)

    def test_borrar_un_borrador_no_reutiliza_su_numero(self):
        primero = self.crear()
        self.client.delete(f"/api/informes/{primero.data['id']}/")
        self.assertEqual(self.crear().data['numero_peticion'], self.numero(2))

    def test_los_informes_creados_sin_la_api_tambien_se_numeran(self):
        # /admin/, seed_data y las pruebas crean informes con el ORM.
        informe = Informe.objects.create(patologia=self.patologia, autor=self.patologo)
        self.assertEqual(informe.numero_peticion, self.numero(1))

    def test_la_base_de_datos_rechaza_un_numero_repetido(self):
        primero = Informe.objects.create(patologia=self.patologia, autor=self.patologo)
        segundo = Informe.objects.create(patologia=self.patologia, autor=self.patologo)
        segundo.numero_peticion = primero.numero_peticion
        with self.assertRaises(IntegrityError), transaction.atomic():
            segundo.save()

    def test_el_numero_de_orden_externa_es_opcional_y_se_puede_repetir(self):
        sin_orden = self.crear()
        self.assertEqual(sin_orden.data['numero_orden_externa'], '')
        # Dos instituciones distintas pueden usar el mismo número de orden.
        for _ in range(2):
            con_orden = self.crear(numero_orden_externa='ORD-123')
            self.assertEqual(con_orden.status_code, status.HTTP_201_CREATED, con_orden.data)
            self.assertEqual(con_orden.data['numero_orden_externa'], 'ORD-123')

    def test_se_busca_por_numero_de_peticion_y_de_orden_externa(self):
        self.crear()
        self.crear(numero_orden_externa='HOSP-77')
        por_peticion = self.client.get('/api/informes/', {'q': self.numero(1)}).data
        self.assertEqual([i['numero_peticion'] for i in por_peticion['results']], [self.numero(1)])
        por_orden = self.client.get('/api/informes/', {'q': 'HOSP-77'}).data
        self.assertEqual([i['numero_peticion'] for i in por_orden['results']], [self.numero(2)])

    def test_el_pdf_lleva_el_numero_de_peticion(self):
        from reportlab.platypus import Table
        id_informe = self.crear().data['id']
        with mock.patch('informes.utils.Table', wraps=Table) as espia:
            respuesta = self.client.get(f'/api/informes/{id_informe}/pdf/')
        self.assertEqual(
            respuesta['Content-Disposition'], f'attachment; filename="informe_{self.numero(1)}.pdf"',
        )
        celdas = str([llamada.args[0] for llamada in espia.call_args_list])
        self.assertIn(self.numero(1), celdas)


class NumeroPeticionConcurrenciaTests(TransactionTestCase):
    """
    Decisión D-7: el número de petición no se repite aunque varios usuarios creen
    informes al mismo tiempo. Cada hilo usa su propia conexión a la base de datos,
    como dos peticiones simultáneas al servidor.
    """

    HILOS = 10

    def test_informes_creados_a_la_vez_reciben_numeros_distintos(self):
        patologo = Usuario.objects.create_user(
            username='patologo_concurrencia', password='ClaveSegura-2026', rol=Usuario.Rol.PATOLOGO,
        )
        patologia = Patologia.objects.create(nombre='Patología concurrencia')
        paciente = paciente_ficticio()
        barrera = threading.Barrier(self.HILOS)
        numeros, errores = [], []

        def crear_informe():
            try:
                cliente = APIClient()
                cliente.force_authenticate(patologo)
                barrera.wait()  # todos los hilos envían su petición al mismo tiempo
                respuesta = cliente.post(
                    '/api/informes/',
                    {'patologia': patologia.id, 'paciente': paciente.id, 'datos_ingresados': {}},
                    format='json',
                )
                if respuesta.status_code == status.HTTP_201_CREATED:
                    numeros.append(respuesta.data['numero_peticion'])
                else:
                    errores.append((respuesta.status_code, respuesta.data))
            except Exception as error:  # cualquier fallo de un hilo debe verse en la prueba
                errores.append(repr(error))
            finally:
                connection.close()

        hilos = [threading.Thread(target=crear_informe) for _ in range(self.HILOS)]
        for hilo in hilos:
            hilo.start()
        for hilo in hilos:
            hilo.join()

        self.assertEqual(errores, [])
        anio = timezone.localdate().year
        self.assertEqual(sorted(numeros), [f'P-{anio}-{n:05d}' for n in range(1, self.HILOS + 1)])


class MigracionNumeroPeticionTests(TransactionTestCase):
    """
    La migración de datos de la etapa 1 numera los informes que ya existían: en
    orden de creación, por año de creación (hora de Bogotá), y deja el contador
    listo para que el siguiente informe continúe la numeración.
    """

    # accounts también vuelve atrás: con la columna registro_medico (accounts 0002, NOT NULL)
    # el modelo histórico de Usuario, que no la conoce, no podría crear usuarios.
    ANTES = [('informes', '0003_quitar_campos_requeridos'), ('accounts', '0001_initial')]

    def test_numera_los_informes_existentes(self):
        executor = MigrationExecutor(connection)
        executor.migrate(self.ANTES)
        modelos = executor.loader.project_state(self.ANTES).apps
        UsuarioAntiguo = modelos.get_model('accounts', 'Usuario')
        PatologiaAntigua = modelos.get_model('informes', 'Patologia')
        InformeAntiguo = modelos.get_model('informes', 'Informe')

        autor = UsuarioAntiguo.objects.create(username='autor_migracion')
        patologia = PatologiaAntigua.objects.create(nombre='Patología migración')
        # 31/12/2025 23:30 en Bogotá ya es 1/1/2026 en UTC: debe contar como 2025.
        fechas = {
            'NOCHEVIEJA': timezone.make_aware(datetime(2025, 12, 31, 23, 30)),
            'MARZO': timezone.make_aware(datetime(2026, 3, 1, 9, 0)),
            'FEBRERO': timezone.make_aware(datetime(2026, 2, 1, 9, 0)),
        }
        ids = {}
        for caso, fecha in fechas.items():
            informe = InformeAntiguo.objects.create(numero_caso=caso, patologia=patologia, autor=autor)
            InformeAntiguo.objects.filter(id=informe.id).update(fecha_creacion=fecha)
            ids[caso] = informe.id

        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(executor.loader.graph.leaf_nodes())

        numeros = {caso: Informe.objects.get(id=id_informe).numero_peticion for caso, id_informe in ids.items()}
        self.assertEqual(numeros, {
            'NOCHEVIEJA': 'P-2025-00001',
            'FEBRERO': 'P-2026-00001',
            'MARZO': 'P-2026-00002',
        })
        # El siguiente informe de 2026 continúa la numeración.
        with mock.patch('django.utils.timezone.localdate', return_value=date(2026, 10, 4)):
            nuevo = Informe.objects.create(
                patologia=Patologia.objects.get(id=patologia.id), autor=Usuario.objects.get(id=autor.id),
            )
        self.assertEqual(nuevo.numero_peticion, 'P-2026-00003')


class OpcionesTests(APITestCase):
    """
    Informe v2, etapa 2 (docs/propuesta-informe-v2.md, sección 3.3): GET /api/opciones/
    devuelve las listas fijas (sexo, tipo de documento, tipo de estudio) sacadas de
    los TextChoices del backend, para que el frontend no tenga que copiarlas.
    """

    def setUp(self):
        self.auditor = Usuario.objects.create_user(username='opciones', password='x', rol=Usuario.Rol.AUDITOR)

    def opciones(self):
        self.client.force_authenticate(self.auditor)
        respuesta = self.client.get('/api/opciones/')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        return respuesta.data

    def test_cualquier_rol_las_lee(self):
        self.assertEqual(set(self.opciones()), {'sexos', 'tipos_documento', 'tipos_estudio'})

    def test_sexos(self):
        # Etiqueta "Sexo" con estas tres opciones (P-3).
        self.assertEqual(self.opciones()['sexos'], [
            {'valor': 'femenino', 'etiqueta': 'Femenino'},
            {'valor': 'masculino', 'etiqueta': 'Masculino'},
            {'valor': 'indeterminado', 'etiqueta': 'Indeterminado'},
        ])

    def test_tipos_documento(self):
        tipos = self.opciones()['tipos_documento']
        self.assertEqual([t['valor'] for t in tipos], ['CC', 'TI', 'RC', 'CE', 'PA', 'PPT', 'MS', 'AS'])
        self.assertEqual(tipos[0], {'valor': 'CC', 'etiqueta': 'Cédula de ciudadanía'})

    def test_tipos_estudio(self):
        tipos = self.opciones()['tipos_estudio']
        self.assertEqual([t['etiqueta'] for t in tipos], [
            'Histología',
            'Citología no ginecológica',
            'Citología cérvico-vaginal',
            'Inmunohistoquímica',
            'Estudio intraoperatorio por congelación',
            'Revisión de láminas (segunda opinión)',
        ])
        self.assertEqual(tipos[0]['valor'], 'histologia')

    def test_requiere_sesion(self):
        self.assertEqual(self.client.get('/api/opciones/').status_code, status.HTTP_401_UNAUTHORIZED)

    def test_es_solo_lectura(self):
        self.client.force_authenticate(self.auditor)
        self.assertEqual(self.client.post('/api/opciones/', {}).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class CatalogoServiciosTests(APITestCase):
    """
    Informe v2, etapa 2 (sección 3.2): catálogo de servicios. Lo administran
    patólogos y admin (decisión D-11); el auditor solo lee. Se desactiva en lugar
    de borrarse (D-4) y se filtra con ?activo=.
    """

    URL = '/api/servicios/'

    def setUp(self):
        self.patologo = Usuario.objects.create_user(username='serv_pat', password='x', rol=Usuario.Rol.PATOLOGO)
        self.auditor = Usuario.objects.create_user(username='serv_aud', password='x', rol=Usuario.Rol.AUDITOR)

    def crear(self, nombre, usuario=None, **extra):
        self.client.force_authenticate(usuario or self.patologo)
        return self.client.post(self.URL, {'nombre': nombre, **extra}, format='json')

    def nombres(self, **params):
        return [s['nombre'] for s in self.client.get(self.URL, params).data['results']]

    def test_patologo_crea_y_auditor_lee(self):
        self.assertEqual(self.crear('Urgencias').status_code, status.HTTP_201_CREATED)
        self.client.force_authenticate(self.auditor)
        self.assertEqual(self.nombres(), ['Urgencias'])

    def test_auditor_no_crea(self):
        self.assertEqual(self.crear('Urgencias', usuario=self.auditor).status_code, status.HTTP_403_FORBIDDEN)

    def test_filtro_activo(self):
        self.crear('Urgencias')
        self.crear('Cirugía', activo=False)
        self.assertEqual(self.nombres(activo='true'), ['Urgencias'])
        self.assertEqual(self.nombres(activo='false'), ['Cirugía'])
        self.assertEqual(self.nombres(), ['Cirugía', 'Urgencias'])

    def test_se_puede_desactivar(self):
        servicio_id = self.crear('Urgencias').data['id']
        respuesta = self.client.patch(f'{self.URL}{servicio_id}/', {'activo': False}, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertFalse(respuesta.data['activo'])

    def test_nombre_repetido_sin_importar_mayusculas_ni_espacios(self):
        self.crear('Urgencias')
        respuesta = self.crear('  urgencias ')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('nombre', respuesta.data)

    def test_seed_data_carga_los_servicios(self):
        from io import StringIO
        from django.core.management import call_command
        call_command('seed_data', stdout=StringIO())
        call_command('seed_data', stdout=StringIO())  # dos veces: no duplica
        self.client.force_authenticate(self.auditor)
        self.assertEqual(sorted(self.nombres()), sorted([
            'Consulta externa', 'Urgencias', 'Hospitalización', 'Cirugía',
            'Unidad de cuidados intensivos', 'Ginecología', 'Dermatología',
        ]))


class DatosSolicitudTests(APITestCase):
    """
    Informe v2, etapa 4 (docs/propuesta-informe-v2.md, secciones 3.4 y 4): el
    informe guarda el paciente y los datos de la solicitud (médico tratante,
    fecha de ingreso, EPS, servicio, estudios solicitados y tipo de estudio).
    Solo datos ficticios (sección 8).
    """

    URL = '/api/informes/'

    def setUp(self):
        self.patologo = Usuario.objects.create_user(
            username='patologo_solicitud', password='ClaveSegura-2026', rol=Usuario.Rol.PATOLOGO,
        )
        self.client.force_authenticate(self.patologo)
        self.patologia = Patologia.objects.create(nombre='Patología solicitud')
        self.eps = EPS.objects.create(nombre='EPS Ficticia')
        self.servicio = Servicio.objects.create(nombre='Urgencias')
        self.paciente = paciente_ficticio(eps=self.eps)

    def crear(self, **extra):
        cuerpo = {'patologia': self.patologia.id, 'paciente': self.paciente.id, 'datos_ingresados': {}, **extra}
        return self.client.post(self.URL, cuerpo, format='json')

    # --- Paciente ---

    def test_paciente_es_obligatorio_al_crear(self):
        respuesta = self.client.post(self.URL, {'patologia': self.patologia.id, 'datos_ingresados': {}}, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('paciente', respuesta.data)
        self.assertEqual(Informe.objects.count(), 0)

    def test_no_se_puede_quitar_el_paciente(self):
        informe_id = self.crear().data['id']
        respuesta = self.client.patch(f'{self.URL}{informe_id}/', {'paciente': None}, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('paciente', respuesta.data)

    def test_informe_antiguo_sin_paciente_se_puede_editar_y_luego_asignarle_uno(self):
        # Los informes de antes de la etapa 4 quedan sin paciente (migración 0008).
        antiguo = Informe.objects.create(patologia=self.patologia, autor=self.patologo)
        detalle = self.client.get(f'{self.URL}{antiguo.id}/').data
        self.assertIsNone(detalle['paciente'])
        self.assertIsNone(detalle['paciente_datos'])
        respuesta = self.client.patch(f'{self.URL}{antiguo.id}/', {'tipo_muestra': 'Biopsia'}, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK, respuesta.data)
        respuesta = self.client.patch(f'{self.URL}{antiguo.id}/', {'paciente': self.paciente.id}, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK, respuesta.data)
        self.assertEqual(respuesta.data['paciente'], self.paciente.id)

    def test_detalle_devuelve_datos_del_paciente_con_la_edad_a_la_fecha_de_ingreso(self):
        # Nació el 5/10/1980: el 4/10/2026 tiene 45 años, aunque hoy sea 2030.
        informe_id = self.crear(fecha_ingreso='2026-10-04').data['id']
        with mock.patch('django.utils.timezone.localdate', return_value=date(2030, 1, 1)):
            datos = self.client.get(f'{self.URL}{informe_id}/').data['paciente_datos']
        self.assertEqual(datos, {
            'id': self.paciente.id,
            'nombre_completo': 'Paciente Ficticio Uno',
            'tipo_documento': 'CC',
            'numero_documento': 'PRUEBA0001',
            'fecha_nacimiento': '1980-10-05',
            'sexo': 'femenino',
            'edad': '45 años',
        })

    # --- Datos de la solicitud ---

    def test_guarda_los_datos_de_la_solicitud(self):
        respuesta = self.crear(
            medico_tratante='Médico Ficticio', fecha_ingreso='2026-10-01', eps=self.eps.id,
            servicio=self.servicio.id, estudios_solicitados='Biopsia de piel',
            tipo_estudio='citologia_no_ginecologica',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED, respuesta.data)
        datos = self.client.get(f"{self.URL}{respuesta.data['id']}/").data
        self.assertEqual(datos['medico_tratante'], 'Médico Ficticio')
        self.assertEqual(datos['fecha_ingreso'], '2026-10-01')
        self.assertEqual((datos['eps'], datos['eps_nombre']), (self.eps.id, 'EPS Ficticia'))
        self.assertEqual((datos['servicio'], datos['servicio_nombre']), (self.servicio.id, 'Urgencias'))
        self.assertEqual(datos['estudios_solicitados'], 'Biopsia de piel')
        self.assertEqual(datos['tipo_estudio'], 'citologia_no_ginecologica')

    def test_valores_por_defecto(self):
        with mock.patch('django.utils.timezone.localdate', return_value=date(2026, 10, 4)):
            datos = self.crear().data
        self.assertEqual(datos['fecha_ingreso'], '2026-10-04')
        self.assertEqual(datos['tipo_estudio'], 'histologia')
        self.assertIsNone(datos['servicio'])
        self.assertEqual(datos['medico_tratante'], '')

    def test_tipo_de_estudio_invalido(self):
        respuesta = self.crear(tipo_estudio='astrologia')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('tipo_estudio', respuesta.data)

    def test_fecha_de_ingreso_en_el_futuro(self):
        manana = timezone.localdate() + timedelta(days=1)
        respuesta = self.crear(fecha_ingreso=manana.isoformat())
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('fecha_ingreso', respuesta.data)

    def test_fecha_de_ingreso_anterior_al_nacimiento(self):
        respuesta = self.crear(fecha_ingreso='1980-10-04')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('fecha_ingreso', respuesta.data)

    def test_fecha_de_ingreso_se_valida_al_cambiar_de_paciente(self):
        informe_id = self.crear(fecha_ingreso='2000-01-01').data['id']
        joven = paciente_ficticio('PRUEBA0002', fecha_nacimiento=date(2010, 1, 1))
        respuesta = self.client.patch(f'{self.URL}{informe_id}/', {'paciente': joven.id}, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('fecha_ingreso', respuesta.data)

    # --- EPS: la del momento del estudio ---

    def test_si_no_se_envia_la_eps_se_copia_la_del_paciente(self):
        datos = self.crear().data
        self.assertEqual(datos['eps'], self.eps.id)

    def test_eps_enviada_vacia_queda_vacia(self):
        datos = self.crear(eps=None).data
        self.assertIsNone(datos['eps'])

    def test_no_se_copia_una_eps_desactivada_del_paciente(self):
        EPS.objects.filter(pk=self.eps.pk).update(activa=False)
        respuesta = self.crear()
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED, respuesta.data)
        self.assertIsNone(respuesta.data['eps'])

    def test_cambiar_la_eps_del_paciente_no_cambia_la_del_informe(self):
        informe_id = self.crear().data['id']
        otra = EPS.objects.create(nombre='Otra')
        Paciente.objects.filter(pk=self.paciente.pk).update(eps=otra)
        self.assertEqual(self.client.get(f'{self.URL}{informe_id}/').data['eps_nombre'], 'EPS Ficticia')

    def test_eps_o_servicio_desactivados_no_se_asignan(self):
        eps_inactiva = EPS.objects.create(nombre='EPS Liquidada', activa=False)
        servicio_inactivo = Servicio.objects.create(nombre='Cerrado', activo=False)
        respuesta = self.crear(eps=eps_inactiva.id, servicio=servicio_inactivo.id)
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('eps', respuesta.data)
        self.assertIn('servicio', respuesta.data)

    def test_informe_conserva_eps_y_servicio_aunque_se_desactiven(self):
        informe_id = self.crear(servicio=self.servicio.id).data['id']
        EPS.objects.filter(pk=self.eps.pk).update(activa=False)
        Servicio.objects.filter(pk=self.servicio.pk).update(activo=False)
        cuerpo = {
            'patologia': self.patologia.id, 'paciente': self.paciente.id, 'datos_ingresados': {},
            'eps': self.eps.id, 'servicio': self.servicio.id, 'medico_tratante': 'Corregido',
        }
        respuesta = self.client.put(f'{self.URL}{informe_id}/', cuerpo, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK, respuesta.data)

    # --- Listado, búsqueda y filtro ---

    def test_listado_incluye_paciente_y_tipo_de_estudio(self):
        self.crear(tipo_estudio='inmunohistoquimica')
        Informe.objects.create(patologia=self.patologia, autor=self.patologo)  # antiguo, sin paciente
        filas = self.client.get(self.URL).data['results']
        self.assertCountEqual(
            [(f['paciente_nombre'], f['paciente_documento'], f['tipo_estudio']) for f in filas],
            [(None, None, 'histologia'), ('Paciente Ficticio Uno', 'CC PRUEBA0001', 'inmunohistoquimica')],
        )

    def test_busqueda_por_nombre_y_documento_del_paciente(self):
        self.crear()
        otro = paciente_ficticio('PRUEBA0002', nombres='Prueba', apellidos='Apellido Dos')
        self.crear(paciente=otro.id)

        def documentos(q):
            return [f['paciente_documento'] for f in self.client.get(self.URL, {'q': q}).data['results']]

        self.assertEqual(documentos('PRUEBA0002'), ['CC PRUEBA0002'])
        self.assertEqual(documentos('ficticio uno'), ['CC PRUEBA0001'])  # nombres + apellidos
        self.assertEqual(documentos('apellido'), ['CC PRUEBA0002'])
        self.assertEqual(len(documentos('prueba')), 2)

    def test_filtro_por_paciente(self):
        self.crear()
        otro = paciente_ficticio('PRUEBA0002')
        self.crear(paciente=otro.id)
        filas = self.client.get(self.URL, {'paciente': otro.id}).data['results']
        self.assertEqual([f['paciente_documento'] for f in filas], ['CC PRUEBA0002'])


class BorrarCatalogosEnUsoPorInformesTests(APITestCase):
    """Etapa 4: una EPS o un servicio que usa un informe no se borra (PROTECT); se responde 400 (D-4)."""

    def setUp(self):
        self.admin = Usuario.objects.create_user(username='cat_admin', password='x', rol=Usuario.Rol.ADMIN)
        self.client.force_authenticate(self.admin)
        self.eps = EPS.objects.create(nombre='EPS en informe')
        self.servicio = Servicio.objects.create(nombre='Servicio en informe')
        Informe.objects.create(
            patologia=Patologia.objects.create(nombre='Patología catálogos'), autor=self.admin,
            eps=self.eps, servicio=self.servicio,
        )

    def test_borrar_servicio_en_uso_responde_400(self):
        respuesta = self.client.delete(f'/api/servicios/{self.servicio.id}/')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('1 informe', respuesta.data['detail'])
        self.assertIn('Desactívelo', respuesta.data['detail'])
        self.assertTrue(Servicio.objects.filter(pk=self.servicio.id).exists())

    def test_borrar_eps_en_uso_por_un_informe_responde_400(self):
        respuesta = self.client.delete(f'/api/pacientes/eps/{self.eps.id}/')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('1 informe', respuesta.data['detail'])
        self.assertIn('Desactívela', respuesta.data['detail'])
        self.assertTrue(EPS.objects.filter(pk=self.eps.id).exists())

    def test_borrar_servicio_sin_uso_sigue_funcionando(self):
        libre = Servicio.objects.create(nombre='Sin uso')
        self.assertEqual(self.client.delete(f'/api/servicios/{libre.id}/').status_code, status.HTTP_204_NO_CONTENT)


class ConsultasListadoInformesTests(APITestCase):
    """Auditoría M-4 aplicada a la etapa 4: los listados de informes no hacen una consulta por fila."""

    def setUp(self):
        self.usuario = Usuario.objects.create_user(username='consultas_inf', password='x', rol=Usuario.Rol.ADMIN)
        self.client.force_authenticate(self.usuario)
        self.patologia = Patologia.objects.create(nombre='Patología consultas')
        self.paciente = paciente_ficticio('PRUEBA9999')

    def crear_informes(self, desde, hasta):
        for i in range(desde, hasta):
            eps = EPS.objects.create(nombre=f'EPS {i}')
            servicio = Servicio.objects.create(nombre=f'Servicio {i}')
            # Uno del paciente fijo (para su historial) y otro de un paciente nuevo.
            for paciente in (self.paciente, paciente_ficticio(f'PRUEBA{i:04d}', eps=eps)):
                Informe.objects.create(
                    patologia=self.patologia, autor=self.usuario, eps=eps, servicio=servicio, paciente=paciente,
                )

    def contar(self, url):
        from django.test.utils import CaptureQueriesContext
        with CaptureQueriesContext(connection) as consultas:
            self.assertEqual(self.client.get(url).status_code, status.HTTP_200_OK)
        return len(consultas)

    def test_las_consultas_no_crecen_con_los_informes(self):
        urls = ['/api/informes/', f'/api/pacientes/{self.paciente.id}/informes/']
        self.crear_informes(0, 3)
        con_3 = [self.contar(url) for url in urls]
        self.crear_informes(3, 10)
        self.assertEqual([self.contar(url) for url in urls], con_3)


class ContenidoInformeTests(APITestCase):
    """
    Informe v2, etapa 5 (docs/propuesta-informe-v2.md, secciones 3.4 y 3.6): el
    informe tiene descripción microscópica, comentarios (antes `notas`, P-5) y
    una lista de diagnósticos con código CIE-10 opcional. Solo datos ficticios.
    """

    URL = '/api/informes/'

    def setUp(self):
        self.patologo = Usuario.objects.create_user(
            username='patologo_contenido', password='ClaveSegura-2026', rol=Usuario.Rol.PATOLOGO,
        )
        self.client.force_authenticate(self.patologo)
        self.patologia = Patologia.objects.create(nombre='Patología contenido')
        self.paciente = paciente_ficticio()

    def crear(self, **extra):
        cuerpo = {'patologia': self.patologia.id, 'paciente': self.paciente.id, 'datos_ingresados': {}, **extra}
        return self.client.post(self.URL, cuerpo, format='json')

    def url(self, informe_id):
        return f'{self.URL}{informe_id}/'

    def diagnosticos(self, informe_id):
        return [
            (d['descripcion'], d['codigo_cie10'])
            for d in self.client.get(self.url(informe_id)).data['diagnosticos']
        ]

    # --- Descripción microscópica y comentarios ---

    def test_guarda_y_devuelve_la_descripcion_microscopica(self):
        respuesta = self.crear(descripcion_microscopica='Proliferación de células basaloides en nidos.')
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED, respuesta.data)
        detalle = self.client.get(self.url(respuesta.data['id'])).data
        self.assertEqual(detalle['descripcion_microscopica'], 'Proliferación de células basaloides en nidos.')

    def test_comentarios_reemplaza_a_notas(self):
        respuesta = self.crear(comentarios='Se sugiere correlación clínica.', notas='ignorado')
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED, respuesta.data)
        detalle = self.client.get(self.url(respuesta.data['id'])).data
        self.assertEqual(detalle['comentarios'], 'Se sugiere correlación clínica.')
        self.assertNotIn('notas', detalle)

    # --- Diagnósticos ---

    def test_guarda_los_diagnosticos_en_el_orden_enviado(self):
        respuesta = self.crear(diagnosticos=[
            {'descripcion': 'Carcinoma basocelular nodular', 'codigo_cie10': 'C44.3'},
            {'descripcion': 'Márgenes libres de lesión', 'codigo_cie10': ''},
        ])
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED, respuesta.data)
        self.assertEqual(self.diagnosticos(respuesta.data['id']), [
            ('Carcinoma basocelular nodular', 'C44.3'),
            ('Márgenes libres de lesión', ''),
        ])

    def test_el_codigo_cie10_es_opcional(self):
        respuesta = self.crear(diagnosticos=[{'descripcion': 'Dermatitis crónica inespecífica'}])
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED, respuesta.data)
        self.assertEqual(self.diagnosticos(respuesta.data['id']), [('Dermatitis crónica inespecífica', '')])

    def test_un_informe_sin_diagnosticos_se_puede_guardar_como_borrador(self):
        respuesta = self.crear()
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED, respuesta.data)
        self.assertEqual(respuesta.data['diagnosticos'], [])

    def test_put_reemplaza_la_lista_de_diagnosticos(self):
        informe_id = self.crear(diagnosticos=[
            {'descripcion': 'Primero', 'codigo_cie10': 'C44.3'},
            {'descripcion': 'Segundo'},
        ]).data['id']
        cuerpo = {
            'patologia': self.patologia.id, 'paciente': self.paciente.id, 'datos_ingresados': {},
            'diagnosticos': [{'descripcion': 'Segundo'}, {'descripcion': 'Tercero', 'codigo_cie10': 'D22.5'}],
        }
        respuesta = self.client.put(self.url(informe_id), cuerpo, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK, respuesta.data)
        self.assertEqual(self.diagnosticos(informe_id), [('Segundo', ''), ('Tercero', 'D22.5')])

    def test_patch_sin_diagnosticos_los_conserva(self):
        informe_id = self.crear(diagnosticos=[{'descripcion': 'Nevus intradérmico', 'codigo_cie10': 'D22.5'}]).data['id']
        respuesta = self.client.patch(self.url(informe_id), {'comentarios': 'Revisado'}, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK, respuesta.data)
        self.assertEqual(self.diagnosticos(informe_id), [('Nevus intradérmico', 'D22.5')])

    def test_una_lista_vacia_quita_todos_los_diagnosticos(self):
        informe_id = self.crear(diagnosticos=[{'descripcion': 'Nevus intradérmico'}]).data['id']
        respuesta = self.client.patch(self.url(informe_id), {'diagnosticos': []}, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK, respuesta.data)
        self.assertEqual(self.diagnosticos(informe_id), [])

    def test_el_codigo_cie10_se_normaliza(self):
        respuesta = self.crear(diagnosticos=[
            {'descripcion': 'Sin punto', 'codigo_cie10': 'c443'},
            {'descripcion': 'Con espacios y minúsculas', 'codigo_cie10': ' d22.5 '},
            {'descripcion': 'Solo categoría', 'codigo_cie10': 'C50'},
            {'descripcion': 'Subcategoría de dos caracteres', 'codigo_cie10': 'M8090'},
        ])
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED, respuesta.data)
        self.assertEqual([codigo for _, codigo in self.diagnosticos(respuesta.data['id'])],
                         ['C44.3', 'D22.5', 'C50', 'M80.90'])

    def test_rechaza_un_codigo_cie10_invalido(self):
        for codigo in ['44.3', 'CC4', 'C4', 'C44.123', 'C44-3', 'Ñ44']:
            with self.subTest(codigo=codigo):
                respuesta = self.crear(diagnosticos=[{'descripcion': 'Diagnóstico', 'codigo_cie10': codigo}])
                self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn('diagnosticos', respuesta.data)
        self.assertEqual(Informe.objects.count(), 0)

    def test_rechaza_un_diagnostico_sin_descripcion(self):
        for descripcion in ['', '   ']:
            with self.subTest(descripcion=descripcion):
                respuesta = self.crear(diagnosticos=[{'descripcion': descripcion, 'codigo_cie10': 'C44.3'}])
                self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn('diagnosticos', respuesta.data)
        self.assertEqual(Informe.objects.count(), 0)

    def test_maximo_20_diagnosticos(self):
        lista = [{'descripcion': f'Diagnóstico {i}'} for i in range(21)]
        respuesta = self.crear(diagnosticos=lista)
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('diagnosticos', respuesta.data)
        self.assertEqual(self.crear(diagnosticos=lista[:20]).status_code, status.HTTP_201_CREATED)

    def test_un_error_no_borra_los_diagnosticos_anteriores(self):
        informe_id = self.crear(diagnosticos=[{'descripcion': 'Nevus intradérmico'}]).data['id']
        respuesta = self.client.patch(
            self.url(informe_id), {'diagnosticos': [{'descripcion': 'Otro', 'codigo_cie10': 'XYZ'}]}, format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.diagnosticos(informe_id), [('Nevus intradérmico', '')])

    def test_un_informe_finalizado_no_cambia_sus_diagnosticos(self):
        # Decisión D-3: tampoco se modifican los diagnósticos de un informe finalizado.
        informe_id = self.crear(diagnosticos=[{'descripcion': 'Nevus intradérmico'}]).data['id']
        Informe.objects.filter(id=informe_id).update(estado=Informe.Estado.FINALIZADO)
        respuesta = self.client.patch(self.url(informe_id), {'diagnosticos': []}, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.diagnosticos(informe_id), [('Nevus intradérmico', '')])

    def test_el_detalle_no_hace_una_consulta_por_diagnostico(self):
        # Auditoría M-4: las consultas del detalle no crecen con los diagnósticos.
        from django.test.utils import CaptureQueriesContext
        uno = self.crear(diagnosticos=[{'descripcion': 'Uno'}]).data['id']
        diez = self.crear(diagnosticos=[{'descripcion': f'D{i}'} for i in range(10)]).data['id']

        def contar(informe_id):
            with CaptureQueriesContext(connection) as consultas:
                self.client.get(self.url(informe_id))
            return len(consultas)

        self.assertEqual(contar(diez), contar(uno))

    def test_el_pdf_muestra_microscopica_diagnosticos_y_comentarios_escapados(self):
        # Auditoría I-3 en los campos nuevos: el texto del usuario sale literal.
        from reportlab.platypus import Paragraph
        informe_id = self.crear(
            descripcion_microscopica='Células <b>atípicas',
            comentarios='<font size=40>ENORME</font>',
            diagnosticos=[{'descripcion': 'Carcinoma & <i>algo', 'codigo_cie10': 'C44.3'}],
        ).data['id']
        with mock.patch('informes.utils.Paragraph', wraps=Paragraph) as espia:
            respuesta = self.client.get(f'{self.url(informe_id)}pdf/')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        textos = ' '.join(str(llamada.args[0]) for llamada in espia.call_args_list)
        self.assertIn('DESCRIPCIÓN MICROSCÓPICA', textos)
        self.assertIn('Células &lt;b&gt;atípicas', textos)
        self.assertIn('DIAGNÓSTICOS', textos)
        self.assertIn('1. Carcinoma &amp; &lt;i&gt;algo (CIE-10: C44.3)', textos)
        self.assertIn('COMENTARIOS', textos)
        self.assertIn('&lt;font size=40&gt;ENORME&lt;/font&gt;', textos)
        self.assertNotIn('NOTAS ADICIONALES', textos)


class MigracionContenidoTests(TransactionTestCase):
    """La migración de la etapa 5 conserva las notas de los informes como comentarios (P-5)."""

    ANTES = [('informes', '0008_datos_solicitud'), ('accounts', '0001_initial')]

    def test_las_notas_pasan_a_comentarios(self):
        executor = MigrationExecutor(connection)
        executor.migrate(self.ANTES)
        modelos = executor.loader.project_state(self.ANTES).apps
        autor = modelos.get_model('accounts', 'Usuario').objects.create(username='autor_migracion_notas')
        patologia = modelos.get_model('informes', 'Patologia').objects.create(nombre='Patología notas')
        informe = modelos.get_model('informes', 'Informe').objects.create(
            numero_peticion='P-2026-09999', patologia=patologia, autor=autor, notas='Nota que debe conservarse',
        )

        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(executor.loader.graph.leaf_nodes())

        self.assertEqual(Informe.objects.get(id=informe.id).comentarios, 'Nota que debe conservarse')


class FinalizacionTests(APITestCase):
    """
    Informe v2, etapa 6 (docs/propuesta-informe-v2.md, 3.7 y 3.9; decisiones D-8 y D-10):
    - para finalizar, el informe tiene paciente y al menos un diagnóstico, el autor
      tiene registro médico y, en histología, hay descripción microscópica;
    - al finalizar se fija la fecha de informe y se congelan los datos que imprime;
    - la firma es siempre la del autor, aunque finalice un admin.
    Solo datos ficticios.
    """

    URL = '/api/informes/'
    SIN_PACIENTE = 'El informe no tiene paciente.'
    SIN_DIAGNOSTICO = 'El informe debe tener al menos un diagnóstico.'
    SIN_MICROSCOPICA = 'En un estudio de histología, la descripción microscópica es obligatoria.'
    SIN_REGISTRO = 'El patólogo autor no tiene registro médico; un administrador debe registrarlo.'

    def setUp(self):
        self.autor = Usuario.objects.create_user(
            username='patologo_firma', password='ClaveSegura-2026', rol=Usuario.Rol.PATOLOGO,
            nombre_completo='Dra. Ficticia Firma', especialidad='Patología Quirúrgica',
            registro_medico='RM-PRUEBA-0001',
        )
        self.admin = Usuario.objects.create_user(
            username='admin_firma', password='ClaveSegura-2026', rol=Usuario.Rol.ADMIN,
            nombre_completo='Admin Ficticio', registro_medico='RM-PRUEBA-9999',
        )
        self.client.force_authenticate(self.autor)
        self.patologia = Patologia.objects.create(nombre='Patología firma')
        self.eps = EPS.objects.create(nombre='EPS Ficticia')
        self.servicio = Servicio.objects.create(nombre='Dermatología')
        self.paciente = paciente_ficticio(eps=self.eps)

    def crear(self, **extra):
        cuerpo = {
            'patologia': self.patologia.id, 'paciente': self.paciente.id, 'datos_ingresados': {},
            'fecha_ingreso': '2026-10-01', 'servicio': self.servicio.id,
            'descripcion_microscopica': 'Proliferación de células basaloides.',
            'diagnosticos': [{'descripcion': 'Carcinoma basocelular nodular', 'codigo_cie10': 'C44.3'}],
            **extra,
        }
        respuesta = self.client.post(self.URL, cuerpo, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED, respuesta.data)
        return respuesta.data['id']

    def finalizar(self, informe_id):
        return self.client.post(f'{self.URL}{informe_id}/finalizar/')

    def detalle(self, informe_id):
        return self.client.get(f'{self.URL}{informe_id}/').data

    def assertNoFinaliza(self, informe_id, requisito):
        respuesta = self.finalizar(informe_id)
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(requisito, respuesta.data['requisitos'])
        self.assertIn(requisito, respuesta.data['detail'])
        informe = Informe.objects.get(id=informe_id)
        self.assertEqual(informe.estado, Informe.Estado.BORRADOR)
        self.assertIsNone(informe.fecha_informe)
        self.assertIsNone(informe.datos_finalizacion)

    # --- Requisitos para finalizar (D-8) ---

    def test_finaliza_un_informe_completo(self):
        informe_id = self.crear()
        respuesta = self.finalizar(informe_id)
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK, respuesta.data)
        self.assertEqual(respuesta.data['estado'], Informe.Estado.FINALIZADO)

    def test_no_finaliza_sin_diagnosticos(self):
        self.assertNoFinaliza(self.crear(diagnosticos=[]), self.SIN_DIAGNOSTICO)

    def test_no_finaliza_si_el_autor_no_tiene_registro_medico(self):
        self.autor.registro_medico = ''
        self.autor.save()
        self.assertNoFinaliza(self.crear(), self.SIN_REGISTRO)

    def test_no_finaliza_un_informe_antiguo_sin_paciente(self):
        antiguo = Informe.objects.create(
            patologia=self.patologia, autor=self.autor, descripcion_microscopica='Hallazgos.',
        )
        Diagnostico.objects.create(informe=antiguo, orden=1, descripcion='Diagnóstico')
        self.assertNoFinaliza(antiguo.id, self.SIN_PACIENTE)

    def test_histologia_exige_descripcion_microscopica(self):
        for vacia in ['', '   ']:
            with self.subTest(microscopica=vacia):
                self.assertNoFinaliza(self.crear(descripcion_microscopica=vacia), self.SIN_MICROSCOPICA)

    def test_otros_tipos_de_estudio_no_exigen_descripcion_microscopica(self):
        informe_id = self.crear(tipo_estudio='citologia_no_ginecologica', descripcion_microscopica='')
        self.assertEqual(self.finalizar(informe_id).status_code, status.HTTP_200_OK)

    def test_informa_todos_los_requisitos_que_faltan_a_la_vez(self):
        self.autor.registro_medico = ''
        self.autor.save()
        informe_id = self.crear(diagnosticos=[], descripcion_microscopica='')
        respuesta = self.finalizar(informe_id)
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(respuesta.data['requisitos'], [self.SIN_DIAGNOSTICO, self.SIN_MICROSCOPICA, self.SIN_REGISTRO])

    def test_el_registro_que_cuenta_es_el_del_autor_aunque_finalice_un_admin(self):
        self.autor.registro_medico = ''
        self.autor.save()
        informe_id = self.crear()
        self.client.force_authenticate(self.admin)  # el admin sí tiene registro médico
        self.assertNoFinaliza(informe_id, self.SIN_REGISTRO)

    def test_un_borrador_incompleto_se_puede_guardar(self):
        # D-8: los requisitos son para finalizar, no para guardar el borrador.
        informe_id = self.crear(diagnosticos=[], descripcion_microscopica='')
        respuesta = self.client.patch(f'{self.URL}{informe_id}/', {'comentarios': 'A medias'}, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK, respuesta.data)

    # --- Fecha de informe ---

    def test_al_finalizar_se_fija_la_fecha_de_informe(self):
        informe_id = self.crear()
        self.assertIsNone(self.detalle(informe_id)['fecha_informe'])
        momento = timezone.make_aware(datetime(2026, 10, 4, 15, 30))
        with mock.patch('django.utils.timezone.now', return_value=momento):
            respuesta = self.finalizar(informe_id)
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK, respuesta.data)
        self.assertEqual(Informe.objects.get(id=informe_id).fecha_informe, momento)
        self.assertIsNotNone(self.detalle(informe_id)['fecha_informe'])

    def test_la_fecha_de_informe_y_los_datos_congelados_no_se_escriben_por_la_api(self):
        informe_id = self.crear(fecha_informe='2020-01-01T00:00:00Z', datos_finalizacion={'falso': True})
        informe = Informe.objects.get(id=informe_id)
        self.assertIsNone(informe.fecha_informe)
        self.assertIsNone(informe.datos_finalizacion)
        self.client.patch(f'{self.URL}{informe_id}/', {'fecha_informe': '2020-01-01T00:00:00Z'}, format='json')
        self.assertIsNone(Informe.objects.get(id=informe_id).fecha_informe)

    # --- Firma ---

    def test_el_borrador_muestra_la_firma_actual_del_autor(self):
        informe_id = self.crear()
        self.assertEqual(self.detalle(informe_id)['firma'], {
            'nombre': 'Dra. Ficticia Firma',
            'especialidad': 'Patología Quirúrgica',
            'registro_medico': 'RM-PRUEBA-0001',
        })

    def test_la_firma_es_la_del_autor_aunque_finalice_un_admin(self):
        informe_id = self.crear()
        self.client.force_authenticate(self.admin)
        respuesta = self.finalizar(informe_id)
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK, respuesta.data)
        self.assertEqual(respuesta.data['firma']['registro_medico'], 'RM-PRUEBA-0001')
        self.assertEqual(respuesta.data['firma']['nombre'], 'Dra. Ficticia Firma')

    # --- Datos congelados (D-10) ---

    def test_corregir_paciente_eps_servicio_o_autor_no_cambia_un_informe_finalizado(self):
        informe_id = self.crear()
        self.assertEqual(self.finalizar(informe_id).status_code, status.HTTP_200_OK)
        antes = self.detalle(informe_id)

        Paciente.objects.filter(id=self.paciente.id).update(
            nombres='Otro Nombre', apellidos='Corregido', numero_documento='PRUEBA0099',
            tipo_documento='TI', sexo='masculino', fecha_nacimiento=date(1990, 1, 1),
        )
        EPS.objects.filter(id=self.eps.id).update(nombre='EPS Renombrada')
        Servicio.objects.filter(id=self.servicio.id).update(nombre='Servicio Renombrado')
        Usuario.objects.filter(id=self.autor.id).update(
            nombre_completo='Nombre Cambiado', especialidad='Otra', registro_medico='RM-PRUEBA-0002',
        )

        despues = self.detalle(informe_id)
        for campo in ['paciente_datos', 'eps_nombre', 'servicio_nombre', 'firma']:
            with self.subTest(campo=campo):
                self.assertEqual(despues[campo], antes[campo])
        self.assertEqual(despues['paciente_datos']['nombre_completo'], 'Paciente Ficticio Uno')
        self.assertEqual(despues['paciente_datos']['edad'], '45 años')  # nació el 5/10/1980, ingresó el 1/10/2026
        self.assertEqual(despues['eps_nombre'], 'EPS Ficticia')
        self.assertEqual(despues['firma']['registro_medico'], 'RM-PRUEBA-0001')

    def test_en_un_borrador_los_datos_siguen_siendo_los_actuales(self):
        informe_id = self.crear()
        EPS.objects.filter(id=self.eps.id).update(nombre='EPS Renombrada')
        Usuario.objects.filter(id=self.autor.id).update(registro_medico='RM-PRUEBA-0002')
        detalle = self.detalle(informe_id)
        self.assertEqual(detalle['eps_nombre'], 'EPS Renombrada')
        self.assertEqual(detalle['firma']['registro_medico'], 'RM-PRUEBA-0002')

    def test_el_pdf_de_un_informe_finalizado_usa_la_firma_congelada(self):
        from reportlab.platypus import Table
        informe_id = self.crear()
        momento = timezone.make_aware(datetime(2026, 10, 4, 15, 30))
        with mock.patch('django.utils.timezone.now', return_value=momento):
            self.assertEqual(self.finalizar(informe_id).status_code, status.HTTP_200_OK)
        Usuario.objects.filter(id=self.autor.id).update(nombre_completo='Nombre Cambiado', registro_medico='RM-OTRO')
        with mock.patch('informes.utils.Table', wraps=Table) as espia:
            respuesta = self.client.get(f'{self.URL}{informe_id}/pdf/')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        filas = dict((fila[0], fila[1]) for fila in espia.call_args.args[0])
        self.assertEqual(filas['Patólogo:'], 'Dra. Ficticia Firma')
        self.assertEqual(filas['Registro médico:'], 'RM-PRUEBA-0001')
        self.assertEqual(filas['Fecha de informe:'], '04/10/2026 15:30')

    def test_el_pdf_de_un_borrador_no_tiene_fecha_de_informe(self):
        from reportlab.platypus import Table
        informe_id = self.crear()
        with mock.patch('informes.utils.Table', wraps=Table) as espia:
            self.client.get(f'{self.URL}{informe_id}/pdf/')
        filas = dict((fila[0], fila[1]) for fila in espia.call_args.args[0])
        self.assertEqual(filas['Patólogo:'], 'Dra. Ficticia Firma')
        self.assertNotIn('Fecha de informe:', filas)

    def test_no_se_puede_finalizar_dos_veces(self):
        informe_id = self.crear()
        self.assertEqual(self.finalizar(informe_id).status_code, status.HTTP_200_OK)
        fecha = Informe.objects.get(id=informe_id).fecha_informe
        self.assertEqual(self.finalizar(informe_id).status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Informe.objects.get(id=informe_id).fecha_informe, fecha)


class MigracionFinalizacionTests(TransactionTestCase):
    """
    La migración de la etapa 6 completa los informes que ya estaban finalizados:
    fecha_informe toma la fecha de la última modificación (la mejor aproximación
    disponible) y datos_finalizacion se llena con los datos actuales.
    """

    ANTES = [('informes', '0009_contenido'), ('accounts', '0001_initial')]

    def test_completa_los_informes_ya_finalizados(self):
        executor = MigrationExecutor(connection)
        executor.migrate(self.ANTES)
        modelos = executor.loader.project_state(self.ANTES).apps
        autor = modelos.get_model('accounts', 'Usuario').objects.create(
            username='autor_migracion_firma', nombre_completo='Dr. Ficticio Migración',
        )
        patologia = modelos.get_model('informes', 'Patologia').objects.create(nombre='Patología migración firma')
        eps = modelos.get_model('pacientes', 'EPS').objects.create(nombre='EPS Migración')
        paciente = modelos.get_model('pacientes', 'Paciente').objects.create(
            tipo_documento='CC', numero_documento='PRUEBA0500', nombres='Paciente Ficticio', apellidos='Migración',
            fecha_nacimiento=date(1970, 1, 1), sexo='femenino',
        )
        InformeAntes = modelos.get_model('informes', 'Informe')
        finalizado = InformeAntes.objects.create(
            numero_peticion='P-2026-09990', patologia=patologia, autor=autor, paciente=paciente, eps=eps,
            fecha_ingreso=date(2026, 9, 1), estado='finalizado',
        )
        borrador = InformeAntes.objects.create(
            numero_peticion='P-2026-09991', patologia=patologia, autor=autor, paciente=paciente,
        )
        sin_paciente = InformeAntes.objects.create(
            numero_peticion='P-2026-09992', patologia=patologia, autor=autor, estado='finalizado',
        )
        actualizado = InformeAntes.objects.get(id=finalizado.id).fecha_actualizacion

        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(executor.loader.graph.leaf_nodes())

        finalizado = Informe.objects.get(id=finalizado.id)
        self.assertEqual(finalizado.fecha_informe, actualizado)
        self.assertEqual(finalizado.datos_finalizacion['paciente']['nombre_completo'], 'Paciente Ficticio Migración')
        self.assertEqual(finalizado.datos_finalizacion['eps_nombre'], 'EPS Migración')
        self.assertEqual(finalizado.datos_finalizacion['firma']['nombre'], 'Dr. Ficticio Migración')
        borrador = Informe.objects.get(id=borrador.id)
        self.assertIsNone(borrador.fecha_informe)
        self.assertIsNone(borrador.datos_finalizacion)
        self.assertIsNone(Informe.objects.get(id=sin_paciente.id).datos_finalizacion['paciente'])

import io
import os
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Usuario

from .models import Comentario, ImagenPublicacion, Publicacion

CARPETA_MEDIA_PRUEBAS = tempfile.mkdtemp(prefix='patolab-media-pruebas-')


def imagen_png(nombre='foto.png', lado=64):
    """PNG válido. Con píxeles al azar pesa varios KB (lado=64 → unos 12 KB)."""
    buffer = io.BytesIO()
    Image.frombytes('RGB', (lado, lado), os.urandom(lado * lado * 3)).save(buffer, format='PNG')
    return SimpleUploadedFile(nombre, buffer.getvalue(), content_type='image/png')


@override_settings(MEDIA_ROOT=CARPETA_MEDIA_PRUEBAS, FORO_MAX_TAMANO_IMAGEN=1024)
class SubidaImagenesForoTests(APITestCase):
    """
    Hallazgo I-6 de docs/auditoria-inicial.md: no había un límite real de tamaño
    para las imágenes del foro, y tampoco se comprobaba que el archivo fuera una
    imagen. En estas pruebas el límite se baja a 1 KB para no fabricar archivos grandes.
    """

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(CARPETA_MEDIA_PRUEBAS, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.patologo = Usuario.objects.create_user(
            username='patologo_foro',
            password='ClaveSegura-2026',
            rol=Usuario.Rol.PATOLOGO,
        )
        self.publicacion = Publicacion.objects.create(autor=self.patologo, titulo='Caso', contenido='Texto')
        self.url = f'/api/foro/publicaciones/{self.publicacion.id}/imagenes/'
        self.client.force_authenticate(self.patologo)

    def subir(self, *archivos):
        return self.client.post(self.url, {'imagenes': list(archivos)}, format='multipart')

    def test_rechaza_imagen_mas_grande_que_el_limite(self):
        respuesta = self.subir(imagen_png(lado=64))  # ~12 KB > 1 KB
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('tamaño', respuesta.data['detail'])
        self.assertEqual(ImagenPublicacion.objects.count(), 0)

    def test_si_una_imagen_es_muy_grande_no_se_guarda_ninguna(self):
        respuesta = self.subir(imagen_png('pequena.png', lado=1), imagen_png('grande.png', lado=64))
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ImagenPublicacion.objects.count(), 0)

    def test_rechaza_archivo_que_no_es_imagen(self):
        falso = SimpleUploadedFile('foto.png', b'<html><script>alert(1)</script></html>', content_type='image/png')
        respuesta = self.subir(falso)
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ImagenPublicacion.objects.count(), 0)

    def test_acepta_imagen_valida_dentro_del_limite(self):
        # Control: una imagen real y pequeña se sigue subiendo normalmente.
        respuesta = self.subir(imagen_png(lado=1))
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ImagenPublicacion.objects.count(), 1)


class LimitePorDefectoTests(APITestCase):
    def test_el_limite_por_defecto_es_10_mb(self):
        from django.conf import settings

        self.assertEqual(getattr(settings, 'FORO_MAX_TAMANO_IMAGEN', None), 10 * 1024 * 1024)


class CamposProtegidosForoTests(APITestCase):
    """
    Hallazgo I-8 de docs/auditoria-inicial.md:
    - solo un admin puede fijar publicaciones (lo dice el propio modelo);
    - un comentario no se puede mover a otra publicación editándolo.
    """

    def setUp(self):
        self.autor = Usuario.objects.create_user(
            username='patologo_autor_foro',
            password='ClaveSegura-2026',
            rol=Usuario.Rol.PATOLOGO,
        )
        self.admin = Usuario.objects.create_user(
            username='admin_foro',
            password='ClaveSegura-2026',
            rol=Usuario.Rol.ADMIN,
        )
        self.publicacion = Publicacion.objects.create(autor=self.autor, titulo='Caso', contenido='Texto')
        self.otra_publicacion = Publicacion.objects.create(autor=self.admin, titulo='Otro', contenido='Texto')

    def test_patologo_no_puede_crear_publicacion_fijada(self):
        self.client.force_authenticate(self.autor)
        respuesta = self.client.post(
            '/api/foro/publicaciones/',
            {'titulo': 'Nuevo', 'contenido': 'Texto', 'fijado': True},
            format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertFalse(Publicacion.objects.get(id=respuesta.data['id']).fijado)

    def test_autor_no_puede_fijar_su_publicacion(self):
        self.client.force_authenticate(self.autor)
        self.client.patch(f'/api/foro/publicaciones/{self.publicacion.id}/', {'fijado': True}, format='json')
        self.publicacion.refresh_from_db()
        self.assertFalse(self.publicacion.fijado)

    def test_admin_si_puede_fijar_publicaciones(self):
        # Control: la moderación del admin sigue funcionando.
        self.client.force_authenticate(self.admin)
        respuesta = self.client.patch(
            f'/api/foro/publicaciones/{self.publicacion.id}/', {'fijado': True}, format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.publicacion.refresh_from_db()
        self.assertTrue(self.publicacion.fijado)

    def test_autor_no_puede_mover_su_comentario_a_otra_publicacion(self):
        comentario = Comentario.objects.create(publicacion=self.publicacion, autor=self.autor, contenido='Hola')
        self.client.force_authenticate(self.autor)
        self.client.patch(
            f'/api/foro/comentarios/{comentario.id}/',
            {'publicacion': self.otra_publicacion.id},
            format='json',
        )
        comentario.refresh_from_db()
        self.assertEqual(comentario.publicacion_id, self.publicacion.id)

    def test_autor_si_puede_editar_el_texto_de_su_comentario(self):
        # Control: editar el contenido sigue permitido.
        comentario = Comentario.objects.create(publicacion=self.publicacion, autor=self.autor, contenido='Hola')
        self.client.force_authenticate(self.autor)
        respuesta = self.client.patch(
            f'/api/foro/comentarios/{comentario.id}/', {'contenido': 'Editado'}, format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        comentario.refresh_from_db()
        self.assertEqual(comentario.contenido, 'Editado')


class TemasInicialesTests(APITestCase):
    """Decisión D-5 (auditoría M-6): seed_data crea los temas iniciales del foro."""

    TEMAS = ['Casos clínicos', 'Dudas y consultas', 'Investigación', 'Técnicas de laboratorio']

    def ejecutar_seed(self):
        from io import StringIO

        from django.core.management import call_command

        call_command('seed_data', stdout=StringIO())

    def test_seed_data_crea_los_temas(self):
        self.ejecutar_seed()
        from .models import TemaForo

        self.assertEqual(sorted(TemaForo.objects.values_list('nombre', flat=True)), self.TEMAS)

    def test_ejecutar_seed_dos_veces_no_duplica(self):
        self.ejecutar_seed()
        self.ejecutar_seed()
        from .models import TemaForo

        self.assertEqual(TemaForo.objects.count(), 4)

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
from .models import ImagenPublicacion, Publicacion

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
            username='patologo_foro', password='ClaveSegura-2026', rol=Usuario.Rol.PATOLOGO,
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

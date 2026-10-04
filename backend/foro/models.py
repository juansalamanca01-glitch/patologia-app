from django.db import models
from django.conf import settings


def ruta_imagen_publicacion(instance, filename):
    return f'foro/publicaciones/{instance.publicacion_id}/{filename}'


class TemaForo(models.Model):
    """Topic/category used to organize forum posts (e.g. Casos clínicos, Técnicas de tinción)."""

    nombre = models.CharField(max_length=150, unique=True, verbose_name='Nombre')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Tema del foro'
        verbose_name_plural = 'Temas del foro'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Publicacion(models.Model):
    """A research note / observation shared by a pathologist in the forum."""

    tema = models.ForeignKey(
        TemaForo,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='publicaciones',
        verbose_name='Tema',
    )
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='publicaciones_foro',
        verbose_name='Autor',
    )
    titulo = models.CharField(max_length=250, verbose_name='Título')
    contenido = models.TextField(verbose_name='Contenido')
    fijado = models.BooleanField(
        default=False, verbose_name='Fijado',
        help_text='Los administradores pueden fijar publicaciones importantes.',
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Publicación'
        verbose_name_plural = 'Publicaciones'
        ordering = ['-fijado', '-fecha_creacion']

    def __str__(self):
        return self.titulo


class ImagenPublicacion(models.Model):
    """Image attached to a forum post."""

    publicacion = models.ForeignKey(
        Publicacion,
        on_delete=models.CASCADE,
        related_name='imagenes',
        verbose_name='Publicación',
    )
    imagen = models.ImageField(upload_to=ruta_imagen_publicacion, verbose_name='Imagen')
    descripcion = models.CharField(max_length=200, blank=True, verbose_name='Descripción')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Imagen de publicación'
        verbose_name_plural = 'Imágenes de publicación'

    def __str__(self):
        return f'Imagen de "{self.publicacion.titulo}"'


class Comentario(models.Model):
    """Comment on a forum post."""

    publicacion = models.ForeignKey(
        Publicacion,
        on_delete=models.CASCADE,
        related_name='comentarios',
        verbose_name='Publicación',
    )
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comentarios_foro',
        verbose_name='Autor',
    )
    contenido = models.TextField(verbose_name='Contenido')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Comentario'
        verbose_name_plural = 'Comentarios'
        ordering = ['fecha_creacion']

    def __str__(self):
        return f'Comentario de {self.autor} en "{self.publicacion.titulo}"'

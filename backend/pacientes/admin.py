from django.contrib import admin
from .models import EPS


@admin.register(EPS)
class EPSAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'activa']
    list_filter = ['activa']
    search_fields = ['nombre']

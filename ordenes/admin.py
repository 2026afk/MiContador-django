from django.contrib import admin

from .models import Movimiento, Usuario

admin.site.register(Usuario)
admin.site.register(Movimiento)


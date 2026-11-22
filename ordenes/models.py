from django.db import models

from django.contrib.auth.hashers import check_password, make_password
from django.db import models


class Usuario(models.Model):

    id_usuario = models.AutoField(primary_key=True, db_column="id_usuario")
    nombre = models.CharField(max_length=30)
    # Se guarda el hash de la contraseña
    contrasena = models.CharField(max_length=128)

    class Meta:
        db_table = "usuario"

    def __str__(self):
        return self.nombre

    def set_contrasena(self, clave_plana):
        self.contrasena = make_password(clave_plana)

    def verificar_contrasena(self, clave_plana):
        return check_password(clave_plana, self.contrasena)


class Movimiento(models.Model):
    
    id_movimiento = models.AutoField(primary_key=True, db_column="id_movimiento")
    tipo = models.BooleanField()
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    descripcion = models.CharField(max_length=100, blank=True, null=True)
    fecha = models.DateTimeField()
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        db_column="id_usuario",
        related_name="movimientos",
    )

    class Meta:
        db_table = "movimientos"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{'Ingreso' if self.tipo else 'Egreso'} {self.monto}"


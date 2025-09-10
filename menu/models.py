from django.db import models

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name="productos")
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=8, decimal_places=2)
    imagen = models.ImageField(upload_to="productos/", blank=True, null=True)

    def __str__(self):
        return self.nombre

class Pedido(models.Model):
    creado_en = models.DateTimeField(auto_now_add=True)
    entregado = models.BooleanField(default=False)

    def __str__(self):
        return f"Pedido #{self.id}"

class PedidoItem(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="items")
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.cantidad}x {self.producto.nombre}"






from django.db import models
from django.db.models import Sum
from django.utils.timezone import now
class Categoria(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name="productos")
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=8, decimal_places=2)
    imagen = models.ImageField(upload_to="productos/", blank=True, null=True)

    def __str__(self):
        return self.nombre

class Pedido(models.Model):
    creado_en = models.DateTimeField(auto_now_add=True)
    entregado = models.BooleanField(default=False)
    confirmado = models.BooleanField(default=False)  # 🔹 Nuevo campo
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    atendido = models.BooleanField(default=False)  # 👈 Nuevo campo

    def calcular_total(self):
        total = self.items.aggregate(
            suma=Sum(models.F("cantidad") * models.F("producto__precio"))
        )["suma"] or 0
        self.total = total
        self.save()
        return total

    def __str__(self):
        return f"Pedido #{self.id} - Total: {self.total}"


class PedidoItem(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="items")
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)

    def subtotal(self):
        return self.cantidad * self.producto.precio

    def __str__(self):
        return f"{self.cantidad}x {self.producto.nombre}"

class VentaDiaria(models.Model):
    fecha = models.DateField(default=now)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"Ventas {self.fecha}: {self.total}"
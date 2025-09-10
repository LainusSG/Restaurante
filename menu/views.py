from django.shortcuts import render, redirect, get_object_or_404
from .models import Categoria, Producto, Pedido, PedidoItem

def menu_view(request):
    categorias = Categoria.objects.prefetch_related("productos").all()
    pedido = Pedido.objects.filter(entregado=False, confirmado=False).first()
    if pedido:
        pedido.calcular_total()

    return render(request, "menu/menu.html", {
        "categorias": categorias,
        "pedido": pedido,
    })

def agregar_al_pedido(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    pedido, creado = Pedido.objects.get_or_create(entregado=False, confirmado=False)

    item, creado_item = PedidoItem.objects.get_or_create(
        pedido=pedido, producto=producto,
        defaults={"cantidad": 1}  # si no existía, arranca en 1
    )

    if not creado_item:  # si ya existía, entonces sí sumamos
        item.cantidad += 1
        item.save()

    return redirect("menu")

def ver_pedido(request):
    pedido = Pedido.objects.filter(entregado=False, confirmado=False).first()
    if pedido:
        pedido.calcular_total()
    return render(request, "menu/pedido.html", {"pedido": pedido})

def atender_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, confirmado=True, atendido=False, entregado=False)
    pedido.atendido = True
    pedido.save()
    return redirect("cocina")  # regresa a la vista de cocina


def confirmar_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, confirmado=False)
    pedido.calcular_total()
    pedido.confirmado = True
    pedido.save()
    return redirect("menu")


def pedidos_cocina(request):
    pedidos = Pedido.objects.filter(confirmado=True, entregado=False).prefetch_related("items__producto")
    return render(request, "menu/cocina.html", {"pedidos": pedidos})


from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import now
from .models import Pedido, VentaDiaria
def surtir_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, confirmado=True, atendido=True, entregado=False)
    pedido.calcular_total()
    pedido.entregado = True
    pedido.save()

    

    # Guardar en ventas diarias
    fecha_hoy = now().date()
    venta, _ = VentaDiaria.objects.get_or_create(fecha=fecha_hoy)
    venta.total += pedido.total
    venta.save()

    return render(request, "menu/ticket.html", {"pedido": pedido})







def ventas_hoy(request):
    fecha_hoy = now().date()
    ventas = VentaDiaria.objects.filter(fecha=fecha_hoy).first()
    return render(request, "menu/ventas.html", {"ventas": ventas})





from django.db.models import Sum
from django.utils.timezone import now
from datetime import timedelta
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, TruncYear
from .models import VentaDiaria

def dashboard_ventas(request):
    filtro = request.GET.get("filtro", "dia")  # valores: dia, semana, mes, año

    hoy = now().date()
    ventas = VentaDiaria.objects.all().order_by("fecha")

    if filtro == "dia":
        datos = ventas.annotate(periodo=TruncDay("fecha")).values("periodo").annotate(total=Sum("total"))
    elif filtro == "semana":
        datos = ventas.annotate(periodo=TruncWeek("fecha")).values("periodo").annotate(total=Sum("total"))
    elif filtro == "mes":
        datos = ventas.annotate(periodo=TruncMonth("fecha")).values("periodo").annotate(total=Sum("total"))
    elif filtro == "año":
        datos = ventas.annotate(periodo=TruncYear("fecha")).values("periodo").annotate(total=Sum("total"))
    else:
        datos = ventas.annotate(periodo=TruncDay("fecha")).values("periodo").annotate(total=Sum("total"))

    # Preparar datos para la gráfica
    labels = [d["periodo"].strftime("%d/%m/%Y") for d in datos]
    valores = [float(d["total"]) for d in datos]

    return render(request, "menu/dashboard.html", {
        "filtro": filtro,
        "labels": labels,
        "valores": valores,
        "datos": datos,
    })





from django.shortcuts import render, redirect
from .forms import CategoriaForm, ProductoForm
from .models import Categoria, Producto
from django.contrib.auth.decorators import login_required

@login_required
def crear_categoria(request):
    if request.method == "POST":
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("crear_menu")
    else:
        form = CategoriaForm()
    return render(request, "menu/crear_categoria.html", {"form": form})

@login_required
def crear_producto(request):
    if request.method == "POST":
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("crear_menu")
    else:
        form = ProductoForm()
    return render(request, "menu/crear_producto.html", {"form": form})
@login_required
def crear_menu(request):
    categorias = Categoria.objects.all().prefetch_related("productos")
    return render(request, "menu/crear_menu.html", {"categorias": categorias})




from django.shortcuts import render, redirect, get_object_or_404
from .models import Pedido, PedidoItem

def eliminar_item_pedido(request, item_id):
    item = get_object_or_404(PedidoItem, id=item_id, pedido__confirmado=False)
    pedido_id = item.pedido.id

    if item.cantidad > 1:
        item.cantidad -= 1
        item.save()
    else:
        item.delete()

    return redirect("menu")



def editar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    if request.method == "POST":
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            return redirect("crear_menu")  # vuelve a la página de administración del menú
    else:
        form = ProductoForm(instance=producto)
    return render(request, "menu/editar_producto.html", {"form": form, "producto": producto})

def eliminar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)

    if request.method == "POST":
        producto.delete()
        return redirect("crear_menu")

    return render(request, "menu/eliminar_producto.html", {"producto": producto})
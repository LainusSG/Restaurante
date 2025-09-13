from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.timezone import now
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, TruncYear

from .models import Categoria, Producto, Pedido, PedidoItem, Mesa, VentaDiaria
from .forms import CategoriaForm, ProductoForm, MesaForm


# =====================
# Selección de mesa
# =====================
def seleccionar_mesa(request):
    mesas = Mesa.objects.all()
    return render(request, "menu/seleccionar_mesa.html", {"mesas": mesas})


# =====================
# Menú y pedidos
# =====================
def menu_view(request, mesa_id):
    mesa = get_object_or_404(Mesa, id=mesa_id)
    categorias = Categoria.objects.prefetch_related("productos").all()

    pedido, _ = Pedido.objects.get_or_create(
        mesa=mesa,
        entregado=False
    )

    pedido.calcular_total()

    # ✅ Revisar si todos los items ya fueron surtidos
    todos_entregados = not pedido.items.filter(surtido=False).exists()

    return render(request, "menu/menu.html", {
        "categorias": categorias,
        "pedido": pedido,
        "mesa": mesa,
        "todos_entregados": todos_entregados,
    })


def agregar_al_pedido(request, mesa_id, producto_id):
    mesa = get_object_or_404(Mesa, id=mesa_id)
    producto = get_object_or_404(Producto, id=producto_id)

    pedido, _ = Pedido.objects.get_or_create(
        mesa=mesa,
        entregado=False
    )

    observaciones = request.POST.get("observaciones", "").strip()
    if not observaciones:
        observaciones = "con todo"

    # 🚨 Siempre crear un nuevo item
    PedidoItem.objects.create(
        pedido=pedido,
        producto=producto,
        observaciones=observaciones,
        cantidad=1,
        confirmado=False
    )

    # 🚨 Si ya estaba confirmado, volver a marcarlo como NO confirmado
    if pedido.confirmado:
        pedido.confirmado = False
        pedido.save()

    return redirect("menu", mesa_id=mesa.id)


def eliminar_item_pedido(request, mesa_id, item_id):
    item = get_object_or_404(PedidoItem, id=item_id, pedido__mesa_id=mesa_id)

    if item.confirmado:
        return redirect("menu", mesa_id=mesa_id)

    if item.cantidad > 1:
        item.cantidad -= 1
        item.save()
    else:
        item.delete()

    return redirect("menu", mesa_id=mesa_id)


def confirmar_pedido(request, mesa_id, pedido_id):
    mesa = get_object_or_404(Mesa, id=mesa_id)
    pedido = get_object_or_404(Pedido, id=pedido_id, mesa=mesa, confirmado=False)

    if request.method == "POST":
        pedido.items.filter(confirmado=False).update(confirmado=True)
        pedido.calcular_total()
        pedido.confirmado = True
        mesa.ocupada = True
        mesa.save()
        pedido.save()

    return redirect("menu", mesa_id=mesa.id)


def generar_ticket(request, mesa_id, pedido_id):
    mesa = get_object_or_404(Mesa, id=mesa_id)
    pedido = get_object_or_404(Pedido, id=pedido_id, mesa=mesa, confirmado=True, entregado=False)

    # 🚨 Solo permitir si todos los items están surtidos
    if pedido.items.filter(surtido=False).exists():
        return redirect("menu", mesa_id=mesa.id)

    pedido.calcular_total()
    pedido.entregado = True
    pedido.save()

    mesa.ocupada = False
    mesa.save()

    fecha_hoy = now().date()
    venta, _ = VentaDiaria.objects.get_or_create(fecha=fecha_hoy)
    venta.total += pedido.total
    venta.save()

    return render(request, "menu/ticket.html", {"pedido": pedido})




# =====================
# Cocina
# =====================
def pedidos_cocina(request):
    pedidos = (
        Pedido.objects.filter(confirmado=True, entregado=False)
        .select_related("mesa")
        .prefetch_related("items__producto")
    )
    return render(request, "menu/cocina.html", {"pedidos": pedidos})


def pedidos_cocina_json(request):
    pedidos = (
        Pedido.objects.filter(confirmado=True, entregado=False)
        .select_related("mesa")
        .prefetch_related("items__producto")
    )
    html = render_to_string("menu/pedidos_list.html", {"pedidos": pedidos})
    return JsonResponse({"html": html})


def atender_item(request, item_id):
    item = get_object_or_404(PedidoItem, id=item_id, confirmado=True, atendido=False)
    item.atendido = True
    item.save()
    return redirect("cocina")


def surtir_item(request, item_id):
    item = get_object_or_404(PedidoItem, id=item_id, confirmado=True, atendido=True, surtido=False)
    item.surtido = True
    item.save()
    return redirect("cocina")


# =====================
# Dashboard de ventas
# =====================
def dashboard_ventas(request):
    filtro = request.GET.get("filtro", "dia")

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

    labels = [d["periodo"].strftime("%d/%m/%Y") for d in datos]
    valores = [float(d["total"]) for d in datos]

    return render(request, "menu/dashboard.html", {
        "filtro": filtro,
        "labels": labels,
        "valores": valores,
        "datos": datos,
    })


# =====================
# CRUD Categorías y Productos
# =====================
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


@login_required
def editar_categoria(request, categoria_id):
    categoria = get_object_or_404(Categoria, id=categoria_id)
    if request.method == "POST":
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            return redirect("crear_menu")
    else:
        form = CategoriaForm(instance=categoria)
    return render(request, "menu/editar_categoria.html", {"form": form, "categoria": categoria})


@login_required
def eliminar_categoria(request, categoria_id):
    categoria = get_object_or_404(Categoria, id=categoria_id)
    if request.method == "POST":
        categoria.delete()
        return redirect("crear_menu")
    return render(request, "menu/eliminar_categoria.html", {"categoria": categoria})


def editar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    if request.method == "POST":
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            return redirect("crear_menu")
    else:
        form = ProductoForm(instance=producto)
    return render(request, "menu/editar_producto.html", {"form": form, "producto": producto})


def eliminar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    if request.method == "POST":
        producto.delete()
        return redirect("crear_menu")
    return render(request, "menu/eliminar_producto.html", {"producto": producto})


# =====================
# CRUD Mesas
# =====================
def crear_mesa(request):
    if request.method == "POST":
        form = MesaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Mesa creada correctamente ✅")
            return redirect("listar_mesas")
    else:
        form = MesaForm()
    return render(request, "menu/crear_mesa.html", {"form": form})


def listar_mesas(request):
    mesas = Mesa.objects.all()
    return render(request, "menu/listar_mesas.html", {"mesas": mesas})


def borrar_mesa(request, mesa_id):
    mesa = get_object_or_404(Mesa, id=mesa_id)
    if request.method == "POST":
        mesa.delete()
        return redirect("listar_mesas")
    return render(request, "menu/confirmar_borrar.html", {"mesa": mesa})



def Menu_cliente(request):
    categorias = Categoria.objects.prefetch_related("productos").all()
    return render(request, "menu/menu_cliente.html", {
        "categorias": categorias
    })

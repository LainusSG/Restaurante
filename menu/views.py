from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, TruncYear

from .models import (
    Categoria, Producto, Pedido, PedidoItem, Mesa, VentaDiaria
)
from .forms import CategoriaForm, ProductoForm, MesaForm
from django.template.loader import render_to_string

# =====================================================
# 🪑 MESAS
# =====================================================

def listar_mesas(request):
    mesas = Mesa.objects.all()
    return render(request, "menu/listar_mesas.html", {"mesas": mesas})

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

def borrar_mesa(request, mesa_id):
    mesa = get_object_or_404(Mesa, id=mesa_id)
    if request.method == "POST":
        mesa.delete()
        return redirect("listar_mesas")
    return render(request, "menu/confirmar_borrar.html", {"mesa": mesa})


# =====================================================
# 📋 MENÚ Y PEDIDOS
# =====================================================

def menu_view(request, mesa_id=None):
    categorias = Categoria.objects.prefetch_related("productos").all()
    mesas = Mesa.objects.all()
    mesa = None
    pedido = None

    if mesa_id:
        mesa = get_object_or_404(Mesa, id=mesa_id)
        pedido = Pedido.objects.filter(mesa=mesa, confirmado=True, entregado=False).first()
        if not pedido:
            pedido = Pedido.objects.create(mesa=mesa, confirmado=True)
            mesa.ocupada = True
            mesa.save()
    else:
        pedido = Pedido.objects.filter(confirmado=False, entregado=False).first()

    if pedido:
        pedido.calcular_total()

    return render(request, "menu/menu.html", {
        "categorias": categorias,
        "pedido": pedido,
        "mesa": mesa,
        "mesas": mesas,
    })


def agregar_al_pedido(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    mesa_id = request.POST.get("mesa_id")
    mesa = get_object_or_404(Mesa, id=mesa_id)

    pedido, _ = Pedido.objects.get_or_create(
        mesa=mesa, confirmado=True, entregado=False
    )

    observaciones = request.POST.get("observaciones", "").strip() or "con todo"

    item, creado_item = PedidoItem.objects.get_or_create(
        pedido=pedido,
        producto=producto,
        observaciones=observaciones,
        defaults={"cantidad": 1}
    )

    if not creado_item:
        item.cantidad += 1
        item.save()

    return redirect("menu_por_mesa", mesa_id=mesa.id)


def eliminar_item_pedido(request, item_id):
    item = get_object_or_404(PedidoItem, id=item_id, pedido__confirmado=False)
    if item.cantidad > 1:
        item.cantidad -= 1
        item.save()
    else:
        item.delete()
    return redirect("menu")


# =====================================================
# 👨‍🍳 COCINA
# =====================================================

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

def atender_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, confirmado=True, atendido=False, entregado=False)
    pedido.atendido = True
    pedido.save()
    return redirect("cocina")

def surtir_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, confirmado=True, atendido=True, entregado=False)
    pedido.calcular_total()
    pedido.entregado = True
    pedido.save()

    if pedido.mesa:
        pedido.mesa.ocupada = False
        pedido.mesa.save()

    fecha_hoy = now().date()
    venta, _ = VentaDiaria.objects.get_or_create(fecha=fecha_hoy)
    venta.total += pedido.total
    venta.save()

    return render(request, "menu/ticket.html", {"pedido": pedido})


# =====================================================
# 💰 VENTAS
# =====================================================

def ventas_hoy(request):
    fecha_hoy = now().date()
    ventas = VentaDiaria.objects.filter(fecha=fecha_hoy).first()
    return render(request, "menu/ventas.html", {"ventas": ventas})

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


# =====================================================
# 🍔 CRUD DE CATEGORÍAS Y PRODUCTOS
# =====================================================

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

@login_required
def crear_menu(request):
    categorias = Categoria.objects.all().prefetch_related("productos")
    return render(request, "menu/crear_menu.html", {"categorias": categorias})

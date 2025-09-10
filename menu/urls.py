from django.urls import path
from . import views

urlpatterns = [
    path("", views.menu_view, name="menu"),
    path("agregar/<int:producto_id>/", views.agregar_al_pedido, name="agregar_al_pedido"),
    path("producto/<int:producto_id>/editar/", views.editar_producto, name="editar_producto"),
    path("producto/<int:producto_id>/eliminar/", views.eliminar_producto, name="eliminar_producto"),



    path("pedido/", views.ver_pedido, name="pedido"),
    path("pedido/confirmar/<int:pedido_id>/", views.confirmar_pedido, name="confirmar_pedido"),
    path("pedido/eliminar/<int:item_id>/", views.eliminar_item_pedido, name="eliminar_item_pedido"),
    path("pedido/<int:pedido_id>/atender/", views.atender_pedido, name="atender_pedido"),


    path("cocina/", views.pedidos_cocina, name="cocina"),
    path("surtir/<int:pedido_id>/", views.surtir_pedido, name="surtir_pedido"),





    path("dashboard/", views.dashboard_ventas, name="dashboard"),



    # CRUD menú
    path("menu/crear/", views.crear_menu, name="crear_menu"),
    path("menu/crear/categoria/", views.crear_categoria, name="crear_categoria"),
    path("menu/crear/producto/", views.crear_producto, name="crear_producto"),
]

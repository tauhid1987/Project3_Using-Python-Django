from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("index", views.index, name="index"),
    path('status', views.status, name="status"),
    path('gen_status', views.gen_status, name="gen_status"),
    path("register", views.register_view, name="register"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("add_item", views.add_item_view, name="add_item"),
    path("remove_item", views.remove_item_view, name="remove_item"),
    path("cart", views.cart_view, name="cart"),
    path("place_order", views.place_order_view, name="place_order"),
    path("show_order", views.show_order_view, name="show_order"),    
    path('delete_order/<str:pk>/', views.deleteOrder, name="delete_order"),
    path('order1/', views.order1, name="order1"),
    path('charge/', views.charge, name="charge"),
    path('success/<str:args>/', views.successMsg, name="success"),
]

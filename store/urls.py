
from django import views
from django.urls import path
from .import views

urlpatterns = [
    path('store.html', views.store, name='store_html'),
    path('<slug:category_slug>/', views.store, name='products_by_category'),
    path('<slug:category_slug>/<slug:product_slug>/', views.product_detail, name='product_detail'),
]





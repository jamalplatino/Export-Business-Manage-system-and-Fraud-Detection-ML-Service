from django.urls import path
from . import views

urlpatterns = [
    path('', views.payment_list, name='payment_list'),
    path('new/', views.payment_create, name='payment_create'),
    path('<int:pk>/', views.payment_detail, name='payment_detail'),
]
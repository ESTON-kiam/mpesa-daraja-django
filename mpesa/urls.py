from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('process-payment/', views.process_payment, name='process_payment'),
    path('mpesa-callback/', views.mpesa_callback, name='mpesa_callback'),
]
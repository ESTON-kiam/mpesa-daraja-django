from django.urls import path
from . import views
from .mpesa import *

urlpatterns = [
    path('', views.index, name='index'),
    path('stk/', StkPushView, name='stk'),
    path('callback/',  mpesa_callback, name='callback'),
    path('process-payment/', views.process_payment, name='process_payment'),
    path('mpesa-callback/', views.mpesa_callback, name='mpesa_callback'),
]

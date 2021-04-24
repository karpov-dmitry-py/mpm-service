from django.urls import path

from . import views

urlpatterns = [

    path('account/', views.view_account, name='users-account'),
]
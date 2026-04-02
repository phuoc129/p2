"""
URL configuration for quanlydonhang project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', views.health_check, name='health_check'),

    # Auth
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Main pages
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # KẾT NỐI APP PRODUCT VÀO HỆ THỐNG
    path('', include('apps.product.urls')),

    path('units/', views.units_view, name='units'),
    # path('accounts/', views.accounts_view, name='accounts'),

    # Order app — đơn hàng & công nợ
    path('', include('apps.order.urls')),
    
    # Warehouse app — nhập kho & tồn kho
    path('', include('apps.warehouse.urls')),
]

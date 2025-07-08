"""
URL configuration for Prep_Tester project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from Test_Interface import urls as Test_Interface_urls

urlpatterns = [
    path('admin/', admin.site.urls), # Admin site URL
    path('test/', include(Test_Interface_urls)), # Main application URL
    path('', include('authenticator.urls')), # User authentication and management URLs
] 
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
 

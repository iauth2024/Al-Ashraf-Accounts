from django.contrib import admin
from django.urls import path, include
from accounts.views import test_view  # Test this import

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('test/', test_view),  # Test the new view
]

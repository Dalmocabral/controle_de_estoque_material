from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('estoque.urls')),  # Include the URLs from the estoque app
]

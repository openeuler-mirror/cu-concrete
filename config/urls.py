"""cu_concrete URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from api import views
from django.conf import settings
from django.conf.urls.static import static


# 添加Swagger文档支持
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# 配置Swagger文档视图
schema_view = get_schema_view(
   openapi.Info(
      title="cu-concrete API",
      default_version='v1',
      description="cu-concrete项目API文档",
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    # path('admin/', admin.site.urls),
    path('', views.index, name='api-root'),
    path('cu-concrete/', include('api.urls')),
    # 添加Swagger和Redoc路由
    path('swagger/', schema_view.with_ui(
        'swagger',
        cache_timeout=0
    ), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui(
        'redoc',
        cache_timeout=0
    ), name='schema-redoc'),
]

# 添加静态文件服务
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# # 在DEBUG模式下添加静态文件服务
# if settings.DEBUG:
#     urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
#     # 如果STATIC_ROOT中没有文件，也可以临时从STATICFILES_DIRS提供服务
#     urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / 'static')
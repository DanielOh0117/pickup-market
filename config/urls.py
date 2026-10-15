from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings  # 🟨 추가
from django.conf.urls.static import static  # 🟨 추가

urlpatterns = [
    path('admin/', admin.site.urls),
    path('stores/', include('stores.urls')),
    path('', RedirectView.as_view(url='/stores/owner/products/', permanent=False)),
]

# 🟨 개발 환경에서 미디어 파일(이미지)을 불러올 수 있도록 경로 추가
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
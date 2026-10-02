from django.urls import include, path

from apps.core.urlconf import validate_unique_url_patterns

urlpatterns = [
    path("api/auth/", include("apps.authentication.urls")),
    path("api/", include("apps.warehouse.urls")),
    path("api/", include("apps.personnel.urls")),
    path("api/", include("apps.reports.urls")),
]

# 启动期校验：任何模块再次注册重复路径/命名都会在此抛出
# ImproperlyConfigured，避免先匹配的路由静默遮蔽正式接口。
validate_unique_url_patterns(urlpatterns)

# 未知路径统一按 JSON 错误格式返回 404。
handler404 = "apps.core.views.not_found"

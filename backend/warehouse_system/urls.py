"""
项目根 URL 配置

所有 API 模块经 build_api_patterns 集中注册；模块间若出现重复路径或
重复 URL 名称，将在启动时直接抛出 ImproperlyConfigured，而不是静默遮蔽。
"""
from apps.core.routing import build_api_patterns
from apps.core.views import json404

# (URL前缀, 模块urlconf)，注册顺序即匹配顺序
API_ROUTES = [
    ("api/auth/", "apps.authentication.urls"),
    ("api/", "apps.warehouse.urls"),
    ("api/", "apps.personnel.urls"),
    ("api/", "apps.reports.urls"),
]

urlpatterns = build_api_patterns(API_ROUTES)

# 未知路径统一返回错误信封，而非 Django 默认 HTML 404 页
handler404 = json404

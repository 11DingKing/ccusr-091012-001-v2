"""
API 路由集中注册与冲突检测

各业务模块通过 ``build_api_patterns(...)`` 声明自己的 URL 前缀与 urlconf，
在项目根 URLConf 加载时即对最终路径与 URL 名称做去重校验。
若两个模块注册了同一路径（或同一 URL 名称），直接抛出
``ImproperlyConfigured``，避免“先注册的占位路由静默遮蔽正式接口”。
"""
from django.core.exceptions import ImproperlyConfigured
from django.urls import include, path
from django.urls.resolvers import URLPattern, URLResolver


def _collect_routes(url_patterns, prefix=""):
    """展开 urlconf，产出 (完整路径, URL名称)；兼容 include 嵌套。"""
    for url_pattern in url_patterns:
        full_route = prefix + str(url_pattern.pattern)
        if isinstance(url_pattern, URLPattern):
            yield full_route, url_pattern.name
        elif isinstance(url_pattern, URLResolver):
            yield from _collect_routes(url_pattern.url_patterns, full_route)


def build_api_patterns(routes):
    """
    :param routes: ``[(URL前缀, urlconf路径或模块), ...]``，注册顺序即匹配顺序。
    :return: 可直接拼入根 ``urlpatterns`` 的列表。
    """
    # 完整路径 -> 注册它的模块
    path_owners = {}
    # URL名称 -> (注册模块, 完整路径)
    name_owners = {}
    patterns = []

    for prefix, urlconf in routes:
        resolver = path(prefix, include(urlconf))
        module_name = urlconf if isinstance(urlconf, str) else urlconf.__name__

        for full_route, name in _collect_routes(resolver.url_patterns, prefix):
            if full_route in path_owners:
                raise ImproperlyConfigured(
                    f"URL 路径冲突: '{full_route}' 同时被 {path_owners[full_route]} "
                    f"和 {module_name} 注册。请调整其中一个模块的路径，"
                    f"不要依赖注册顺序相互遮蔽。"
                )
            path_owners[full_route] = module_name

            if name is not None and name in name_owners:
                owner_module, owner_route = name_owners[name]
                raise ImproperlyConfigured(
                    f"URL 名称冲突: name='{name}' 同时被 {owner_module}（'{owner_route}'）"
                    f"和 {module_name}（'{full_route}'）注册。"
                    f"请使用唯一的 URL 名称或配置命名空间。"
                )
            if name is not None:
                name_owners[name] = (module_name, full_route)

        patterns.append(resolver)

    return patterns

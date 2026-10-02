"""
URLconf 完整性校验工具。

Django 按注册顺序匹配路由：当两个模块注册了相同路径时，
先注册的路由会静默遮蔽后续路由（本项目的 /api/dashboard/ 占位视图
曾因此遮蔽了 reports 应用的真实统计接口）。这里提供启动期校验，
一旦发现重复路径或重复命名就直接抛出 ImproperlyConfigured，
让冲突在启动/测试阶段暴露，而不是在线上静默生效。
"""
from django.core.exceptions import ImproperlyConfigured
from django.urls import URLResolver


def _describe_callback(callback):
    """返回视图回调的可读描述，用于冲突报错信息。"""
    view_class = getattr(callback, 'view_class', None)
    if view_class is not None:
        return f'{view_class.__module__}.{view_class.__name__}'
    module = getattr(callback, '__module__', '')
    name = getattr(callback, '__name__', repr(callback))
    return f'{module}.{name}' if module else name


def _iter_patterns(urlpatterns, prefix=''):
    """递归展开 URL 配置，产出 (完整路径, 路由名称, 视图描述)。"""
    for pattern in urlpatterns:
        route = prefix + str(pattern.pattern)
        if isinstance(pattern, URLResolver):
            yield from _iter_patterns(pattern.url_patterns, route)
        else:
            yield route, pattern.name, _describe_callback(pattern.callback)


def validate_unique_url_patterns(urlpatterns):
    """
    校验 URL 配置中不存在重复路径或重复命名。

    - 相同完整路径被多个视图注册：先匹配者会遮蔽其余，属于冲突；
    - 相同路由名称被多处使用：reverse() 结果不确定，属于冲突。

    发现冲突时抛出 ImproperlyConfigured，阻止应用带隐患启动。
    """
    seen_paths = {}
    seen_names = {}
    conflicts = []

    for route, name, view in _iter_patterns(urlpatterns):
        if route in seen_paths:
            conflicts.append(
                f'重复路径 "{route}": {seen_paths[route]} 与 {view} '
                f'(先注册的路由会静默遮蔽后者)'
            )
        else:
            seen_paths[route] = view

        if name:
            if name in seen_names:
                conflicts.append(
                    f'重复路由命名 "{name}": {seen_names[name]} 与 {view} '
                    f'(reverse() 解析结果不确定)'
                )
            else:
                seen_names[name] = view

    if conflicts:
        details = '\n  - '.join(conflicts)
        raise ImproperlyConfigured(
            f'检测到 {len(conflicts)} 处 URL 路由冲突:\n  - {details}\n'
            f'请为每个端点保留唯一的路径与命名后再启动服务。'
        )

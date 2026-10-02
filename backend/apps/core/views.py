"""
核心视图：全局错误处理。

URL 解析失败（未知路径）不会进入 DRF 视图，也就不会经过
custom_exception_handler，因此这里提供 handler404，
保证未知路径同样返回统一错误格式。
"""
from django.http import JsonResponse


def not_found(request, exception=None):
    """未知路径统一返回 JSON 错误格式，与全局异常处理保持一致。"""
    return JsonResponse(
        {
            'success': False,
            'code': 404,
            'message': '资源不存在',
            'data': None,
        },
        status=404,
    )

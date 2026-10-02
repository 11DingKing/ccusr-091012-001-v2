"""
跨模块通用视图/错误处理
"""
from django.http import JsonResponse


def json404(request, exception=None):
    """未知路径统一返回错误信封，与业务异常响应格式保持一致。"""
    return JsonResponse(
        {
            "success": False,
            "code": 404,
            "message": "请求的资源不存在",
            "data": None,
        },
        status=404,
    )

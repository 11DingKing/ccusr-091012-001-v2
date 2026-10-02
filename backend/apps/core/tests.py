"""
核心模块测试用例
"""
from types import ModuleType

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings
from rest_framework.test import APIClient, APITestCase
from rest_framework.views import APIView
from rest_framework import status
from django.urls import path
from .exceptions import (
    BusinessException, AuthenticationException,
    PermissionException, NotFoundException
)
from .response import success_response, error_response, created_response, deleted_response
from .routing import build_api_patterns


class _StubView(APIView):
    """路由校验用的空视图。"""
    def get(self, request):
        pass


def _stub_urlconf(module_name, entries):
    """entries: [(route, url_name), ...]"""
    module = ModuleType(module_name)
    module.urlpatterns = [
        path(route, _StubView.as_view(), name=name) for route, name in entries
    ]
    return module


class RoutingConflictTest(TestCase):
    """路由集中注册的冲突检测。"""

    def test_duplicate_path_raises_at_startup(self):
        """两个模块注册同一路径必须在启动时直接报错，而不是静默遮蔽。"""
        first = _stub_urlconf("fake_first", [("dashboard/", "first-dashboard")])
        second = _stub_urlconf("fake_second", [("dashboard/", "second-dashboard")])

        with self.assertRaises(ImproperlyConfigured) as ctx:
            build_api_patterns([("api/", first), ("api/", second)])

        self.assertIn("dashboard/", str(ctx.exception))
        self.assertIn("路径冲突", str(ctx.exception))

    def test_duplicate_name_raises_at_startup(self):
        """路径不同但 URL 名称相同同样必须报错。"""
        first = _stub_urlconf("fake_first", [("dashboard/", "dashboard")])
        second = _stub_urlconf("fake_second", [("reports/dashboard/", "dashboard")])

        with self.assertRaises(ImproperlyConfigured) as ctx:
            build_api_patterns([("api/", first), ("api/", second)])

        self.assertIn("名称冲突", str(ctx.exception))
        self.assertIn("dashboard", str(ctx.exception))

    def test_distinct_routes_build_normally(self):
        first = _stub_urlconf("fake_first", [("goods/", "goods-list")])
        second = _stub_urlconf("fake_second", [("dashboard/", "dashboard")])

        patterns = build_api_patterns([("api/", first), ("api/", second)])
        self.assertEqual(len(patterns), 2)


class UnknownPathResponseTest(APITestCase):
    """未知路径仍按统一错误信封返回。"""

    @override_settings(DEBUG=False)
    def test_unknown_path_returns_unified_error_envelope(self):
        response = APIClient().get("/api/this-endpoint-does-not-exist/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        body = response.json()
        self.assertFalse(body["success"])
        self.assertEqual(body["code"], 404)
        self.assertIn("message", body)
        self.assertIsNone(body["data"])


class ExceptionTest(TestCase):
    """异常测试"""
    
    def test_business_exception(self):
        """测试业务异常"""
        exc = BusinessException('业务错误', code=400)
        self.assertEqual(exc.message, '业务错误')
        self.assertEqual(exc.code, 400)
    
    def test_authentication_exception(self):
        """测试认证异常"""
        exc = AuthenticationException()
        self.assertEqual(exc.message, '认证失败')
        self.assertEqual(exc.code, 401)
    
    def test_permission_exception(self):
        """测试权限异常"""
        exc = PermissionException()
        self.assertEqual(exc.message, '权限不足')
        self.assertEqual(exc.code, 403)
    
    def test_not_found_exception(self):
        """测试资源不存在异常"""
        exc = NotFoundException('用户不存在')
        self.assertEqual(exc.message, '用户不存在')
        self.assertEqual(exc.code, 404)


class ResponseTest(TestCase):
    """响应测试"""
    
    def test_success_response(self):
        """测试成功响应"""
        response = success_response(data={'id': 1}, message='操作成功')
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], '操作成功')
        self.assertEqual(response.data['data']['id'], 1)
    
    def test_error_response(self):
        """测试错误响应"""
        response = error_response(message='操作失败', code=400)
        
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['message'], '操作失败')
    
    def test_created_response(self):
        """测试创建成功响应"""
        response = created_response(data={'id': 1})
        
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data['success'])
    
    def test_deleted_response(self):
        """测试删除成功响应"""
        response = deleted_response()
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])


class LoggingConfigTest(TestCase):
    """日志配置测试"""
    
    def test_request_id(self):
        """测试请求ID"""
        from .logging_config import set_request_id, get_request_id, clear_request_id
        
        # 设置请求ID
        request_id = set_request_id()
        self.assertIsNotNone(request_id)
        self.assertEqual(len(request_id), 8)
        
        # 获取请求ID
        self.assertEqual(get_request_id(), request_id)
        
        # 清除请求ID
        clear_request_id()
        self.assertIsNone(get_request_id())
    
    def test_custom_request_id(self):
        """测试自定义请求ID"""
        from .logging_config import set_request_id, get_request_id, clear_request_id
        
        custom_id = 'test1234'
        set_request_id(custom_id)
        self.assertEqual(get_request_id(), custom_id)
        
        clear_request_id()
    
    def test_get_logger(self):
        """测试获取日志记录器"""
        from .logging_config import get_logger
        
        logger = get_logger('test')
        self.assertIsNotNone(logger)
        self.assertEqual(logger.name, 'test')

"""
核心模块测试用例
"""
from importlib import import_module

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse
from django.test import TestCase
from django.urls import include, path
from rest_framework.test import APITestCase
from rest_framework import status
from .exceptions import (
    BusinessException, AuthenticationException,
    PermissionException, NotFoundException
)
from .response import success_response, error_response, created_response, deleted_response
from .urlconf import validate_unique_url_patterns


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


def _placeholder_view_a(request):
    return HttpResponse('a')


def _placeholder_view_b(request):
    return HttpResponse('b')


class UrlConfValidationTest(TestCase):
    """路由冲突校验：重复注册同名端点必须在启动期报错而非静默遮蔽"""

    def test_project_urlconf_passes_validation(self):
        """项目自身的 URL 配置不存在冲突"""
        urlconf = import_module(settings.ROOT_URLCONF)
        validate_unique_url_patterns(urlconf.urlpatterns)  # 不应抛出异常

    def test_duplicate_path_across_includes_raises(self):
        """两个应用注册相同路径时抛出 ImproperlyConfigured"""
        patterns = [
            path('api/', include([
                path('dashboard/', _placeholder_view_a, name='dashboard-a'),
            ])),
            path('api/', include([
                path('dashboard/', _placeholder_view_b, name='dashboard-b'),
            ])),
        ]
        with self.assertRaises(ImproperlyConfigured):
            validate_unique_url_patterns(patterns)

    def test_duplicate_route_name_raises(self):
        """相同路由命名导致 reverse() 不确定，必须报错"""
        patterns = [
            path('a/', _placeholder_view_a, name='dup-name'),
            path('b/', _placeholder_view_b, name='dup-name'),
        ]
        with self.assertRaises(ImproperlyConfigured):
            validate_unique_url_patterns(patterns)

    def test_unique_patterns_pass(self):
        """路径与命名均唯一时校验通过"""
        patterns = [
            path('api/', include([
                path('a/', _placeholder_view_a, name='route-a'),
            ])),
            path('api/', include([
                path('b/', _placeholder_view_b, name='route-b'),
            ])),
        ]
        validate_unique_url_patterns(patterns)  # 不应抛出异常


class UnknownPathTest(TestCase):
    """未知路径按统一错误格式返回 404"""

    def test_unknown_path_returns_unified_error_format(self):
        response = self.client.get('/api/no-such-endpoint/')
        self.assertEqual(response.status_code, 404)
        payload = response.json()
        self.assertFalse(payload['success'])
        self.assertEqual(payload['code'], 404)
        self.assertEqual(payload['message'], '资源不存在')
        self.assertIsNone(payload['data'])

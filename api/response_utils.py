"""
API响应格式工具模块
提供统一的响应格式，包含code和message字段
"""

from rest_framework.response import Response
from rest_framework import status

class ApiResponse:
    """API响应格式工具类"""
    
    # 成功响应
    @staticmethod
    def success(data=None, message="操作成功", code=200):
        """
        返回成功响应
        
        Args:
            data: 返回的数据内容
            message: 成功消息
            code: 状态码，默认200
            
        Returns:
            Response: 标准成功响应格式
        """
        response_data = {
            'code': code,
            'message': message,
            'data': data
        }
        return Response(response_data, status=status.HTTP_200_OK)
    
    # 错误响应
    @staticmethod
    def error(message="操作失败", code=500, data=None, http_status=status.HTTP_500_INTERNAL_SERVER_ERROR):
        """
        返回错误响应
        
        Args:
            message: 错误消息
            code: 错误码
            data: 额外的错误数据
            http_status: HTTP状态码
            
        Returns:
            Response: 标准错误响应格式
        """
        response_data = {
            'code': code,
            'message': message,
            'data': data
        }
        return Response(response_data, status=http_status)
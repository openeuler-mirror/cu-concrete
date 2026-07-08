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
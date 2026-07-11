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
    
   # 参数错误
    @staticmethod
    def bad_request(message="请求参数错误", data=None):
        """
        返回400错误响应
        
        Args:
            message: 错误消息
            data: 额外的错误数据
            
        Returns:
            Response: 400错误响应
        """
        return ApiResponse.error(
            message=message, 
            code=400, 
            data=data, 
            http_status=status.HTTP_400_BAD_REQUEST
        )
        
    # 未找到
    @staticmethod
    def not_found(message="资源未找到", data=None):
        """
        返回404错误响应
        
        Args:
            message: 错误消息
            data: 额外的错误数据
            
        Returns:
            Response: 404错误响应
        """
        return ApiResponse.error(
            message=message, 
            code=404, 
            data=data, 
            http_status=status.HTTP_404_NOT_FOUND
        )
        
    # 服务器内部错误
    @staticmethod
    def server_error(message="服务器内部错误", data=None):
        """
        返回500错误响应
        
        Args:
            message: 错误消息
            data: 额外的错误数据
            
        Returns:
            Response: 500错误响应
        """
        return ApiResponse.error(
            message=message, 
            code=500, 
            data=data, 
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
# 预定义的常用响应
class CommonResponses:
    """常用的预定义响应"""
    
    # 查询相关
    QUERY_SUCCESS = lambda data=None, message="查询成功": ApiResponse.success(data, message)
    QUERY_FAILED = lambda msg="查询失败": ApiResponse.error(msg, 500)
    
    # 操作相关
    OPERATION_SUCCESS = lambda data=None, message="操作成功": ApiResponse.success(data, message)
    OPERATION_FAILED = lambda msg="操作失败": ApiResponse.error(msg, 500)

    # 文件相关
    FILE_NOT_FOUND = lambda msg="文件不存在": ApiResponse.not_found(msg)
    FILE_ACCESS_DENIED = lambda msg="无权访问文件": ApiResponse.error(msg, 403, http_status=status.HTTP_403_FORBIDDEN)
    
    # 参数相关
    MISSING_PARAMETER = lambda param: ApiResponse.bad_request(f"缺少必要参数: {param}")
    INVALID_PARAMETER = lambda param: ApiResponse.bad_request(f"无效参数: {param}")
    
    # 冲突/并发相关
    CONFLICT = lambda msg="操作冲突": ApiResponse.error(msg, 409, http_status=status.HTTP_409_CONFLICT)
    
    # 资源相关
    RESOURCE_NOT_FOUND = lambda msg="资源不存在": ApiResponse.not_found(msg)

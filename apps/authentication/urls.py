from django.urls import path
from .api_views import (
    LoginAPIView,
    LogoutAPIView,
    UserProfileAPIView,
    ChangePasswordAPIView
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # Theo BM01:
    # POST /api/xac-thuc/ - Đăng nhập
    path('', LoginAPIView.as_view(), name='api_login'),
    
    # POST /api/xac-thuc/logout - Đăng xuất
    path('logout/', LogoutAPIView.as_view(), name='api_logout'),
    
    # GET /api/xac-thuc/profile - Thông tin người dùng
    path('profile/', UserProfileAPIView.as_view(), name='api_profile'),
    
    # PUT /api/xac-thuc/changepass - Đổi mật khẩu
    path('changepass/', ChangePasswordAPIView.as_view(), name='api_changepass'),
    
    # (Bổ sung) Refresh token cho FE
    path('refresh/', TokenRefreshView.as_view(), name='api_token_refresh'),
]

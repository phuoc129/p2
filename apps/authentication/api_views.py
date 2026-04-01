from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer
)

User = get_user_model()


# ============================================================
# 1. ĐĂNG NHẬP API (POST /api/xac-thuc/)
# ============================================================
class LoginAPIView(TokenObtainPairView):
    """
    Theo BM01: POST /api/xac-thuc/
    Nhận username, password. 
    Trả về token (access, refresh) và userId, hoTen, vaiTro.
    """
    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer


# ============================================================
# 2. ĐĂNG XUẤT API (POST /api/xac-thuc/logout)
# ============================================================
class LogoutAPIView(APIView):
    """
    Theo BM01: POST /api/xac-thuc/logout
    Vô hiệu hóa refresh_token.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh_token")
            if not refresh_token:
                return Response(
                    {"message": "Vui lòng cung cấp refresh_token"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {"message": "Đăng xuất thành công"}, 
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"message": "Refresh token không hợp lệ hoặc đã bị vô hiệu hóa"}, 
                status=status.HTTP_400_BAD_REQUEST
            )


# ============================================================
# 3. THÔNG TIN CÁ NHÂN API (GET /api/xac-thuc/profile)
# ============================================================
class UserProfileAPIView(generics.RetrieveAPIView):
    """
    Theo BM01: GET /api/xac-thuc/profile
    Yêu cầu: Header mang Bearer Token.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user


# ============================================================
# 4. ĐỔI MẬT KHẨU API (PUT /api/xac-thuc/changepass)
# ============================================================
class ChangePasswordAPIView(APIView):
    """
    Theo BM01: PUT /api/xac-thuc/changepass
    Yêu cầu: Header mang Bearer Token.
    """
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            old_password = serializer.validated_data.get("old_password")
            new_password = serializer.validated_data.get("new_password")

            if not user.check_password(old_password):
                return Response(
                    {"message": "Mật khẩu cũ không chính xác"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Cập nhật mật khẩu mới
            user.set_password(new_password)
            user.save()

            return Response(
                {"message": "Đổi mật khẩu thành công"}, 
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

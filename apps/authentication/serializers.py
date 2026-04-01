"""
Serializers cho Authentication - theo BM01
Payload JWT chứa: userId, hoTen, vaiTro (theo BM01 mục 2 ☑)
"""
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


# ============================================================
# JWT CUSTOM PAYLOAD - Thêm hoTen, vaiTro vào token (theo BM01)
# ============================================================
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Ghi đè token mặc định để thêm userId, hoTen, vaiTro vào payload.
    Theo BM01 mục 2: ☑ userId  ☑ hoTen  ☑ vaiTro
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Thêm các trường tùy chỉnh vào payload JWT
        token['userId'] = str(user.id)
        token['hoTen'] = user.full_name or user.username
        token['vaiTro'] = user.role

        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        # Thêm thông tin người dùng vào response body (ngoài token)
        # Response theo BM01: { "access": "...", "refresh": "...", "vaiTro": "..." }
        data['vaiTro'] = self.user.role
        data['userId'] = str(self.user.id)
        data['hoTen'] = self.user.full_name or self.user.username

        return data


# ============================================================
# PROFILE SERIALIZER - Trả về thông tin cá nhân theo BM01
# Response: { "userId": 1, "username": "...", "hoTen": "...", "vaiTro": "..." }
# ============================================================
class UserProfileSerializer(serializers.ModelSerializer):
    hoTen = serializers.CharField(source='full_name')
    vaiTro = serializers.CharField(source='role')
    userId = serializers.UUIDField(source='id')

    class Meta:
        model = User
        fields = ['userId', 'username', 'hoTen', 'vaiTro', 'phone_number', 'email']
        read_only_fields = fields


# ============================================================
# CHANGE PASSWORD SERIALIZER - Đổi mật khẩu theo BM01
# Request: { "old_password": "...", "new_password": "..." }
# ============================================================
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=6)

    def validate_new_password(self, value):
        if len(value) < 6:
            raise serializers.ValidationError("Mật khẩu mới phải có ít nhất 6 ký tự.")
        return value

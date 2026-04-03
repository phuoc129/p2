from rest_framework import serializers
from .models import Category, Product, ProductUnit


class CategorySerializer(serializers.ModelSerializer):
    """Serializer cho danh mục sản phẩm"""
    
    class Meta:
        model = Category
        fields = ['id', 'name']
    
    def validate_name(self, value):
        if value and len(value) < 2:
            raise serializers.ValidationError("Tên danh mục phải có ít nhất 2 ký tự.")
        if value and len(value) > 255:
            raise serializers.ValidationError("Tên danh mục không được vượt quá 255 ký tự.")
        return value


class ProductUnitSerializer(serializers.ModelSerializer):
    """Serializer cho đơn vị sản phẩm"""
    
    class Meta:
        model = ProductUnit
        fields = ['id', 'product', 'unit_name', 'conversion_rate']
    
    def validate_unit_name(self, value):
        if value and len(value) < 1:
            raise serializers.ValidationError("Tên đơn vị không được để trống.")
        return value
    
    def validate_conversion_rate(self, value):
        if value and value <= 0:
            raise serializers.ValidationError("Tỷ lệ chuyển đổi phải lớn hơn 0.")
        if value and value > 1000000:
            raise serializers.ValidationError("Tỷ lệ chuyển đổi quá lớn.")
        return value


class ProductSerializer(serializers.ModelSerializer):
    """Serializer cho sản phẩm"""
    units = ProductUnitSerializer(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'category', 'base_price', 'base_unit', 'image_url', 'units']
    
    def validate_name(self, value):
        if value and len(value) < 2:
            raise serializers.ValidationError("Tên sản phẩm phải có ít nhất 2 ký tự.")
        return value
    
    def validate_base_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Giá não được âm.")
        return value
    
    def validate_base_unit(self, value):
        if value and len(value) < 1:
            raise serializers.ValidationError("Đơn vị gốc không được để trống.")
        return value
    
    def validate_image_url(self, value):
        if value and not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("URL hình ảnh phải bắt đầu bằng http:// hoặc https://.")
        return value

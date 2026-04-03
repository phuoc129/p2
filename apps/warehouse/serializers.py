from rest_framework import serializers
from django.core.validators import MinValueValidator
from .models import ImportReceipt, ImportReceiptItem, ExportReceipt, ExportReceiptItem, ProductStock


class ImportReceiptItemSerializer(serializers.ModelSerializer):
    """Serializer cho chi tiết phiếu nhập"""
    
    class Meta:
        model = ImportReceiptItem
        fields = ['id', 'product', 'quantity', 'unit_price', 'note']
    
    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Số lượng phải lớn hơn 0.")
        if value > 999999:
            raise serializers.ValidationError("Số lượng quá lớn.")
        return value
    
    def validate_unit_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Đơn giá không được âm.")
        if value > 9999999:
            raise serializers.ValidationError("Đơn giá quá lớn.")
        return value


class ImportReceiptSerializer(serializers.ModelSerializer):
    """Serializer cho phiếu nhập kho"""
    items = ImportReceiptItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = ImportReceipt
        fields = ['id', 'receipt_code', 'status', 'note', 'created_at', 'items']
    
    def validate_note(self, value):
        if value and len(value) > 500:
            raise serializers.ValidationError("Ghi chú không được vượt quá 500 ký tự.")
        return value


class ExportReceiptItemSerializer(serializers.ModelSerializer):
    """Serializer cho chi tiết phiếu xuất"""
    
    class Meta:
        model = ExportReceiptItem
        fields = ['id', 'product', 'quantity', 'unit_price', 'note']
    
    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Số lượng phải lớn hơn 0.")
        if value > 999999:
            raise serializers.ValidationError("Số lượng quá lớn.")
        return value
    
    def validate_unit_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Đơn giá không được âm.")
        if value > 9999999:
            raise serializers.ValidationError("Đơn giá quá lớn.")
        return value


class ExportReceiptSerializer(serializers.ModelSerializer):
    """Serializer cho phiếu xuất kho"""
    items = ExportReceiptItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = ExportReceipt
        fields = ['id', 'receipt_code', 'status', 'note', 'created_at', 'items']
    
    def validate_note(self, value):
        if value and len(value) > 500:
            raise serializers.ValidationError("Ghi chú không được vượt quá 500 ký tự.")
        return value


class ProductStockSerializer(serializers.ModelSerializer):
    """Serializer cho tồn kho"""
    
    class Meta:
        model = ProductStock
        fields = ['id', 'product', 'quantity', 'last_updated']
    
    def validate_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Số lượng không được âm.")
        return value

"""
apps/product/forms.py - CẬP NHẬT để hỗ trợ upload ảnh thực
Thay thế file cũ bằng file này.
"""
from django import forms
from .models import Product, Category, ProductUnit

CONTROL_CLASS = 'search-input'


class ProductForm(forms.ModelForm):
    # Thêm trường upload ảnh mới (không bắt buộc để có thể sửa sản phẩm mà không cần upload lại)
    anh_san_pham = forms.ImageField(
        required=False,
        label='Ảnh sản phẩm',
        widget=forms.FileInput(attrs={
            'class': 'file-input-hidden',
            'accept': 'image/jpeg,image/png,image/webp',
            'id': 'id_anh_san_pham'
        }),
        error_messages={
            'invalid_image': 'File không phải ảnh hợp lệ.',
        }
    )

    class Meta:
        model = Product
        # Bỏ image_url khỏi fields - sẽ xử lý qua anh_san_pham
        fields = ['name', 'category', 'base_price', 'base_unit']
        labels = {
            'name': 'Tên vật liệu',
            'category': 'Danh mục',
            'base_price': 'Giá cơ bản',
            'base_unit': 'Đơn vị gốc',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': CONTROL_CLASS, 'placeholder': 'VD: Xi măng Hà Tiên'}),
            'category': forms.Select(attrs={'class': CONTROL_CLASS}),
            'base_price': forms.NumberInput(attrs={'class': CONTROL_CLASS, 'step': '0.01'}),
            'base_unit': forms.TextInput(attrs={'class': CONTROL_CLASS, 'placeholder': 'VD: Bao, Cây, m3...'}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        labels = {'name': 'Tên danh mục'}
        widgets = {
            'name': forms.TextInput(attrs={
                'class': CONTROL_CLASS,
                'placeholder': 'VD: Gạch xây dựng, Sắt thép...'
            }),
        }


class ProductUnitForm(forms.ModelForm):
    class Meta:
        model = ProductUnit
        fields = ['product', 'unit_name', 'conversion_rate']
        labels = {
            'product': 'Sản phẩm mục tiêu',
            'unit_name': 'Đơn vị quy đổi',
            'conversion_rate': 'Tỷ lệ quy đổi'
        }
        widgets = {
            'product': forms.Select(attrs={'class': CONTROL_CLASS}),
            'unit_name': forms.TextInput(attrs={'class': CONTROL_CLASS, 'placeholder': 'VD: Tấn, Thùng...'}),
            'conversion_rate': forms.NumberInput(attrs={'class': CONTROL_CLASS, 'step': '0.0001'}),
        }

    def clean_conversion_rate(self):
        rate = self.cleaned_data.get('conversion_rate')
        if rate <= 0:
            raise forms.ValidationError("Tỷ lệ quy đổi phải lớn hơn 0.")
        return rate
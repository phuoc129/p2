from django import forms
from django.core.exceptions import ValidationError
from .models import Product, Category, ProductUnit


# Cấu hình chung cho các Input
CONTROL_CLASS = 'search-input'


class CategoryForm(forms.ModelForm):
    """Form tạo/sửa danh mục"""
    
    class Meta:
        model = Category
        fields = ['name']
        labels = {'name': 'Tên danh mục'}
        widgets = {
            'name': forms.TextInput(attrs={
                'class': CONTROL_CLASS,
                'placeholder': 'VD: Vật liệu xây dựng, Sắt thép...'
            })
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and len(name) < 2:
            raise ValidationError("Tên danh mục phải có ít nhất 2 ký tự.")
        if name and len(name) > 255:
            raise ValidationError("Tên danh mục không được vượt quá 255 ký tự.")
        return name


class ProductForm(forms.ModelForm):
    """Form tạo/sửa sản phẩm"""
    
    class Meta:
        model = Product
        fields = ['name', 'category', 'base_price', 'base_unit', 'image_url']
        labels = {
            'name': 'Tên vật liệu',
            'category': 'Danh mục',
            'base_price': 'Giá cơ bản',
            'base_unit': 'Đơn vị gốc',
            'image_url': 'Link hình ảnh'
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': CONTROL_CLASS, 'placeholder': 'VD: Xi măng Hà Tiên'}),
            'category': forms.Select(attrs={'class': CONTROL_CLASS}),
            'base_price': forms.NumberInput(attrs={'class': CONTROL_CLASS, 'step': '0.01', 'min': '0'}),
            'base_unit': forms.TextInput(attrs={'class': CONTROL_CLASS, 'placeholder': 'VD: Bao, Cây, m3...'}),
            'image_url': forms.TextInput(attrs={'class': CONTROL_CLASS, 'placeholder': 'https://...'})
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name and len(name) < 2:
            raise ValidationError("Tên sản phẩm phải có ít nhất 2 ký tự.")
        return name
    
    def clean_base_price(self):
        price = self.cleaned_data.get('base_price')
        if price and price < 0:
            raise ValidationError("Giá không được âm.")
        return price
    
    def clean_base_unit(self):
        unit = self.cleaned_data.get('base_unit')
        if unit and len(unit) < 1:
            raise ValidationError("Đơn vị gốc không được để trống.")
        return unit
    
    def clean_image_url(self):
        url = self.cleaned_data.get('image_url')
        if url and not url.startswith(('http://', 'https://')):
            raise ValidationError("URL hình ảnh phải bắt đầu bằng http:// hoặc https://.")
        return url


class ProductUnitForm(forms.ModelForm):
    """Form tạo/sửa đơn vị sản phẩm"""
    
    class Meta:
        model = ProductUnit
        fields = ['product', 'unit_name', 'conversion_rate']
        labels = {
            'product': 'Sản phẩm',
            'unit_name': 'Tên đơn vị',
            'conversion_rate': 'Tỷ lệ chuyển đổi'
        }
        widgets = {
            'product': forms.Select(attrs={'class': CONTROL_CLASS}),
            'unit_name': forms.TextInput(attrs={
                'class': CONTROL_CLASS,
                'placeholder': 'VD: Bao, Cây, m3...'
            }),
            'conversion_rate': forms.NumberInput(attrs={
                'class': CONTROL_CLASS,
                'step': '0.0001',
                'min': '0.0001'
            })
        }
    
    def clean_unit_name(self):
        unit_name = self.cleaned_data.get('unit_name')
        if unit_name and len(unit_name) < 1:
            raise ValidationError("Tên đơn vị không được để trống.")
        return unit_name
    
    def clean_conversion_rate(self):
        rate = self.cleaned_data.get('conversion_rate')
        if rate and rate <= 0:
            raise ValidationError("Tỷ lệ chuyển đổi phải lớn hơn 0.")
        if rate and rate > 1000000:
            raise ValidationError("Tỷ lệ chuyển đổi quá lớn.")
        return rate

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

        """Đảm bảo tỷ lệ quy đổi phải lớn hơn 0"""

        rate = self.cleaned_data.get('conversion_rate')

        if rate <= 0:

            raise forms.ValidationError("Tỷ lệ quy đổi phải lớn hơn 0.")

        return rate
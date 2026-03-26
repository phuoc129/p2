from django import forms

from .models import Product, Category, ProductUnit



# Cấu hình chung cho các Input để có giao diện đồng bộ

CONTROL_CLASS = 'search-input' # Sử dụng class CSS từ file base.html của bạn



class ProductForm(forms.ModelForm):

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

            'base_price': forms.NumberInput(attrs={'class': CONTROL_CLASS, 'step': '0.01'}),

            'base_unit': forms.TextInput(attrs={'class': CONTROL_CLASS, 'placeholder': 'VD: Bao, Cây, m3...'}),

            'image_url': forms.TextInput(attrs={'class': CONTROL_CLASS, 'placeholder': 'https://...'}),

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

        """Đảm bảo tỷ lệ quy đổi phải lớn hơn 0"""

        rate = self.cleaned_data.get('conversion_rate')

        if rate <= 0:

            raise forms.ValidationError("Tỷ lệ quy đổi phải lớn hơn 0.")

        return rate
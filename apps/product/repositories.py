from django.db import transaction
from django.shortcuts import get_object_or_404
from django.db.models import Count
from .models import Category, Product, ProductUnit

class CategoryRepository:
    model = Category

    def get_all(self):
        # Annotate giúp lấy count sản phẩm cực nhanh bằng 1 câu SQL
        return self.model.objects.annotate(product_count=Count('products')).all()

    def get_by_id(self, category_id):
        return get_object_or_404(self.model, pk=category_id)

    def create(self, name):
        return self.model.objects.create(name=name)

class ProductRepository:
    model = Product

    def get_all(self):
        # Dùng select_related để JOIN bảng Category ngay lập tức
        return self.model.objects.select_related('category').prefetch_related('units').all()

    def get_by_id(self, product_id):
        return get_object_or_404(self.model.objects.select_related('category'), pk=product_id)

    @transaction.atomic
    def create_product_full(self, product_data, units_list=None):
        """
        Tạo sản phẩm và danh sách đơn vị quy đổi trong 1 transaction.
        units_list: list of dict [{'unit_name': 'Thùng', 'conversion_rate': 10}]
        """
        # Tạo sản phẩm
        product = self.model.objects.create(**product_data)
        
        # Nếu có đơn vị đi kèm thì tạo luôn
        if units_list:
            units = [
                ProductUnit(product=product, **unit) 
                for unit in units_list
            ]
            ProductUnit.objects.bulk_create(units)
            
        return product

    def update(self, product_id, data):
        # Cập nhật thông minh: chỉ update những field có trong data
        product = self.get_by_id(product_id)
        for key, value in data.items():
            setattr(product, key, value)
        product.save()
        return product

    def get_product_units(self, product_id):
        return ProductUnit.objects.filter(product_id=product_id).order_by('conversion_rate')
"""
apps/product/views.py - CẬP NHẬT để xử lý upload ảnh sản phẩm
Thay thế file cũ bằng file này.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages

from .forms import ProductForm, CategoryForm, ProductUnitForm
from .services import ProductService, CategoryService

# Import middleware upload mới
from middlewares.upload_middleware import xu_ly_va_luu_anh, xoa_anh_cu
from .validators import ProductValidator, CategoryValidator, ProductUnitValidator


# ==========================================
# 1. QUẢN LÝ SẢN PHẨM (PRODUCT)
# ==========================================
class ProductListView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'product.view_product'
    raise_exception = True

    def get(self, request):
        service = ProductService()
        cat_service = CategoryService()

        search_query = request.GET.get('search')
        category_id = request.GET.get('category')

        queryset = service.get_all_products(search=search_query, category=category_id)

        return render(request, 'product/product_list.html', {
            'products': queryset,
            'categories': cat_service.get_list(),
        })


class ProductDetailView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'product.view_product'
    raise_exception = True

    def get(self, request, pk):
        service = ProductService()
        product = service.repository.get_by_id(pk)
        units = service.unit_repository.get_by_product(pk)

        return render(request, 'product/detail.html', {
            'product': product,
            'units': units
        })


class ProductCreateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'product.add_product'
    raise_exception = True

    def post_create(self, request):
        from .validators import ProductValidator
        from middlewares.upload_middleware import xu_ly_va_luu_anh
        from .services import ProductService
        from django.contrib import messages
        from django.shortcuts import redirect
 
        # 1. Validate trước khi làm bất cứ điều gì
        errors = ProductValidator.validate_create(request.POST)
        if errors:
            for field, msg in errors.items():
                messages.error(request, f'{msg}')
            return redirect('product:product_list')
 
        form_data = request.POST.dict()
        form_data.pop('csrfmiddlewaretoken', None)
 
        # 2. Xử lý upload ảnh nếu có
        file_anh = request.FILES.get('anh_san_pham')
        if file_anh:
            try:
                duong_dan_anh = xu_ly_va_luu_anh(file_anh, thu_muc_con='san-pham')
                form_data['image_url'] = duong_dan_anh
            except ValueError as e:
                messages.error(request, f'Lỗi ảnh: {str(e)}')
                return redirect('product:product_list')
 
        service = ProductService()
        service.create_product(form_data)
        messages.success(request, 'Tạo sản phẩm thành công!')
        return redirect('product:product_list')


class ProductUpdateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'product.change_product'
    raise_exception = True

    def post_update(self, request, pk):
        from .validators import ProductValidator
        from middlewares.upload_middleware import xu_ly_va_luu_anh, xoa_anh_cu
        from .services import ProductService
        from django.contrib import messages
        from django.shortcuts import redirect
 
        errors = ProductValidator.validate_update(request.POST.dict())
        if errors:
            for field, msg in errors.items():
                messages.error(request, msg)
            return redirect('product:product_list')
 
        service = ProductService()
        product = service.repository.get_by_id(pk)
        form_data = request.POST.dict()
        form_data.pop('csrfmiddlewaretoken', None)
 
        file_anh = request.FILES.get('anh_san_pham')
        if file_anh:
            try:
                xoa_anh_cu(product.image_url)
                duong_dan_anh = xu_ly_va_luu_anh(file_anh, thu_muc_con='san-pham')
                form_data['image_url'] = duong_dan_anh
            except ValueError as e:
                messages.error(request, f'Lỗi ảnh: {str(e)}')
                return redirect('product:product_list')
        else:
            form_data['image_url'] = product.image_url
 
        service.repository.update(product, form_data)
        messages.success(request, 'Cập nhật sản phẩm thành công!')
        return redirect('product:product_list')


class ProductDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'product.delete_product'
    raise_exception = True

    def post(self, request, pk):
        service = ProductService()
        product = service.repository.get_by_id(pk)

        if product:
            # Xóa ảnh khi xóa sản phẩm (dọn dẹp file trên server)
            xoa_anh_cu(product.image_url)
            service.repository.delete(product)
            messages.warning(request, 'Đã xóa sản phẩm thành công.')
        else:
            messages.error(request, 'Không tìm thấy sản phẩm để xóa.')

        return redirect('product:product_list')


# ==========================================
# 2. QUẢN LÝ DANH MỤC (CATEGORY)
# ==========================================
class CategoryListView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'product.view_category'
    raise_exception = True

    def post_category_create(self, request):
        from .validators import CategoryValidator
        from .services import CategoryService
        from django.contrib import messages
        from django.shortcuts import redirect
 
        data = {'name': request.POST.get('name', '')}
        errors = CategoryValidator.validate_create(data)
        if errors:
            for field, msg in errors.items():
                messages.error(request, msg)
            return redirect('product:category_list')
 
        service = CategoryService()
        category, msg = service.create_category(data['name'])
        if category:
            messages.success(request, 'Đã thêm danh mục mới thành công!')
        else:
            messages.error(request, msg)
 
        return redirect('product:category_list')


class CategoryUpdateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'product.change_category'
    raise_exception = True

    def post(self, request, pk):
        service = CategoryService()
        category = service.repository.get_by_id(pk)
        name = request.POST.get('name')

        if name:
            service.repository.update(category, name)
            messages.success(request, 'Cập nhật danh mục thành công!')
        else:
            messages.error(request, 'Tên danh mục không được để trống.')

        return redirect('product:category_list')


class CategoryDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'product.delete_category'
    raise_exception = True

    def post(self, request, pk):
        service = CategoryService()
        category = service.repository.get_by_id(pk)

        if category.products.exists():
            messages.error(request, 'Không thể xóa danh mục đang có sản phẩm!')
        else:
            service.repository.delete(category)
            messages.warning(request, 'Đã xóa danh mục.')

        return redirect('product:category_list')


# ==========================================
# 3. QUẢN LÝ ĐƠN VỊ TÍNH (PRODUCT UNIT)
# ==========================================
class ProductUnitListView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'product.view_productunit'
    raise_exception = True

    def get(self, request):
        service = ProductService()
        units = service.unit_repository.get_all()
        products = service.repository.get_all()

        return render(request, 'units/unit_list.html', {
            'units': units,
            'products': products,
            'title': 'Quản lý Đơn vị & Quy đổi'
        })


class ProductUnitCreateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'product.add_productunit'
    raise_exception = True

    def post_unit_create(self, request):
        from .validators import ProductUnitValidator
        from .services import ProductService
        from django.contrib import messages
        from django.shortcuts import redirect
 
        data = {
            'unit_name': request.POST.get('unit_name', ''),
            'conversion_rate': request.POST.get('conversion_rate', ''),
            'product_id': request.POST.get('product_id', ''),
        }
 
        errors = ProductUnitValidator.validate_create(data)
        if errors:
            for field, msg in errors.items():
                messages.error(request, msg)
            return redirect('product:units_list')
 
        service = ProductService()
        unit, msg = service.add_new_unit_to_product(
            data['product_id'],
            data['unit_name'],
            data['conversion_rate'],
        )
 
        if unit:
            messages.success(request, f"Đã thêm đơn vị {data['unit_name']} thành công.")
        else:
            messages.error(request, msg)
 
        return redirect('product:units_list')


class ProductUnitUpdateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'product.change_productunit'
    raise_exception = True

    def post(self, request, pk):
        service = ProductService()
        unit = service.unit_repository.get_by_id(pk)

        if not unit:
            messages.error(request, "Không tìm thấy đơn vị tính.")
            return redirect('product:units_list')

        unit_name = request.POST.get('unit_name')
        conversion_rate = request.POST.get('conversion_rate')

        if unit_name and conversion_rate:
            service.unit_repository.update(unit, {
                'unit_name': unit_name,
                'conversion_rate': conversion_rate
            })
            messages.success(request, 'Cập nhật thành công!')
        else:
            messages.error(request, 'Vui lòng điền đủ thông tin.')

        return redirect('product:units_list')


class ProductUnitDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'product.delete_productunit'
    raise_exception = True

    def post(self, request, pk):
        service = ProductService()

        if service.unit_repository.delete(pk):
            messages.warning(request, 'Đã xóa đơn vị tính thành công.')
        else:
            messages.error(request, 'Không tìm thấy đơn vị tính để xóa.')

        return redirect('product:units_list')
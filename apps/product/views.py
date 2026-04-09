from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.paginator import Paginator
from django.contrib import messages

from .forms import ProductForm, CategoryForm, ProductUnitForm
from .services import ProductService, CategoryService


def _get_stock_map():
    """Lấy dict {product_id: quantity} từ tồn kho"""
    try:
        from apps.warehouse.models import ProductStock
        stocks = ProductStock.objects.all().values('product_id', 'quantity')
        return {str(s['product_id']): float(s['quantity']) for s in stocks}
    except Exception:
        return {}


# ==========================================
# 1. QUẢN LÝ SẢN PHẨM (PRODUCT)
# ==========================================
class ProductListView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'product.view_product'
    raise_exception = True

    def get(self, request):
        service = ProductService()
        cat_service = CategoryService()

        search_query = request.GET.get('search', '').strip()
        category_id = request.GET.get('category', '')
        page_number = request.GET.get('page', 1)

        queryset = service.get_all_products(
            search=search_query if search_query else None,
            category=category_id if category_id else None
        )

        paginator = Paginator(queryset, 5)
        page_obj = paginator.get_page(page_number)

        stock_map = _get_stock_map()

        return render(request, 'product/product_list.html', {
            'products': page_obj,
            'categories': cat_service.get_list(),
            'tong_so_luong': paginator.count,
            'search_query': search_query,
            'category_id': category_id,
            'paginator': paginator,
            'page_obj': page_obj,
            'stock_map_json': __import__('json').dumps(stock_map),
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

    def post(self, request):
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            service = ProductService()
            service.create_product(form.cleaned_data)
            messages.success(request, 'Tạo sản phẩm thành công!')
        else:
            messages.error(request, 'Dữ liệu không hợp lệ, vui lòng kiểm tra lại.')

        return redirect('product:product_list')


class ProductUpdateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'product.change_product'
    raise_exception = True

    def post(self, request, pk):
        service = ProductService()
        product = service.repository.get_by_id(pk)
        form = ProductForm(request.POST, request.FILES, instance=product)

        if form.is_valid():
            service.repository.update(product, form.cleaned_data)
            messages.success(request, 'Cập nhật sản phẩm thành công!')
        else:
            messages.error(request, 'Lỗi cập nhật. Vui lòng kiểm tra lại thông tin.')

        return redirect('product:product_list')


class ProductDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'product.delete_product'
    raise_exception = True

    def post(self, request, pk):
        service = ProductService()
        product = service.repository.get_by_id(pk)

        if product:
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

    def get(self, request):
        service = CategoryService()
        categories = service.get_list()

        return render(request, 'categories/category_list.html', {
            'categories': categories,
            'form': CategoryForm()
        })

    def post(self, request):
        form = CategoryForm(request.POST)
        if form.is_valid():
            service = CategoryService()
            category, msg = service.create_category(form.cleaned_data['name'])

            if category:
                messages.success(request, 'Đã thêm danh mục mới thành công!')
            else:
                messages.error(request, msg)
        else:
            messages.error(request, "Dữ liệu không hợp lệ, vui lòng kiểm tra lại.")

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

    def post(self, request):
        service = ProductService()
        product_id = request.POST.get('product_id')
        unit_name = request.POST.get('unit_name')
        rate = request.POST.get('conversion_rate')

        if not product_id or not unit_name or not rate:
            messages.error(request, "Vui lòng nhập đầy đủ thông tin.")
            return redirect('product:units_list')

        unit, msg = service.add_new_unit_to_product(product_id, unit_name, rate)

        if unit:
            messages.success(request, f'Đã thêm đơn vị {unit_name} thành công.')
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
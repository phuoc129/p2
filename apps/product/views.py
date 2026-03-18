from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.contrib import messages
from .models import Product
from .forms import ProductForm
from apps.core.exceptions import LoiKhongTimThay, LoiDuLieuKhongHopLe

class ProductListView(View):
    """Lấy danh sách sản phẩm (layDanhSach)"""
    def get(self, request):
        trang_hien_tai = request.GET.get('trang', 1)
        so_luong = request.GET.get('soLuong', 10)
        
        # Gọi qua Repository/Service (ở đây viết gọn bằng ORM)
        queryset = Product.objects.all().order_by('-id')
        
        paginator = Paginator(queryset, so_luong)
        page_obj = paginator.get_page(trang_hien_tai)

        return render(request, 'product/index.html', {
            'products': page_obj,
            'tong_so_luong': paginator.count
        })

class ProductDetailView(View):
    """Lấy chi tiết sản phẩm (layChiTiet)"""
    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        return render(request, 'product/detail.html', {'product': product})

class ProductCreateView(LoginRequiredMixin, View):
    """Tạo sản phẩm mới (taoMoi)"""
    def get(self, request):
        form = ProductForm()
        return render(request, 'product/form.html', {'form': form, 'title': 'Thêm sản phẩm'})

    def post(self, request):
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tạo sản phẩm thành công!')
            return redirect('product:index')
        return render(request, 'product/form.html', {'form': form})

class ProductUpdateView(LoginRequiredMixin, View):
    """Cập nhật sản phẩm (capNhat)"""
    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        form = ProductForm(instance=product)
        return render(request, 'product/form.html', {'form': form, 'title': 'Chỉnh sửa sản phẩm'})

    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cập nhật thành công!')
            return redirect('product:detail', pk=pk)
        return render(request, 'product/form.html', {'form': form})

class ProductDeleteView(LoginRequiredMixin, View):
    """Xóa sản phẩm (xoa)"""
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        product.delete()
        messages.warning(request, f'Đã xóa sản phẩm {product.name}')
        return redirect('product:index')
    

import json
import uuid
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.db import connections
from django.db.utils import OperationalError
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

# --- IMPORT TẦNG SERVICE ---
from apps.authentication.services import UserService
from apps.product.models import ProductUnit, Product # Mở comment và đảm bảo path đúng

# ==========================================
# 1. HỆ THỐNG & SỨC KHỎE (HEALTH CHECK)
# ==========================================
def health_check(request):
    health_status = {"api": "ok", "database": "ok"}
    status_code = 200
    try:
        db_conn = connections['default']
        db_conn.cursor()
    except OperationalError:
        health_status["database"] = "disconnected"
        status_code = 503
    except Exception as e:
        health_status["database"] = "error"
        health_status["details"] = str(e)
        status_code = 500
    return JsonResponse(health_status, status=status_code)

# ==========================================
# 2. XÁC THỰC NGƯỜI DÙNG (KẾT NỐI SERVICE)
# ==========================================
def login_view(request):
    # Nếu đã đăng nhập rồi thì vào thẳng Dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Gọi Service để xử lý xác thực
        auth_service = UserService()
        user = auth_service.login_service(request, username, password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Chào mừng trở lại, {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Tên đăng nhập hoặc mật khẩu không đúng hoặc tài khoản bị khóa.')
            
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

# ==========================================
# 3. HÀM BỔ TRỢ (SỬ DỤNG TRƯỜNG ROLE MỚI)
# ==========================================
def _base_context(request):
    """Lấy thông tin hiển thị dựa trên Custom User Model."""
    user = request.user
    role_name = "Thành viên"
    
    if user.is_authenticated:
        # Tận dụng trường 'role' trực tiếp từ Model User bạn đã tạo
        roles_map = {
            'ADMIN': 'Quản trị viên',
            'KHO': 'Thủ kho',
            'SALE': 'Nhân viên bán hàng',
            'KE_TOAN': 'Kế toán',
        }
        # Lấy tên hiển thị Tiếng Việt từ Map, nếu không có thì dùng giá trị gốc
        current_role = 'ADMIN' if user.is_superuser else user.role
        role_name = roles_map.get(current_role, current_role)

    return {
        'user_full_name': getattr(user, 'full_name', user.username) if user.is_authenticated else "Khách",
        'user_initial': user.username[0].upper() if user.is_authenticated else '?',
        'user_role': role_name,
    }

# ==========================================
# 4. CÁC TRANG TỔNG QUAN (DASHBOARD)
# ==========================================
@login_required
def dashboard_view(request):
    # Dữ liệu mẫu cho Dashboard
    stats = [
        {'label': 'Tổng đơn hàng', 'value': '1,284', 'change': '+12.5%', 'is_positive': True},
        {'label': 'Doanh thu tháng', 'value': '452M đ', 'change': '+8.2%', 'is_positive': True},
        {'label': 'Đang xử lý', 'value': '48', 'change': '-2.4%', 'is_positive': False},
        {'label': 'Tỷ lệ hoàn thành', 'value': '94.2%', 'change': '+1.1%', 'is_positive': True},
    ]

    orders = [
        {'ma_don': '#ORD-7721', 'khach_hang': 'Nguyễn Văn A', 'vat_lieu': 'Xi măng Hà Tiên', 'ngay_tao': '07/03/2026', 'trang_thai': 'Đang xử lý', 'trang_thai_class': 'processing', 'dot_color': '#f59e0b', 'tong_tien': '1,200,000đ'},
        {'ma_don': '#ORD-7722', 'khach_hang': 'Trần Thị B', 'vat_lieu': 'Sắt phi 16', 'ngay_tao': '06/03/2026', 'trang_thai': 'Đã giao', 'trang_thai_class': 'done', 'dot_color': '#22c55e', 'tong_tien': '850,000đ'},
    ]

    context = {
        **_base_context(request),
        'stats': stats,
        'orders': orders,
        'total_orders': 1284,
        'page_range': range(1, 4),
        'current_page': 1,
    }
    return render(request, 'dashboard.html', context)

# ==========================================
# 5. QUẢN LÝ NGHIỆP VỤ (DÙNG LOGIN_REQUIRED)
# ==========================================
@login_required
def product_view(request):
    return render(request, 'Product.html', _base_context(request))

@login_required
def units_view(request):
    """Trang hiển thị Đơn vị quy đổi (AJAX)"""
    # Lấy dữ liệu thực từ DB để truyền cho giao diện AJAX
    unit_list = ProductUnit.objects.select_related('product').all()
    units_data = [{
        'id': str(u.id),
        'unit_name': u.unit_name,
        'conversion_rate': float(u.conversion_rate),
        'product_name': u.product.name,
        'base_unit': u.product.base_unit
    } for u in unit_list]

    product_list = Product.objects.all()
    Product_data = [{
        'id': str(p.id),
        'name': p.name,
        'base_unit': p.base_unit
    } for p in product_list]

    context = {
        **_base_context(request),
        'units_json': units_data,
        'Product_json': Product_data,
    }
    return render(request, 'units.html', context)
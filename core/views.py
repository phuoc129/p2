import json
import uuid
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.db import connections
from django.db.utils import OperationalError
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

# Đảm bảo tên Model khớp với cấu trúc Database của bạn
from .models import ProductUnits, Products 

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
# 2. XÁC THỰC NGƯỜI DÙNG (AUTHENTICATION)
# ==========================================
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Tên đăng nhập hoặc mật khẩu không đúng.')
            
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

# ==========================================
# 3. HÀM BỔ TRỢ (UTILITIES)
# ==========================================
def _base_context(request):
    """Context dùng chung cho Sidebar và Thông tin người dùng."""
    user = request.user
    role_name = "Thành viên"
    
    if user.is_authenticated:
        group = user.groups.first()
        if group:
            roles = {
                'admin': 'Quản trị viên',
                'warehouse': 'Thủ kho',
                'sales': 'Nhân viên bán hàng',
                'accountant': 'Kế toán',
            }
            role_name = roles.get(group.name.lower(), group.name)
        elif user.is_superuser:
            role_name = "Quản trị hệ thống"

    return {
        'user_full_name': user.get_full_name() or user.username,
        'user_initial': user.username[0].upper() if user.is_authenticated else '?',
        'user_role': role_name,
    }

# ==========================================
# 4. CÁC TRANG TỔNG QUAN (DASHBOARD)
# ==========================================
@login_required
def dashboard_view(request):
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
# 5. QUẢN LÝ NGHIỆP VỤ (BUSINESS LOGIC)
# ==========================================
@login_required
def products_view(request):
    return render(request, 'products.html', _base_context(request))

@login_required
def categories_view(request):
    return render(request, 'categories.html', _base_context(request))

@login_required
def accounts_view(request):
    return render(request, 'accounts.html', _base_context(request))

# ==========================================
# 6. ĐƠN VỊ & QUY ĐỔI (UNITS - AJAX VERSION)
# ==========================================
@login_required
def units_view(request):
    """Trang hiển thị danh sách Đơn vị quy đổi."""
    
    # 1. Lấy toàn bộ quy đổi từ DB và chuyển sang List dict để hóa JSON
    unit_list = ProductUnits.objects.select_related('product').all()
    units_data = []
    for u in unit_list:
        units_data.append({
            'id': str(u.id),
            'unit_name': u.unit_name,
            'conversion_rate': float(u.conversion_rate),
            'product_id': str(u.product.id),
            'product_name': u.product.name,
            'base_unit': u.product.base_unit
        })

    # 2. Lấy toàn bộ Sản phẩm để đổ vào Dropdown trong Modal
    product_list = Products.objects.all()
    products_data = []
    for p in product_list:
        products_data.append({
            'id': str(p.id),
            'name': p.name,
            'base_unit': p.base_unit
        })

    context = {
        **_base_context(request),
        'units_json': units_data,
        'products_json': products_data,
    }
    return render(request, 'units.html', context)

@login_required
@require_POST
def api_save_unit(request):
    """API lưu hoặc cập nhật đơn vị quy đổi (Giao diện gọi ngầm)"""
    try:
        data = json.loads(request.body)
        unit_id = data.get('id')
        product_id = data.get('product_id')
        unit_name = data.get('unit_name')
        conversion_rate = data.get('conversion_rate')

        product = Products.objects.filter(id=product_id).first()
        if not product:
            return JsonResponse({'success': False, 'message': 'Sản phẩm không tồn tại!'})

        if unit_id:
            unit = ProductUnits.objects.filter(id=unit_id).first()
            if unit:
                unit.product = product
                unit.unit_name = unit_name
                unit.conversion_rate = conversion_rate
                unit.save()
            else:
                return JsonResponse({'success': False, 'message': 'Không tìm thấy đơn vị để sửa!'})
        else:
            ProductUnits.objects.create(
                id=str(uuid.uuid4()), 
                product=product,
                unit_name=unit_name,
                conversion_rate=conversion_rate
            )
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required
@require_POST
def api_delete_unit(request, unit_id):
    """API xóa đơn vị quy đổi (Giao diện gọi ngầm)"""
    try:
        unit = ProductUnits.objects.filter(id=unit_id).first()
        if unit:
            unit.delete()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'message': 'Không tìm thấy đơn vị!'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})
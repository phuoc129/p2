from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.db import connections
from django.db.utils import OperationalError


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


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        if username and password:
            request.session['user_email'] = username
            request.session['user_initial'] = username[0].upper()
            return redirect('dashboard')
        else:
            messages.error(request, 'Vui lòng nhập đầy đủ thông tin.')
    return render(request, 'login.html')


def logout_view(request):
    request.session.flush()
    return redirect('login')


def _require_login(request):
    """Trả về None nếu đã đăng nhập, redirect nếu chưa."""
    if not request.session.get('user_email'):
        return redirect('login')
    return None


def _base_context(request):
    """Context dùng chung cho tất cả trang có sidebar."""
    return {
        'user_email': request.session.get('user_email', 'admin@teliet.vn'),
        'user_initial': request.session.get('user_initial', 'A'),
        'user_role': request.session.get('user_role', 'Quản trị viên'),
    }


def dashboard_view(request):
    check = _require_login(request)
    if check:
        return check

    stats = [
        {'label': 'Tổng đơn hàng', 'value': '1,284', 'change': '+12.5%', 'is_positive': True},
        {'label': 'Doanh thu tháng', 'value': '452M đ', 'change': '+8.2%', 'is_positive': True},
        {'label': 'Đang xử lý', 'value': '48', 'change': '-2.4%', 'is_positive': False},
        {'label': 'Tỷ lệ hoàn thành', 'value': '94.2%', 'change': '+1.1%', 'is_positive': True},
    ]

    orders = [
        {'ma_don': '#ORD-7721', 'khach_hang': 'Nguyễn Văn A', 'vat_lieu': 'Xi măng Hà Tiên', 'ngay_tao': '07/03/2026', 'trang_thai': 'Đang xử lý', 'trang_thai_class': 'processing', 'dot_color': '#f59e0b', 'tong_tien': '1,200,000đ'},
        {'ma_don': '#ORD-7722', 'khach_hang': 'Trần Thị B', 'vat_lieu': 'Sắt phi 16', 'ngay_tao': '06/03/2026', 'trang_thai': 'Đã giao', 'trang_thai_class': 'done', 'dot_color': '#22c55e', 'tong_tien': '850,000đ'},
        {'ma_don': '#ORD-7723', 'khach_hang': 'Lê Minh C', 'vat_lieu': 'Gạch ốp lát', 'ngay_tao': '05/03/2026', 'trang_thai': 'Chờ xác nhận', 'trang_thai_class': 'pending', 'dot_color': '#3b82f6', 'tong_tien': '3,450,000đ'},
        {'ma_don': '#ORD-7724', 'khach_hang': 'Phạm Thị D', 'vat_lieu': 'Cát xây dựng', 'ngay_tao': '04/03/2026', 'trang_thai': 'Đã hủy', 'trang_thai_class': 'cancel', 'dot_color': '#ef4444', 'tong_tien': '620,000đ'},
        {'ma_don': '#ORD-7725', 'khach_hang': 'Hoàng Văn E', 'vat_lieu': 'Tôn lợp mái', 'ngay_tao': '03/03/2026', 'trang_thai': 'Đã giao', 'trang_thai_class': 'done', 'dot_color': '#22c55e', 'tong_tien': '5,200,000đ'},
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


def products_view(request):
    check = _require_login(request)
    if check:
        return check
    return render(request, 'products.html', _base_context(request))


def categories_view(request):
    check = _require_login(request)
    if check:
        return check
    return render(request, 'categories.html', _base_context(request))


def units_view(request):
    check = _require_login(request)
    if check:
        return check
    return render(request, 'units.html', _base_context(request))


def accounts_view(request):
    check = _require_login(request)
    if check:
        return check
    return render(request, 'accounts.html', _base_context(request))
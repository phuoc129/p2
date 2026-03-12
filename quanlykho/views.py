from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.db import connections
from django.db.utils import OperationalError

# --- Hàm cũ của bạn ---
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

# --- CÁC HÀM MỚI CHO GIAO DIỆN ---
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        if email and password:
            request.session['user_email'] = email
            return redirect('dashboard')
        else:
            messages.error(request, 'Vui lòng nhập đầy đủ thông tin.')
    return render(request, 'login.html')

def dashboard_view(request):
    user_email = request.session.get('user_email')
    if not user_email:
        return redirect('login')
        
    # Dữ liệu mẫu cho bảng
    orders = [
        { 'id': '#ORD-7721', 'customer': 'Nguyễn Văn A', 'date': '07/03/2024', 'status': 'Đang xử lý', 'total': '1,200,000đ' },
        { 'id': '#ORD-7722', 'customer': 'Trần Thị B', 'date': '06/03/2024', 'status': 'Đã giao', 'total': '850,000đ' },
    ]
    
    stats = [
        { 'label': 'Tổng đơn hàng', 'value': '1,284', 'change': '+12.5%', 'is_positive': True },
        { 'label': 'Doanh thu', 'value': '452,000,000đ', 'change': '+8.2%', 'is_positive': True },
        { 'label': 'Đang xử lý', 'value': '48', 'change': '-2.4%', 'is_positive': False },
        { 'label': 'Tỷ lệ hoàn thành', 'value': '94.2%', 'change': '+1.1%', 'is_positive': True },
    ]
    
    context = {
        'user_email': user_email,
        'user_initial': user_email[0].upper(),
        'orders': orders,
        'stats': stats
    }
    return render(request, 'dashboard.html', context)

def logout_view(request):
    if 'user_email' in request.session:
        del request.session['user_email']
    return redirect('login')
import json
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse

from apps.product.models import Product
from .services import ImportReceiptService, SalesOrderService


# ─────────────────────────────────────────────────────────────
# HELPER: lấy danh sách sản phẩm JSON để dùng trong template
# ─────────────────────────────────────────────────────────────
def _products_json():
    products = Product.objects.select_related('category').all().order_by('name')
    return [
        {
            'id': str(p.id),
            'name': p.name,
            'base_unit': p.base_unit,
            'base_price': float(p.base_price),
            'category': p.category.name if p.category else '',
        }
        for p in products
    ]


def _stocks_json():
    from .repositories import ProductStockRepository
    stocks = ProductStockRepository.get_all()
    return {str(s.product_id): float(s.quantity) for s in stocks}


# ═══════════════════════════════════════════════════════════════
# NHẬP KHO
# ═══════════════════════════════════════════════════════════════

class ImportReceiptListView(LoginRequiredMixin, View):
    """
    Thủ kho: thấy phiếu của mình
    Kế toán: thấy tất cả phiếu
    """
    def get(self, request):
        service = ImportReceiptService()
        user = request.user

        # Kế toán / Admin xem tất cả; Thủ kho chỉ xem của mình
        if user.role in ('KE_TOAN', 'ADMIN'):
            receipts = service.get_all()
        else:
            receipts = service.get_by_user(user)

        status_filter = request.GET.get('status', '')
        if status_filter:
            receipts = receipts.filter(status=status_filter)

        products_data = _products_json()

        return render(request, 'warehouse/import_receipt_list.html', {
            'receipts': receipts,
            'products_json': json.dumps(products_data, ensure_ascii=False),
            'status_filter': status_filter,
            'user_role': user.role,
        })

    def post(self, request):
        """Thủ kho tạo phiếu nhập mới"""
        if request.user.role not in ('KHO', 'ADMIN'):
            messages.error(request, 'Bạn không có quyền tạo phiếu nhập kho.')
            return redirect('warehouse:import_list')

        service = ImportReceiptService()
        note = request.POST.get('note', '')

        # Parse items từ form
        items_data = _parse_items_from_post(request.POST)

        receipt, error = service.create_receipt(note, items_data, request.user)
        if receipt:
            messages.success(request, f'Đã tạo phiếu nhập {receipt.receipt_code} thành công. Đang chờ kế toán duyệt.')
        else:
            messages.error(request, error)

        return redirect('warehouse:import_list')


class ImportReceiptDetailView(LoginRequiredMixin, View):
    def get(self, request, pk):
        service = ImportReceiptService()
        receipt = service.get_by_id(pk)
        if not receipt:
            messages.error(request, 'Không tìm thấy phiếu nhập kho.')
            return redirect('warehouse:import_list')

        products_data = _products_json()
        return render(request, 'warehouse/import_receipt_detail.html', {
            'receipt': receipt,
            'products_json': json.dumps(products_data, ensure_ascii=False),
            'user_role': request.user.role,
        })


class ImportReceiptApproveView(LoginRequiredMixin, View):
    """Kế toán duyệt phiếu"""
    def post(self, request, pk):
        if request.user.role not in ('KE_TOAN', 'ADMIN'):
            messages.error(request, 'Bạn không có quyền duyệt phiếu.')
            return redirect('warehouse:import_list')

        service = ImportReceiptService()
        success, msg = service.approve_receipt(pk, request.user)
        if success:
            messages.success(request, msg)
        else:
            messages.error(request, msg)
        return redirect('warehouse:import_list')


class ImportReceiptRejectView(LoginRequiredMixin, View):
    """Kế toán từ chối phiếu"""
    def post(self, request, pk):
        if request.user.role not in ('KE_TOAN', 'ADMIN'):
            messages.error(request, 'Bạn không có quyền từ chối phiếu.')
            return redirect('warehouse:import_list')

        service = ImportReceiptService()
        rejection_note = request.POST.get('rejection_note', '')
        success, msg = service.reject_receipt(pk, request.user, rejection_note)
        if success:
            messages.warning(request, msg)
        else:
            messages.error(request, msg)
        return redirect('warehouse:import_list')


class ImportReceiptResubmitView(LoginRequiredMixin, View):
    """Thủ kho sửa lại phiếu bị từ chối và gửi lại"""
    def post(self, request, pk):
        if request.user.role not in ('KHO', 'ADMIN'):
            messages.error(request, 'Bạn không có quyền gửi lại phiếu.')
            return redirect('warehouse:import_list')

        service = ImportReceiptService()
        note = request.POST.get('note', '')
        items_data = _parse_items_from_post(request.POST)

        receipt, error = service.resubmit_receipt(pk, note, items_data, request.user)
        if receipt:
            messages.success(request, f'Đã gửi lại phiếu {receipt.receipt_code}. Đang chờ kế toán duyệt.')
        else:
            messages.error(request, error)
        return redirect('warehouse:import_list')


# ═══════════════════════════════════════════════════════════════
# XUẤT KHO / ĐƠN HÀNG SALE
# ═══════════════════════════════════════════════════════════════

class SalesOrderListView(LoginRequiredMixin, View):
    def get(self, request):
        service = SalesOrderService()
        user = request.user

        if user.role in ('KE_TOAN', 'ADMIN'):
            orders = service.get_all()
        elif user.role == 'SALE':
            orders = service.get_by_user(user)
        else:
            orders = service.get_all()

        products_data = _products_json()
        stocks_data = _stocks_json()

        return render(request, 'warehouse/sales_order_list.html', {
            'orders': orders,
            'products_json': json.dumps(products_data, ensure_ascii=False),
            'stocks_json': json.dumps(stocks_data),
            'user_role': user.role,
        })

    def post(self, request):
        """Sale tạo đơn hàng"""
        if request.user.role not in ('SALE', 'ADMIN'):
            messages.error(request, 'Bạn không có quyền tạo đơn hàng.')
            return redirect('warehouse:sales_list')

        service = SalesOrderService()
        customer_name = request.POST.get('customer_name', '')
        customer_phone = request.POST.get('customer_phone', '')
        note = request.POST.get('note', '')
        items_data = _parse_items_from_post(request.POST)

        order, errors = service.create_order(customer_name, customer_phone, note, items_data, request.user)

        if order:
            messages.success(request, f'Đơn hàng {order.order_code} đã được tạo. Tồn kho đã được trừ tự động.')
        else:
            for err in errors:
                messages.error(request, err['message'])

        return redirect('warehouse:sales_list')


class SalesOrderDetailView(LoginRequiredMixin, View):
    def get(self, request, pk):
        service = SalesOrderService()
        order = service.get_by_id(pk)
        if not order:
            messages.error(request, 'Không tìm thấy đơn hàng.')
            return redirect('warehouse:sales_list')

        return render(request, 'warehouse/sales_order_detail.html', {
            'order': order,
            'user_role': request.user.role,
        })


# ═══════════════════════════════════════════════════════════════
# TỒN KHO
# ═══════════════════════════════════════════════════════════════

class StockListView(LoginRequiredMixin, View):
    def get(self, request):
        service = SalesOrderService()
        stocks = service.get_all_stocks()
        return render(request, 'warehouse/stock_list.html', {
            'stocks': stocks,
            'user_role': request.user.role,
        })


# ─────────────────────────────────────────────────────────────
# HELPER: parse items từ POST form
# ─────────────────────────────────────────────────────────────
def _parse_items_from_post(post_data):
    """
    Form gửi lên: product_id_0, quantity_0, unit_price_0, item_note_0, ...
    """
    items = []
    i = 0
    while True:
        product_id = post_data.get(f'product_id_{i}')
        if product_id is None:
            break
        if product_id:  # bỏ qua dòng trống
            items.append({
                'product_id': product_id,
                'quantity': post_data.get(f'quantity_{i}', 0),
                'unit_price': post_data.get(f'unit_price_{i}', 0),
                'note': post_data.get(f'item_note_{i}', ''),
            })
        i += 1
    return items
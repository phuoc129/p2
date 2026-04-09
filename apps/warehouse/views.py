import json
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Q
from django.core.paginator import Paginator

from apps.product.models import Product
from .services import ImportReceiptService, StockService, ExportReceiptService
from .models import ImportReceipt, ImportReceiptItem, ExportReceipt, ExportReceiptItem


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


def _parse_items_from_post(post_data):
    items = []
    i = 0
    while True:
        product_id = post_data.get(f'product_id_{i}')
        if product_id is None:
            break
        if product_id:
            items.append({
                'product_id': product_id,
                'quantity': post_data.get(f'quantity_{i}', 0),
                'unit_price': post_data.get(f'unit_price_{i}', 0),
                'note': post_data.get(f'item_note_{i}', ''),
            })
        i += 1
    return items


def _get_import_receipt_stats():
    today = timezone.now().date()
    return {
        'total_receipts': ImportReceipt.objects.count(),
        'pending_receipts': ImportReceipt.objects.filter(status='PENDING').count(),
        'total_items': ImportReceiptItem.objects.aggregate(total=Sum('quantity'))['total'] or 0,
        'today_transactions': ImportReceipt.objects.filter(created_at__date=today).count(),
    }


def _get_export_receipt_stats():
    today = timezone.now().date()
    return {
        'total_receipts': ExportReceipt.objects.count(),
        'pending_receipts': ExportReceipt.objects.filter(status='PENDING').count(),
        'total_items': ExportReceiptItem.objects.aggregate(total=Sum('quantity'))['total'] or 0,
        'today_transactions': ExportReceipt.objects.filter(created_at__date=today).count(),
    }


PAGE_SIZE = 10  # Số phiếu mỗi trang


# ═══════════════════════════════════════════════════════════════
# NHẬP KHO
# ═══════════════════════════════════════════════════════════════

class ImportReceiptListView(LoginRequiredMixin, View):
    def get(self, request):
        service = ImportReceiptService()
        user = request.user

        if user.role in ('KE_TOAN', 'ADMIN'):
            receipts = service.get_all()
        else:
            receipts = service.get_by_user(user)

        status_filter = request.GET.get('status', '')
        search_query = request.GET.get('search', '')
        page_number = request.GET.get('page', 1)

        if status_filter:
            receipts = receipts.filter(status=status_filter)

        if search_query:
            receipts = receipts.filter(
                Q(receipt_code__icontains=search_query) |
                Q(note__icontains=search_query)
            )

        paginator = Paginator(receipts, PAGE_SIZE)
        page_obj = paginator.get_page(page_number)

        products_data = _products_json()
        stats = _get_import_receipt_stats()

        user_role = 'ADMIN' if user.is_superuser else user.role

        return render(request, 'warehouse/import_receipt_list.html', {
            'receipts': page_obj,
            'page_obj': page_obj,
            'paginator': paginator,
            'products_json': json.dumps(products_data, ensure_ascii=False),
            'status_filter': status_filter,
            'search_query': search_query,
            'user_role': user_role,
            'stats': stats,
        })

    def post(self, request):
        if request.user.role not in ('KHO', 'ADMIN') and not request.user.is_superuser:
            messages.error(request, 'Bạn không có quyền tạo phiếu nhập kho.')
            return redirect('warehouse:import_list')

        service = ImportReceiptService()
        note = request.POST.get('note', '')
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
            'user_role': 'ADMIN' if request.user.is_superuser else request.user.role,
        })


class ImportReceiptApproveView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if request.user.role not in ('KE_TOAN', 'ADMIN') and not request.user.is_superuser:
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
    def post(self, request, pk):
        if request.user.role not in ('KE_TOAN', 'ADMIN') and not request.user.is_superuser:
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
    def post(self, request, pk):
        if request.user.role not in ('KHO', 'ADMIN') and not request.user.is_superuser:
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
# TỒN KHO
# ═══════════════════════════════════════════════════════════════

class StockListView(LoginRequiredMixin, View):
    def get(self, request):
        service = StockService()
        search_query = request.GET.get('search', '')
        page_number = request.GET.get('page', 1)

        stocks_qs = service.get_all_stocks()

        if search_query:
            stocks_qs = stocks_qs.filter(
                Q(product__name__icontains=search_query) |
                Q(product__category__name__icontains=search_query)
            )

        paginator = Paginator(stocks_qs, 5)  # 5 cards mỗi trang
        page_obj = paginator.get_page(page_number)

        return render(request, 'warehouse/stock_list.html', {
            'stocks': page_obj,
            'page_obj': page_obj,
            'paginator': paginator,
            'search_query': search_query,
            'user_role': 'ADMIN' if request.user.is_superuser else request.user.role,
        })


# ═══════════════════════════════════════════════════════════════
# XUẤT KHO — Tất cả role đều có thể duyệt
# ═══════════════════════════════════════════════════════════════

EXPORT_APPROVE_ROLES = ('KHO', 'KE_TOAN', 'ADMIN', 'SALE')


class ExportReceiptListView(LoginRequiredMixin, View):
    def get(self, request):
        service = ExportReceiptService()
        user = request.user

        receipts = service.get_all()

        status_filter = request.GET.get('status', '')
        search_query = request.GET.get('search', '')
        page_number = request.GET.get('page', 1)

        if status_filter:
            receipts = receipts.filter(status=status_filter)

        if search_query:
            receipts = receipts.filter(
                Q(receipt_code__icontains=search_query) |
                Q(note__icontains=search_query)
            )

        paginator = Paginator(receipts, PAGE_SIZE)
        page_obj = paginator.get_page(page_number)

        products_data = _products_json()
        stats = _get_export_receipt_stats()

        return render(request, 'warehouse/export_receipt_list.html', {
            'receipts': page_obj,
            'page_obj': page_obj,
            'paginator': paginator,
            'products_json': json.dumps(products_data, ensure_ascii=False),
            'status_filter': status_filter,
            'search_query': search_query,
            'user_role': 'ADMIN' if user.is_superuser else user.role,
            'stats': stats,
        })

    def post(self, request):
        if request.user.role not in ('KHO', 'ADMIN') and not request.user.is_superuser:
            messages.error(request, 'Bạn không có quyền tạo phiếu xuất kho.')
            return redirect('warehouse:export_list')

        service = ExportReceiptService()
        note = request.POST.get('note', '')
        items_data = _parse_items_from_post(request.POST)

        receipt, error = service.create_receipt(note, items_data, request.user)
        if receipt:
            messages.success(request, f'Đã tạo phiếu xuất {receipt.receipt_code} thành công. Chờ duyệt.')
        else:
            messages.error(request, error)

        return redirect('warehouse:export_list')


class ExportReceiptDetailView(LoginRequiredMixin, View):
    def get(self, request, pk):
        service = ExportReceiptService()
        receipt = service.get_by_id(pk)
        if not receipt:
            messages.error(request, 'Không tìm thấy phiếu xuất kho.')
            return redirect('warehouse:export_list')

        products_data = _products_json()
        return render(request, 'warehouse/export_receipt_detail.html', {
            'receipt': receipt,
            'products_json': json.dumps(products_data, ensure_ascii=False),
            'user_role': 'ADMIN' if request.user.is_superuser else request.user.role,
        })


class ExportReceiptApproveView(LoginRequiredMixin, View):
    def post(self, request, pk):
        service = ExportReceiptService()
        success, msg = service.approve_receipt(pk, request.user)
        if success:
            messages.success(request, msg)
        else:
            messages.error(request, msg)
        return redirect('warehouse:export_list')


class ExportReceiptRejectView(LoginRequiredMixin, View):
    def post(self, request, pk):
        service = ExportReceiptService()
        rejection_note = request.POST.get('rejection_note', '')
        success, msg = service.reject_receipt(pk, request.user, rejection_note)
        if success:
            messages.warning(request, msg)
        else:
            messages.error(request, msg)
        return redirect('warehouse:export_list')


class ExportReceiptResubmitView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if request.user.role not in ('KHO', 'ADMIN') and not request.user.is_superuser:
            messages.error(request, 'Bạn không có quyền gửi lại phiếu.')
            return redirect('warehouse:export_list')

        service = ExportReceiptService()
        note = request.POST.get('note', '')
        items_data = _parse_items_from_post(request.POST)

        receipt, error = service.resubmit_receipt(pk, note, items_data, request.user)
        if receipt:
            messages.success(request, f'Đã gửi lại phiếu {receipt.receipt_code}. Chờ duyệt.')
        else:
            messages.error(request, error)
        return redirect('warehouse:export_list')
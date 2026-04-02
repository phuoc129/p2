import json
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

from apps.product.models import Product
from .services import SalesOrderService, CustomerDebtService


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
    from apps.warehouse.repositories import ProductStockRepository
    stocks = ProductStockRepository.get_all()
    return {str(s.product_id): float(s.quantity) for s in stocks}


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


class SalesOrderListView(LoginRequiredMixin, View):
    """Danh sách đơn hàng — Sale tạo, mọi người xem"""

    def get(self, request):
        service = SalesOrderService()
        user = request.user

        if user.role in ('KE_TOAN', 'ADMIN'):
            orders = service.get_all()
        elif user.role == 'SALE':
            orders = service.get_by_user(user)
        else:
            orders = service.get_all()

        status_filter = request.GET.get('status', '')
        if status_filter:
            orders = orders.filter(status=status_filter)

        products_data = _products_json()
        stocks_data = _stocks_json()

        return render(request, 'order/sales_order_list.html', {
            'orders': orders,
            'products_json': json.dumps(products_data, ensure_ascii=False),
            'stocks_json': json.dumps(stocks_data),
            'user_role': user.role,
            'status_filter': status_filter,
        })

    def post(self, request):
        """Sale tạo đơn hàng"""
        if request.user.role not in ('SALE', 'ADMIN'):
            messages.error(request, 'Bạn không có quyền tạo đơn hàng.')
            return redirect('order:sales_list')

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

        return redirect('order:sales_list')


class SalesOrderDetailView(LoginRequiredMixin, View):
    def get(self, request, pk):
        service = SalesOrderService()
        order = service.get_by_id(pk)
        if not order:
            messages.error(request, 'Không tìm thấy đơn hàng.')
            return redirect('order:sales_list')

        return render(request, 'order/sales_order_detail.html', {
            'order': order,
            'user_role': request.user.role,
        })


class CustomerDebtListView(LoginRequiredMixin, View):
    def get(self, request):
        service = CustomerDebtService()
        status_filter = request.GET.get('status', '')
        search = request.GET.get('search', '')

        debts = service.get_all(status=status_filter or None, search=search or None)

        return render(request, 'order/customer_debt_list.html', {
            'debts': debts,
            'status_filter': status_filter,
            'user_role': request.user.role,
        })

    def post(self, request):
        """Đánh dấu công nợ đã thanh toán"""
        if request.user.role not in ('KE_TOAN', 'ADMIN'):
            messages.error(request, 'Bạn không có quyền cập nhật công nợ.')
            return redirect('order:debt_list')

        debt_id = request.POST.get('debt_id')
        service = CustomerDebtService()
        success, msg = service.mark_paid(debt_id)

        if success:
            messages.success(request, msg)
        else:
            messages.error(request, msg)

        return redirect('order:debt_list')
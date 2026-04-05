from .repositories import SalesOrderRepository, CustomerDebtRepository
from decimal import Decimal

class SalesOrderService:

    # Luồng trạng thái HỢP LỆ — chỉ đi 1 chiều, không quay lại
    VALID_TRANSITIONS = {
        'CONFIRMED': ['WAITING', 'CANCELLED'],
        'WAITING':   ['DONE', 'CANCELLED'],
        'DONE':      [],
        'CANCELLED': [],
    }

    def __init__(self):
        self.repo = SalesOrderRepository()

    def get_all(self, status=None, search=None):
        return SalesOrderRepository.get_all(status=status, search=search)

    def get_by_id(self, order_id):
        return SalesOrderRepository.get_by_id(order_id)

    def get_by_user(self, user):
        return SalesOrderRepository.get_by_user(user)

    def create_order(self, customer_name, customer_phone, note, items_data, user):
        """
        Sale tạo đơn hàng.
        Hệ thống tự kiểm tra kho và trừ ngay nếu đủ.
        Trả về (order, None) hoặc (None, errors_list)
        """
        if not customer_name or not customer_name.strip():
            return None, [{'message': 'Vui lòng nhập tên khách hàng.'}]

        if not items_data:
            return None, [{'message': 'Đơn hàng phải có ít nhất 1 sản phẩm.'}]

        cleaned_items = []
        for idx, item in enumerate(items_data):
            if not item.get('product_id'):
                return None, [{'message': f'Dòng {idx+1}: chưa chọn sản phẩm.'}]
            try:
                qty = Decimal(str(item.get('quantity', 0)))
            except (ValueError, TypeError):
                return None, [{'message': f'Dòng {idx+1}: số lượng không hợp lệ.'}]
            if qty <= 0:
                return None, [{'message': f'Dòng {idx+1}: số lượng phải lớn hơn 0.'}]
            item['quantity'] = qty
            cleaned_items.append(item)

        order_data = {
            'customer_name': customer_name.strip(),
            'customer_phone': customer_phone.strip() if customer_phone else '',
            'note': note or '',
        }

        order, errors = SalesOrderRepository.create_with_items(order_data, cleaned_items, user)
        return order, errors

    def update_status(self, order_id, new_status, updated_by=None):
        order = SalesOrderRepository.get_by_id(order_id)
        if not order:
            return False, 'Không tìm thấy đơn hàng.'

        # Kiểm tra luồng hợp lệ
        allowed = self.VALID_TRANSITIONS.get(order.status, [])
        if new_status not in allowed:
            status_labels = {
                'CONFIRMED': 'Đã xác nhận',
                'WAITING': 'Chờ lấy hàng',
                'DONE': 'Hoàn thành',
                'CANCELLED': 'Đã hủy',
            }
            current_label = status_labels.get(order.status, order.status)
            new_label = status_labels.get(new_status, new_status)
            return False, f'Không thể chuyển từ "{current_label}" sang "{new_label}".'

        SalesOrderRepository.update_status(order, new_status)

        # Khi chuyển sang "Chờ lấy hàng" → tự động tạo phiếu xuất kho
        if new_status == 'WAITING' and updated_by is not None:
            self._create_export_receipt_for_order(order, updated_by)

        return True, 'Cập nhật trạng thái thành công.'

    def _create_export_receipt_for_order(self, order, user):
        """Tạo phiếu xuất kho tự động từ đơn hàng khi chuyển sang Chờ lấy hàng"""
        from apps.warehouse.repositories import ExportReceiptRepository
        items_data = [
            {
                'product_id': str(item.product_id),
                'quantity': float(item.quantity),
                'unit_price': float(item.unit_price),
                'note': f'Đơn hàng {order.order_code}',
            }
            for item in order.items.select_related('product').all()
        ]
        receipt_data = {
            'note': f'Xuất hàng cho đơn {order.order_code} — KH: {order.customer_name}',
        }
        try:
            ExportReceiptRepository.create_with_items(receipt_data, items_data, user)
        except Exception as e:
            # Không block luồng chính nếu tạo phiếu thất bại
            import logging
            logging.getLogger(__name__).error(f'Lỗi tạo phiếu xuất cho đơn {order.order_code}: {e}')


class CustomerDebtService:

    def __init__(self):
        self.repo = CustomerDebtRepository()

    def get_all(self, status=None, search=None):
        return CustomerDebtRepository.get_all(status=status, search_customer=search)

    def get_by_id(self, debt_id):
        return CustomerDebtRepository.get_by_id(debt_id)

    def get_pending(self):
        return CustomerDebtRepository.get_pending_debts()

    def create_debt(self, sales_order, customer_name, remaining_amount, due_date=None, note=None):
        data = {
            'sales_order': sales_order,
            'customer_name': customer_name,
            'remaining_amount': remaining_amount,
            'due_date': due_date,
            'note': note or '',
        }
        return CustomerDebtRepository.create(data)

    def mark_paid(self, debt_id):
        debt = CustomerDebtRepository.get_by_id(debt_id)
        if not debt:
            return False, 'Không tìm thấy công nợ.'
        CustomerDebtRepository.update_status(debt, 'PAID')
        return True, 'Đã đánh dấu thanh toán.'
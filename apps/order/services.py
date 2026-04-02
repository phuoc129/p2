from .repositories import SalesOrderRepository, CustomerDebtRepository
from decimal import Decimal

class SalesOrderService:

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

    def update_status(self, order_id, status):
        order = SalesOrderRepository.get_by_id(order_id)
        if not order:
            return False, 'Không tìm thấy đơn hàng.'
        SalesOrderRepository.update_status(order, status)
        return True, 'Cập nhật trạng thái thành công.'


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
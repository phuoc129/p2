from .repositories import ImportReceiptRepository, ProductStockRepository, SalesOrderRepository


class ImportReceiptService:
    def __init__(self):
        self.repo = ImportReceiptRepository()

    def get_all(self):
        return ImportReceiptRepository.get_all()

    def get_by_id(self, receipt_id):
        return ImportReceiptRepository.get_by_id(receipt_id)

    def get_pending(self):
        return ImportReceiptRepository.get_by_status('PENDING')

    def get_by_user(self, user):
        return ImportReceiptRepository.get_by_user(user)

    def create_receipt(self, note, items_data, user):
        """
        Thủ kho tạo phiếu nhập.
        items_data: list of dict {product_id, quantity, unit_price, note}
        """
        if not items_data:
            return None, 'Phiếu phải có ít nhất 1 sản phẩm.'

        for idx, item in enumerate(items_data):
            if not item.get('product_id'):
                return None, f'Dòng {idx+1}: chưa chọn sản phẩm.'
            try:
                qty = float(item.get('quantity', 0))
            except (ValueError, TypeError):
                return None, f'Dòng {idx+1}: số lượng không hợp lệ.'
            if qty <= 0:
                return None, f'Dòng {idx+1}: số lượng phải lớn hơn 0.'
            item['quantity'] = qty

        receipt_data = {'note': note}
        receipt = ImportReceiptRepository.create_with_items(receipt_data, items_data, user)
        return receipt, None

    def approve_receipt(self, receipt_id, reviewed_by):
        """Kế toán duyệt phiếu"""
        receipt = ImportReceiptRepository.get_by_id(receipt_id)
        if not receipt:
            return False, 'Không tìm thấy phiếu.'
        if receipt.status != 'PENDING':
            return False, 'Chỉ có thể duyệt phiếu đang chờ duyệt.'
        ImportReceiptRepository.approve(receipt, reviewed_by)
        return True, f'Phiếu {receipt.receipt_code} đã được duyệt. Tồn kho đã được cập nhật.'

    def reject_receipt(self, receipt_id, reviewed_by, rejection_note):
        """Kế toán từ chối phiếu"""
        receipt = ImportReceiptRepository.get_by_id(receipt_id)
        if not receipt:
            return False, 'Không tìm thấy phiếu.'
        if receipt.status != 'PENDING':
            return False, 'Chỉ có thể từ chối phiếu đang chờ duyệt.'
        if not rejection_note or not rejection_note.strip():
            return False, 'Vui lòng ghi lý do từ chối.'
        ImportReceiptRepository.reject(receipt, reviewed_by, rejection_note.strip())
        return True, f'Phiếu {receipt.receipt_code} đã bị từ chối.'

    def resubmit_receipt(self, receipt_id, note, items_data, user):
        """Thủ kho sửa lại phiếu bị từ chối và gửi lại"""
        receipt = ImportReceiptRepository.get_by_id(receipt_id)
        if not receipt:
            return None, 'Không tìm thấy phiếu.'
        if receipt.status != 'REJECTED':
            return None, 'Chỉ có thể gửi lại phiếu bị từ chối.'
        if receipt.created_by != user:
            return None, 'Bạn không có quyền sửa phiếu này.'

        if not items_data:
            return None, 'Phiếu phải có ít nhất 1 sản phẩm.'

        for idx, item in enumerate(items_data):
            try:
                qty = float(item.get('quantity', 0))
            except (ValueError, TypeError):
                return None, f'Dòng {idx+1}: số lượng không hợp lệ.'
            if qty <= 0:
                return None, f'Dòng {idx+1}: số lượng phải lớn hơn 0.'
            item['quantity'] = qty

        receipt = ImportReceiptRepository.resubmit(receipt, items_data, note)
        return receipt, None


class SalesOrderService:
    def __init__(self):
        self.repo = SalesOrderRepository()

    def get_all(self):
        return SalesOrderRepository.get_all()

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
                qty = float(item.get('quantity', 0))
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

        order, errors = SalesOrderRepository.create_with_stock_check(order_data, cleaned_items, user)
        return order, errors

    def get_stock_info(self, product_id):
        return ProductStockRepository.get_stock(product_id)

    def get_all_stocks(self):
        return ProductStockRepository.get_all()
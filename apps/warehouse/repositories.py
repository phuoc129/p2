from django.db import transaction
from django.utils import timezone
from .models import ImportReceipt, ImportReceiptItem, ProductStock, SalesOrder, SalesOrderItem


# ============================================================
# Import Receipt Repository
# ============================================================
class ImportReceiptRepository:

    @staticmethod
    def get_all():
        return ImportReceipt.objects.select_related(
            'created_by', 'reviewed_by'
        ).prefetch_related('items__product').all()

    @staticmethod
    def get_by_id(receipt_id):
        try:
            return ImportReceipt.objects.select_related(
                'created_by', 'reviewed_by'
            ).prefetch_related('items__product').get(pk=receipt_id)
        except ImportReceipt.DoesNotExist:
            return None

    @staticmethod
    def get_by_status(status):
        return ImportReceipt.objects.select_related(
            'created_by', 'reviewed_by'
        ).prefetch_related('items__product').filter(status=status)

    @staticmethod
    def get_by_user(user):
        return ImportReceipt.objects.select_related(
            'created_by', 'reviewed_by'
        ).prefetch_related('items__product').filter(created_by=user)

    @staticmethod
    def generate_receipt_code():
        """Tạo mã phiếu tự động: PN-YYYYMMDD-XXX"""
        from django.utils import timezone
        import random
        date_str = timezone.now().strftime('%Y%m%d')
        count = ImportReceipt.objects.filter(
            receipt_code__startswith=f'PN-{date_str}'
        ).count() + 1
        return f'PN-{date_str}-{count:03d}'

    @staticmethod
    @transaction.atomic
    def create_with_items(receipt_data, items_data, user):
        """Tạo phiếu nhập + các dòng sản phẩm trong 1 transaction"""
        receipt_data['receipt_code'] = ImportReceiptRepository.generate_receipt_code()
        receipt_data['created_by'] = user
        receipt_data['status'] = 'PENDING'

        receipt = ImportReceipt.objects.create(**receipt_data)

        item_instances = [
            ImportReceiptItem(
                receipt=receipt,
                product_id=item['product_id'],
                quantity=item['quantity'],
                unit_price=item.get('unit_price', 0),
                note=item.get('note', ''),
            )
            for item in items_data
        ]
        ImportReceiptItem.objects.bulk_create(item_instances)

        return receipt

    @staticmethod
    @transaction.atomic
    def approve(receipt, reviewed_by):
        """Kế toán duyệt → cộng vào tồn kho"""
        receipt.status = 'APPROVED'
        receipt.reviewed_by = reviewed_by
        receipt.reviewed_at = timezone.now()
        receipt.rejection_note = ''
        receipt.save()

        # Cộng số lượng vào ProductStock
        for item in receipt.items.select_related('product').all():
            stock, _ = ProductStock.objects.get_or_create(
                product=item.product,
                defaults={'quantity': 0}
            )
            stock.quantity += item.quantity
            stock.save()

        return receipt

    @staticmethod
    def reject(receipt, reviewed_by, rejection_note):
        """Kế toán từ chối + ghi ghi chú"""
        receipt.status = 'REJECTED'
        receipt.reviewed_by = reviewed_by
        receipt.reviewed_at = timezone.now()
        receipt.rejection_note = rejection_note
        receipt.save()
        return receipt

    @staticmethod
    @transaction.atomic
    def resubmit(receipt, items_data, note=''):
        """Thủ kho sửa lại phiếu bị từ chối và gửi lại"""
        receipt.status = 'PENDING'
        receipt.rejection_note = ''
        receipt.note = note
        receipt.reviewed_by = None
        receipt.reviewed_at = None
        receipt.save()

        # Xóa items cũ, tạo lại
        receipt.items.all().delete()
        item_instances = [
            ImportReceiptItem(
                receipt=receipt,
                product_id=item['product_id'],
                quantity=item['quantity'],
                unit_price=item.get('unit_price', 0),
                note=item.get('note', ''),
            )
            for item in items_data
        ]
        ImportReceiptItem.objects.bulk_create(item_instances)
        return receipt


# ============================================================
# Product Stock Repository
# ============================================================
class ProductStockRepository:

    @staticmethod
    def get_stock(product_id):
        try:
            return ProductStock.objects.select_related('product').get(product_id=product_id)
        except ProductStock.DoesNotExist:
            return None

    @staticmethod
    def get_all():
        return ProductStock.objects.select_related('product__category').all()

    @staticmethod
    def get_quantity(product_id):
        stock = ProductStockRepository.get_stock(product_id)
        return stock.quantity if stock else 0


# ============================================================
# Sales Order Repository
# ============================================================
class SalesOrderRepository:

    @staticmethod
    def get_all():
        return SalesOrder.objects.select_related('created_by').prefetch_related('items__product').all()

    @staticmethod
    def get_by_id(order_id):
        try:
            return SalesOrder.objects.select_related('created_by').prefetch_related('items__product').get(pk=order_id)
        except SalesOrder.DoesNotExist:
            return None

    @staticmethod
    def get_by_user(user):
        return SalesOrder.objects.select_related('created_by').prefetch_related('items__product').filter(created_by=user)

    @staticmethod
    def generate_order_code():
        from django.utils import timezone
        date_str = timezone.now().strftime('%Y%m%d')
        count = SalesOrder.objects.filter(
            order_code__startswith=f'DH-{date_str}'
        ).count() + 1
        return f'DH-{date_str}-{count:03d}'

    @staticmethod
    @transaction.atomic
    def create_with_stock_check(order_data, items_data, user):
        """
        Tạo đơn hàng + tự động trừ kho.
        Trả về (order, None) nếu thành công.
        Trả về (None, error_list) nếu không đủ tồn kho.
        """
        # Kiểm tra tồn kho trước
        errors = []
        for item in items_data:
            stock = ProductStockRepository.get_stock(item['product_id'])
            available = stock.quantity if stock else 0
            if available < item['quantity']:
                from apps.product.models import Product
                try:
                    product = Product.objects.get(pk=item['product_id'])
                    name = product.name
                    unit = product.base_unit
                except Product.DoesNotExist:
                    name = 'Sản phẩm không tồn tại'
                    unit = ''
                errors.append({
                    'product_id': item['product_id'],
                    'product_name': name,
                    'requested': item['quantity'],
                    'available': available,
                    'unit': unit,
                    'message': f'"{name}" chỉ còn {available} {unit}, bạn yêu cầu {item["quantity"]} {unit}.'
                })

        if errors:
            return None, errors

        # Tạo đơn hàng
        order_data['order_code'] = SalesOrderRepository.generate_order_code()
        order_data['created_by'] = user
        order_data['status'] = 'CONFIRMED'

        order = SalesOrder.objects.create(**order_data)

        item_instances = []
        for item in items_data:
            item_instances.append(SalesOrderItem(
                order=order,
                product_id=item['product_id'],
                quantity=item['quantity'],
                unit_price=item.get('unit_price', 0),
            ))

            # Trừ kho ngay
            stock, _ = ProductStock.objects.get_or_create(
                product_id=item['product_id'],
                defaults={'quantity': 0}
            )
            stock.quantity -= item['quantity']
            stock.save()

        SalesOrderItem.objects.bulk_create(item_instances)
        return order, None
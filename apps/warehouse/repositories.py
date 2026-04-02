from django.db import transaction
from django.utils import timezone
from .models import ImportReceipt, ImportReceiptItem, ProductStock


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
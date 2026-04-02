import uuid
from django.db import models
from django.conf import settings
from apps.product.models import Product


# ============================================================
# PHIẾU NHẬP KHO (do Thủ kho tạo, Kế toán duyệt)
# ============================================================
class ImportReceipt(models.Model):
    """Phiếu nhập kho — nhiều sản phẩm trong 1 phiếu"""

    STATUS_CHOICES = [
        ('PENDING', 'Chờ duyệt'),      # Thủ kho vừa tạo/gửi lại
        ('APPROVED', 'Đã duyệt'),       # Kế toán duyệt → cộng vào tồn kho
        ('REJECTED', 'Từ chối'),        # Kế toán từ chối (kèm ghi chú)
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    receipt_code = models.CharField(max_length=30, unique=True)

    # Người tạo (Thủ kho - KHO role)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='import_receipts_created',
    )

    # Người duyệt (Kế toán - KE_TOAN role)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='import_receipts_reviewed',
    )

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    note = models.TextField(blank=True, null=True, help_text='Thủ kho ghi chú khi tạo')
    rejection_note = models.TextField(blank=True, null=True, help_text='Kế toán ghi lý do từ chối')

    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'import_receipts'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.receipt_code} — {self.get_status_display()}'

    @property
    def total_items(self):
        return self.items.count()

    @property
    def can_be_edited(self):
        """Thủ kho chỉ sửa được khi đang PENDING hoặc REJECTED"""
        return self.status in ('PENDING', 'REJECTED')


class ImportReceiptItem(models.Model):
    """Chi tiết từng dòng sản phẩm trong phiếu nhập"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    receipt = models.ForeignKey(ImportReceipt, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='import_items')
    quantity = models.DecimalField(max_digits=15, decimal_places=2)
    unit_price = models.DecimalField(max_digits=19, decimal_places=4, default=0)
    note = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'import_receipt_items'

    @property
    def subtotal(self):
        return self.quantity * self.unit_price


# ============================================================
# TỒN KHO (inventory đơn giản — số lượng trên sản phẩm)
# ============================================================
class ProductStock(models.Model):
    """Tồn kho hiện tại của từng sản phẩm"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='stock')
    quantity = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'product_stocks'

    def __str__(self):
        return f'{self.product.name}: {self.quantity} {self.product.base_unit}'


# ============================================================
# PHIẾU XUẤT KHO / ĐƠN HÀNG (do Sale tạo)
# ============================================================
class SalesOrder(models.Model):
    """Đơn hàng bán — Sale tạo, hệ thống tự trừ kho ngay"""

    STATUS_CHOICES = [
        ('CONFIRMED', 'Đã xác nhận'),
        ('WAITING', 'Chờ lấy hàng'),
        ('DONE', 'Hoàn thành'),
        ('CANCELLED', 'Đã hủy'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_code = models.CharField(max_length=30, unique=True)
    customer_name = models.CharField(max_length=200)
    customer_phone = models.CharField(max_length=20, blank=True, null=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='sales_orders_created',
    )

    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='CONFIRMED')
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sales_orders'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.order_code} — {self.customer_name}'

    @property
    def total_amount(self):
        return sum(item.subtotal for item in self.items.all())


class SalesOrderItem(models.Model):
    """Chi tiết từng dòng sản phẩm trong đơn hàng"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='sales_items')
    quantity = models.DecimalField(max_digits=15, decimal_places=2)
    unit_price = models.DecimalField(max_digits=19, decimal_places=4, default=0)

    class Meta:
        db_table = 'sales_order_items'

    @property
    def subtotal(self):
        return self.quantity * self.unit_price
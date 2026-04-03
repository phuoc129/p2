import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from apps.product.models import Product


# ============================================================
# PHIẾU NHẬP KHO (do Thủ kho tạo, Kế toán duyệt)
# ============================================================
class ImportReceipt(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Chờ duyệt'),
        ('APPROVED', 'Đã duyệt'),
        ('REJECTED', 'Từ chối'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    receipt_code = models.CharField(max_length=30, unique=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='import_receipts_created',
    )

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
        return self.status in ('PENDING', 'REJECTED')


class ImportReceiptItem(models.Model):
    """Chi tiết từng dòng sản phẩm trong phiếu nhập"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    receipt = models.ForeignKey(ImportReceipt, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='import_items')
    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text="Số lượng, phải > 0"
    )
    unit_price = models.DecimalField(
        max_digits=19,
        decimal_places=4,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Giá/đơn vị, không được âm"
    )
    note = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'import_receipt_items'

    @property
    def subtotal(self):
        return self.quantity * self.unit_price


# ============================================================
# TỒN KHO
# ============================================================
class ProductStock(models.Model):
    """Tồn kho hiện tại của từng sản phẩm"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='stock')
    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Số lượng tồn, không được âm"
    )
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'product_stocks'

    def __str__(self):
        return f'{self.product.name}: {self.quantity} {self.product.base_unit}'


# ============================================================
# PHIẾU XUẤT KHO (do Thủ kho tạo, Kế toán duyệt)
# ============================================================
class ExportReceipt(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Chờ duyệt'),
        ('APPROVED', 'Đã duyệt'),
        ('REJECTED', 'Từ chối'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    receipt_code = models.CharField(max_length=30, unique=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='export_receipts_created',
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='export_receipts_reviewed',
    )

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    note = models.TextField(blank=True, null=True, help_text='Lý do xuất kho')
    rejection_note = models.TextField(blank=True, null=True, help_text='Kế toán ghi lý do từ chối')

    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'export_receipts'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.receipt_code} — {self.get_status_display()}'

    @property
    def total_items(self):
        return self.items.count()

    @property
    def can_be_edited(self):
        return self.status in ('PENDING', 'REJECTED')


class ExportReceiptItem(models.Model):
    """Chi tiết từng dòng sản phẩm trong phiếu xuất"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    receipt = models.ForeignKey(ExportReceipt, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='export_items')
    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text="Số lượng, phải > 0"
    )
    unit_price = models.DecimalField(
        max_digits=19,
        decimal_places=4,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Giá/đơn vị, không được âm"
    )
    note = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'export_receipt_items'

    @property
    def subtotal(self):
        return self.quantity * self.unit_price
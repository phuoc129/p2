import uuid
from django.db import models
from django.conf import settings
from apps.product.models import Product


# ============================================================
# ĐƠN HÀNG BÁN (do Sale tạo)
# ============================================================
class SalesOrder(models.Model):
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
        related_name='order_sales_orders_created',
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
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='order_sales_items')
    quantity = models.DecimalField(max_digits=15, decimal_places=2)
    unit_price = models.DecimalField(max_digits=19, decimal_places=4, default=0)

    class Meta:
        db_table = 'sales_order_items'

    @property
    def subtotal(self):
        return self.quantity * self.unit_price


# ============================================================
# CÔNG NỢ KHÁCH HÀNG
# ============================================================
class CustomerDebt(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Chưa thanh toán'),
        ('PAID', 'Đã thanh toán'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sales_order = models.ForeignKey(
        SalesOrder, on_delete=models.CASCADE, related_name='debts'
    )
    customer_name = models.CharField(max_length=200)
    remaining_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    due_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'customer_debts'
        ordering = ['due_date']

    def __str__(self):
        return f'{self.customer_name} — còn {self.remaining_amount}'
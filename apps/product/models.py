import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MinLengthValidator, URLValidator


# ============================================================
# 1. DANH MỤC
# ============================================================
class Category(models.Model):
    id   = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=255,
        unique=True,
        validators=[MinLengthValidator(2)],
        help_text="Tên danh mục, tối thiểu 2 ký tự"
    )

    class Meta:
        db_table = 'categories'

    def __str__(self):
        return self.name


# ============================================================
# 2. SẢN PHẨM
# ============================================================
class Product(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name       = models.CharField(
        max_length=255,
        unique=True,
        validators=[MinLengthValidator(2)],
        help_text="Tên sản phẩm, tối thiểu 2 ký tự"
    )
    base_price = models.DecimalField(
        max_digits=19,
        decimal_places=4,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Giá cơ bản, không được âm"
    )
    image_url  = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        validators=[URLValidator()],
        help_text="URL hình ảnh (phải là URL hợp lệ)"
    )
    base_unit  = models.CharField(
        max_length=50,
        validators=[MinLengthValidator(1)],
        help_text="Đơn vị gốc (Bao, Cây, m3...)"
    )
    category   = models.ForeignKey(
        Category, on_delete=models.SET_NULL,
        null=True, related_name='products'
    )

    class Meta:
        db_table = 'products'

    def __str__(self):
        return self.name


# ============================================================
# 3. ĐƠN VỊ TÍNH
# ============================================================
class ProductUnit(models.Model):
    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product         = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='units')
    unit_name       = models.CharField(
        max_length=100,
        validators=[MinLengthValidator(1)],
        help_text="Tên đơn vị (Bao, Cây, m3...)"
    )
    conversion_rate = models.DecimalField(
        max_digits=19,
        decimal_places=4,
        default=1.0,
        validators=[MinValueValidator(0.0001)],
        help_text="Tỉ lệ chuyển đổi, phải > 0"
    )

    class Meta:
        db_table = 'product_units'

    def __str__(self):
        return f"{self.product.name} - {self.unit_name}"


# # ============================================================
# # 4. KHO
# # ============================================================
# class Warehouse(models.Model):
#     id          = models.BigAutoField(primary_key=True)
#     name        = models.CharField(max_length=100)
#     location    = models.CharField(max_length=255, null=True, blank=True)
#     description = models.TextField(null=True, blank=True)

#     class Meta:
#         db_table = 'warehouses'

#     def __str__(self):
#         return self.name


# # ============================================================
# # 5. TỒN KHO
# # ============================================================
# class Inventory(models.Model):
#     id                = models.BigAutoField(primary_key=True)
#     product           = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventories')
#     warehouse         = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='inventories')
#     quantity_on_hand  = models.DecimalField(max_digits=15, decimal_places=2, default=0)
#     quantity_reserved = models.DecimalField(max_digits=15, decimal_places=2, default=0)
#     min_stock_level   = models.DecimalField(max_digits=15, decimal_places=2, default=0)
#     last_updated      = models.DateTimeField(auto_now=True)

#     class Meta:
#         db_table = 'inventories'
#         unique_together = ('product', 'warehouse')

#     def __str__(self):
#         return f"{self.product.name} @ {self.warehouse.name}"


# # ============================================================
# # 6. ĐƠN HÀNG BÁN
# # ============================================================
# class SalesOrder(models.Model):
#     STATUS_CHOICES = [
#         ('Pending',    'Chờ xử lý'),
#         ('Processing', 'Đang xử lý'),
#         ('Completed',  'Hoàn thành'),
#         ('Cancelled',  'Đã huỷ'),
#     ]

#     id            = models.BigAutoField(primary_key=True)
#     order_code    = models.CharField(max_length=20, unique=True)
#     customer_name = models.CharField(max_length=100)
#     created_by    = models.ForeignKey(
#         settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
#         related_name='sales_orders'
#     )
#     order_date    = models.DateTimeField(auto_now_add=True)
#     total_amount  = models.DecimalField(max_digits=15, decimal_places=2, default=0)
#     status        = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

#     class Meta:
#         db_table = 'sales_orders'

#     def __str__(self):
#         return f"{self.order_code} - {self.customer_name}"


# # ============================================================
# # 7. CÔNG NỢ KHÁCH HÀNG
# # ============================================================
# class CustomerDebt(models.Model):
#     STATUS_CHOICES = [
#         ('Pending', 'Chưa thanh toán'),
#         ('Paid',    'Đã thanh toán'),
#     ]

#     id               = models.BigAutoField(primary_key=True)
#     sales_order      = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='debts')
#     customer_name    = models.CharField(max_length=100)
#     remaining_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
#     due_date         = models.DateTimeField(null=True, blank=True)
#     status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

#     class Meta:
#         db_table = 'customer_debts'

#     def __str__(self):
#         return f"{self.customer_name} - còn {self.remaining_amount}"


# # ============================================================
# # 8. GIAO DỊCH KHO
# # ============================================================
# class WarehouseTransaction(models.Model):
#     TYPE_CHOICES = [
#         ('IMPORT', 'Nhập kho'),
#         ('EXPORT', 'Xuất kho'),
#     ]

#     id               = models.BigAutoField(primary_key=True)
#     code             = models.CharField(max_length=20, unique=True)
#     product          = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='transactions')
#     warehouse        = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='transactions')
#     quantity         = models.DecimalField(max_digits=15, decimal_places=2)
#     transaction_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
#     transaction_date = models.DateTimeField(auto_now_add=True)
#     created_by       = models.ForeignKey(
#         settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
#         related_name='warehouse_transactions'
#     )

#     class Meta:
#         db_table = 'warehouse_transactions'

#     def __str__(self):
#         return f"{self.code} - {self.transaction_type}"


# # ============================================================
# # 9. NHẬT KÝ HỆ THỐNG
# # ============================================================
# class SystemLog(models.Model):
#     id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     user          = models.ForeignKey(
#         settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
#         related_name='system_logs'
#     )
#     action_type   = models.CharField(max_length=50)
#     target_module = models.CharField(max_length=50)
#     old_value     = models.JSONField(null=True, blank=True)
#     new_value     = models.JSONField(null=True, blank=True)
#     created_at    = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         db_table = 'system_logs'

#     def __str__(self):
#         return f"{self.action_type} - {self.target_module} - {self.created_at}"


# # ============================================================
# # 10. NHẬT KÝ XUẤT BÁO CÁO
# # ============================================================
# class ExportLog(models.Model):
#     FORMAT_CHOICES = [
#         ('EXCEL', 'Excel'),
#         ('PDF',   'PDF'),
#     ]

#     id          = models.BigAutoField(primary_key=True)
#     user        = models.ForeignKey(
#         settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
#         related_name='export_logs'
#     )
#     report_name = models.CharField(max_length=100)
#     format      = models.CharField(max_length=10, choices=FORMAT_CHOICES)
#     export_time = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         db_table = 'export_logs'

#     def __str__(self):
#         return f"{self.report_name} - {self.format}"
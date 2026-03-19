from django.db import models
from django.conf import settings # Import settings để lấy AUTH_USER_MODEL
import uuid

# ==========================================
# 2. DANH MỤC & SẢN PHẨM
# ==========================================
class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = 'categories'

    def __str__(self):
        return self.name

class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    base_price = models.DecimalField(max_digits=19, decimal_places=4, default=0)
    image_url = models.CharField(max_length=255, null=True, blank=True)
    base_unit = models.CharField(max_length=50)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')

    class Meta:
        db_table = 'products'

class ProductUnit(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='units')
    unit_name = models.CharField(max_length=100)
    conversion_rate = models.DecimalField(max_digits=19, decimal_places=4, default=1.0)

    class Meta:
        db_table = 'product_units'

# ==========================================
# 3. KHO & TỒN KHO
# ==========================================
class Warehouse(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'warehouses'

class Inventory(models.Model):
    id = models.BigAutoField(primary_key=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    quantity_on_hand = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    quantity_reserved = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    min_stock_level = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'inventories'
        unique_together = ('product', 'warehouse')

# ==========================================
# 4. ĐƠN HÀNG & GIAO DỊCH
# ==========================================
class SalesOrder(models.Model):
    id = models.BigAutoField(primary_key=True)
    order_code = models.CharField(max_length=20, unique=True)
    customer_name = models.CharField(max_length=100)
    # SỬA LỖI TẠI ĐÂY: Dùng settings.AUTH_USER_MODEL thay vì import User trực tiếp
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    order_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    status = models.CharField(max_length=20, default='Pending')

    class Meta:
        db_table = 'sales_orders'

class CustomerDebt(models.Model):
    id = models.BigAutoField(primary_key=True)
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=100)
    remaining_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    due_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, default='Pending')

    class Meta:
        db_table = 'customer_debts'

class WarehouseTransaction(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=20, unique=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=15, decimal_places=2)
    transaction_type = models.CharField(max_length=20) # IMPORT, EXPORT...
    transaction_date = models.DateTimeField(auto_now_add=True)
    # SỬA LỖI TẠI ĐÂY: Dùng settings.AUTH_USER_MODEL
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    class Meta:
        db_table = 'warehouse_transactions'

# ==========================================
# 5. NHẬT KÝ & HỆ THỐNG
# ==========================================
class SystemLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # SỬA LỖI TẠI ĐÂY: Dùng settings.AUTH_USER_MODEL
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    action_type = models.CharField(max_length=50)
    target_module = models.CharField(max_length=50)
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'system_logs'

class ExportLog(models.Model):
    id = models.BigAutoField(primary_key=True)
    # SỬA LỖI TẠI ĐÂY: Dùng settings.AUTH_USER_MODEL
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    report_name = models.CharField(max_length=100)
    format = models.CharField(max_length=10) # EXCEL, PDF
    export_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'export_logs'
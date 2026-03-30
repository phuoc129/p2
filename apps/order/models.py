from django.db import models
from django.conf import settings 
from apps.product.models import Product  # Giữ lại import này để liên kết đơn hàng với sản phẩm

class Warehouse(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    address = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'warehouses'

class SalesOrder(models.Model):
    id = models.BigAutoField(primary_key=True)
    order_code = models.CharField(max_length=20, unique=True)
    customer_name = models.CharField(max_length=100)
    # Thêm related_name cụ thể để tránh lỗi E304/E305
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        related_name='order_sales_orders' 
    )
    order_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    status = models.CharField(max_length=20, default='Pending')

    class Meta:
        db_table = 'sales_orders'

class CustomerDebt(models.Model):
    id = models.BigAutoField(primary_key=True)
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='order_debts')
    customer_name = models.CharField(max_length=100)
    remaining_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    due_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, default='Pending')

    class Meta:
        db_table = 'customer_debts'

class WarehouseTransaction(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=20, unique=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order_transactions')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='order_transactions')
    quantity = models.DecimalField(max_digits=15, decimal_places=2)
    transaction_type = models.CharField(max_length=20)
    transaction_date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    class Meta:
        db_table = 'warehouse_transactions'
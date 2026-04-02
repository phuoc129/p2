from django.contrib import admin
from .models import SalesOrder, SalesOrderItem, CustomerDebt

# Cấu hình để hiển thị chi tiết các món hàng ngay trong trang Đơn hàng
class SalesOrderItemInline(admin.TabularInline):
    model = SalesOrderItem
    extra = 1

@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ('order_code', 'customer_name', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order_code', 'customer_name')
    inlines = [SalesOrderItemInline]

@admin.register(CustomerDebt)
class CustomerDebtAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'remaining_amount', 'status', 'due_date')
    list_filter = ('status',)
    search_fields = ('customer_name',)

# Nếu bạn muốn quản lý riêng lẻ từng dòng hàng (không bắt buộc)
# admin.site.register(SalesOrderItem)
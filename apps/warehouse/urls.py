from django.urls import path
from . import views

app_name = 'warehouse'

urlpatterns = [
    # ── Nhập kho ──────────────────────────────────
    path('import/', views.ImportReceiptListView.as_view(), name='import_list'),
    path('import/<uuid:pk>/', views.ImportReceiptDetailView.as_view(), name='import_detail'),
    path('import/<uuid:pk>/approve/', views.ImportReceiptApproveView.as_view(), name='import_approve'),
    path('import/<uuid:pk>/reject/', views.ImportReceiptRejectView.as_view(), name='import_reject'),
    path('import/<uuid:pk>/resubmit/', views.ImportReceiptResubmitView.as_view(), name='import_resubmit'),

    # ── Xuất kho / Đơn hàng Sale ──────────────────
    path('sales/', views.SalesOrderListView.as_view(), name='sales_list'),
    path('sales/<uuid:pk>/', views.SalesOrderDetailView.as_view(), name='sales_detail'),

    # ── Tồn kho ───────────────────────────────────
    path('stock/', views.StockListView.as_view(), name='stock_list'),
]
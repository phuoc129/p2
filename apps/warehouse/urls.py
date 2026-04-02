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

    # ── Xuất kho ──────────────────────────────────
    path('export/', views.ExportReceiptListView.as_view(), name='export_list'),
    path('export/<uuid:pk>/', views.ExportReceiptDetailView.as_view(), name='export_detail'),
    path('export/<uuid:pk>/approve/', views.ExportReceiptApproveView.as_view(), name='export_approve'),
    path('export/<uuid:pk>/reject/', views.ExportReceiptRejectView.as_view(), name='export_reject'),
    path('export/<uuid:pk>/resubmit/', views.ExportReceiptResubmitView.as_view(), name='export_resubmit'),

    # ── Tồn kho ───────────────────────────────────
    path('stock/', views.StockListView.as_view(), name='stock_list'),
]
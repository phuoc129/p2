from django.urls import path
from . import views

app_name = 'order'

urlpatterns = [
    # Đơn hàng bán
    path('sales/', views.SalesOrderListView.as_view(), name='sales_list'),
    path('sales/export-excel/', views.SalesOrderExportExcelView.as_view(), name='sales_export_excel'),
    path('sales/export-pdf/', views.SalesOrderExportPdfView.as_view(), name='sales_export_pdf'),
    path('sales/<uuid:pk>/', views.SalesOrderDetailView.as_view(), name='sales_detail'),
]
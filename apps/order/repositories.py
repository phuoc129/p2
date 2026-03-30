from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q
from .models import SalesOrder, CustomerDebt

class SalesOrderRepository:

    @staticmethod
    def get_all(status=None, search=None):
        queryset = SalesOrder.objects.select_related('created_by').all()
        if status:
            queryset = queryset.filter(status=status)
        if search:
            queryset = queryset.filter(
                Q(customer_name__icontains=search) |
                Q(order_code__icontains=search)
            )
        return queryset.order_by('-order_date')

    @staticmethod
    def get_by_id(order_id):
        return get_object_or_404(
            SalesOrder.objects.select_related('created_by'),
            pk=order_id
        )

    @staticmethod
    def get_by_order_code(order_code):
        return SalesOrder.objects.filter(order_code=order_code).first()

    @staticmethod
    @transaction.atomic
    def create(data):
        return SalesOrder.objects.create(**data)

    @staticmethod
    def update(order, data):
        for attr, value in data.items():
            setattr(order, attr, value)
        order.save()
        return order

    @staticmethod
    def update_status(order, status):
        order.status = status
        order.save(update_fields=['status'])
        return order

    @staticmethod
    def delete(order):
        order.delete()
        return True


class CustomerDebtRepository:

    @staticmethod
    def get_all(status=None, search_customer=None):
        queryset = CustomerDebt.objects.select_related('sales_order').all()
        if status:
            queryset = queryset.filter(status=status)
        if search_customer:
            queryset = queryset.filter(customer_name__icontains=search_customer)
        return queryset.order_by('due_date')

    @staticmethod
    def get_by_id(debt_id):
        return get_object_or_404(
            CustomerDebt.objects.select_related('sales_order'),
            pk=debt_id
        )

    @staticmethod
    def get_by_sales_order(order_id):
        return CustomerDebt.objects.filter(sales_order_id=order_id).order_by('due_date')

    @staticmethod
    def get_pending_debts():
        return CustomerDebt.objects.select_related('sales_order').filter(
            status='Pending'
        ).order_by('due_date')

    @staticmethod
    def create(data):
        return CustomerDebt.objects.create(**data)

    @staticmethod
    def update(debt, data):
        for attr, value in data.items():
            setattr(debt, attr, value)
        debt.save()
        return debt

    @staticmethod
    def update_status(debt, status):
        debt.status = status
        debt.save(update_fields=['status'])
        return debt

    @staticmethod
    def delete(debt):
        debt.delete()
        return True
from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Waiter
    path('', views.waiter_dashboard, name='waiter_dashboard'),
    path('table/<int:table_id>/', views.table_orders, name='table_orders'),
    path('table/<int:table_id>/add-item/<int:item_id>/', views.add_item, name='add_item'),
    path('scale-weight/', views.scale_weight, name='scale_weight'),
    path('order-item/<int:item_id>/change-qty/', views.change_qty, name='change_qty'),
    path('order/<int:order_id>/save/', views.save_order, name='save_order'),
    path('order/<int:order_id>/clear/', views.clear_order, name='clear_order'),
    path('order/<int:order_id>/print-check/', views.print_check, name='print_check'),

    # Admin
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/orders/', views.admin_orders, name='admin_orders'),
    path('admin-panel/menu/', views.admin_menu, name='admin_menu'),
    path('admin-panel/menu/add/', views.menu_add, name='menu_add'),
    path('admin-panel/menu/edit/<int:item_id>/', views.menu_edit, name='menu_edit'),
    path('admin-panel/menu/delete/<int:item_id>/', views.menu_delete, name='menu_delete'),
    path('admin-panel/tables/', views.admin_tables, name='admin_tables'),
    path('admin-panel/users/', views.admin_users, name='admin_users'),
    path('admin-panel/users/add/', views.user_add, name='user_add'),
    path('admin-panel/users/edit/<int:user_id>/', views.user_edit, name='user_edit'),
    path('admin-panel/users/delete/<int:user_id>/', views.user_delete, name='user_delete'),
    path('admin-panel/reports/', views.admin_reports, name='admin_reports'),
    path('admin-panel/clear-history/', views.clear_history, name='clear_history'),
    path('admin-panel/saved-receipts/', views.saved_receipts, name='saved_receipts'),
    path('admin-panel/receipt/<int:receipt_id>/', views.receipt_detail, name='receipt_detail'),
]

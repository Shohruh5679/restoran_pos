from datetime import timedelta
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from .models import Table, Category, MenuItem, Order, OrderItem, UserProfile, Settings, SavedReceipt
from .forms import LoginForm, MenuItemForm, UserForm


def get_or_create_user_profile(user):
    default_role = 'admin' if user.is_staff or user.is_superuser else 'waiter'
    profile, _ = UserProfile.objects.get_or_create(
        user=user,
        defaults={'role': default_role},
    )
    return profile


def get_tax_rate():
    '''QQS stavkasini olish (default: 12%)'''
    try:
        setting = Settings.objects.get(key='tax_rate')
        return setting.value
    except Settings.DoesNotExist:
        return '12'


def build_receipt_data(order):
    return {
        'order_id': order.id,
        'table_number': order.table.number,
        'waiter': order.waiter.get_full_name() or order.waiter.username,
        'created_at': order.created_at.isoformat(),
        'items': [
            {
                'name': item.menu_item.name,
                'quantity': item.quantity if not item.is_weight_item else None,
                'weight_kg': float(item.weight_kg) if item.is_weight_item else None,
                'price_at_time': item.price_at_time,
                'total': item.total,
            }
            for item in order.items.all()
        ],
        'subtotal': order.subtotal,
        'tax': order.tax,
        'total': order.total,
    }


def save_receipt_snapshot(order, expires_at=None):
    receipt, _ = SavedReceipt.objects.update_or_create(
        order=order,
        defaults={
            'receipt_data': build_receipt_data(order),
            'expires_at': expires_at or SavedReceipt.expiry_time(),
        },
    )
    return receipt


def ensure_recent_receipt_snapshots(now=None):
    now = now or timezone.now()
    cutoff = now - timedelta(days=SavedReceipt.RETENTION_DAYS)
    completed_orders = (
        Order.objects
        .filter(status='completed', saved_receipt__isnull=True, updated_at__gt=cutoff)
        .select_related('table', 'waiter')
        .prefetch_related('items', 'items__menu_item')
    )

    for order in completed_orders:
        save_receipt_snapshot(order, expires_at=SavedReceipt.expiry_time(order.updated_at))


def login_view(request):
    if request.user.is_authenticated:
        return redirect('waiter_dashboard')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        role = request.POST.get('role', 'waiter')

        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)

            if user is not None:
                profile = get_or_create_user_profile(user)
                if profile.role == role:
                    login(request, user)
                    if role == 'admin':
                        return redirect('admin_dashboard')
                    return redirect('waiter_dashboard')
                messages.error(request, 'Rol noto\'g\'ri tanlangan!')
            else:
                messages.error(request, 'Login yoki parol noto\'g\'ri!')
        else:
            messages.error(request, 'Login yoki parol noto\'g\'ri!')
    else:
        form = LoginForm()

    return render(request, 'pos/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def waiter_dashboard(request):
    try:
        if request.user.userprofile.role != 'waiter':
            return redirect('admin_dashboard')
    except UserProfile.DoesNotExist:
        return redirect('login')

    tables = Table.objects.filter(is_active=True).order_by('number')
    active_orders = Order.objects.filter(status='active')

    table_data = []
    for table in tables:
        order = active_orders.filter(table=table).first()
        table_data.append({
            'table': table,
            'order': order,
            'has_order': order is not None,
            'total': order.total if order else 0,
        })

    tax_rate = get_tax_rate()

    return render(request, 'pos/waiter_dashboard.html', {
        'table_data': table_data,
        'user_name': request.user.first_name or request.user.username,
        'tax_rate': tax_rate,
    })


@login_required
def table_orders(request, table_id):
    try:
        if request.user.userprofile.role != 'waiter':
            return redirect('admin_dashboard')
    except UserProfile.DoesNotExist:
        return redirect('login')

    table = get_object_or_404(Table, id=table_id)
    order = Order.objects.filter(table=table, status='active').first()
    categories = Category.objects.all()
    menu_items = MenuItem.objects.filter(is_active=True)

    category_filter = request.GET.get('category', 'all')
    if category_filter != 'all':
        menu_items = menu_items.filter(category__slug=category_filter)

    tax_rate = get_tax_rate()
    kg_default_weights = [0.1, 0.25, 0.5, 1, 2, 5]
    kg_rounding = 0

    return render(request, 'pos/order_panel.html', {
        'table': table,
        'order': order,
        'categories': categories,
        'menu_items': menu_items,
        'current_category': category_filter,
        'tax_rate': tax_rate,
        'kg_default_weights': kg_default_weights,
        'kg_rounding': kg_rounding,
    })


@login_required
@require_POST
def add_item(request, table_id, item_id):
    try:
        if request.user.userprofile.role != 'waiter':
            return JsonResponse({'success': False, 'error': 'Ruxsat yo\'q'})
    except UserProfile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Profil topilmadi'})

    table = get_object_or_404(Table, id=table_id)
    menu_item = get_object_or_404(MenuItem, id=item_id)
    weight_kg = request.POST.get('weight_kg')

    order, created = Order.objects.get_or_create(
        table=table,
        status='active',
        defaults={'waiter': request.user}
    )

    if menu_item.is_weight_based and weight_kg:
        try:
            weight_value = Decimal(weight_kg)
        except Exception:
            return JsonResponse({'success': False, 'error': 'Og\'irlik noto\'g\'ri kiritildi'})

        if weight_value <= 0:
            return JsonResponse({'success': False, 'error': 'Og\'irlik 0 dan katta bo\'lishi kerak'})
        if weight_value < menu_item.min_weight:
            return JsonResponse({'success': False, 'error': f'Eng kam og\'irlik {menu_item.min_weight} kg'})
        if weight_value > menu_item.stock_kg:
            return JsonResponse({'success': False, 'error': 'Skladda yetarli og\'irlik yo\'q'})

        order_item, created = OrderItem.objects.get_or_create(
            order=order,
            menu_item=menu_item,
            defaults={
                'price_at_time': menu_item.price_per_kg or menu_item.price,
                'weight_kg': weight_value,
            }
        )
        if not created:
            order_item.weight_kg += weight_value
            order_item.save()

        menu_item.stock_kg = max(menu_item.stock_kg - weight_value, 0)
        menu_item.save()
    else:
        order_item, created = OrderItem.objects.get_or_create(
            order=order,
            menu_item=menu_item,
            defaults={'price_at_time': menu_item.price}
        )
        if not created:
            order_item.quantity += 1
            order_item.save()

    return JsonResponse({
        'success': True,
        'item_name': menu_item.name,
        'order_total': order.total,
    })


@login_required
@require_POST
def change_qty(request, item_id):
    try:
        if request.user.userprofile.role != 'waiter':
            return JsonResponse({'success': False})
    except UserProfile.DoesNotExist:
        return JsonResponse({'success': False})

    order_item = get_object_or_404(OrderItem, id=item_id)
    order = order_item.order
    delta = int(request.POST.get('delta', 0))

    if order_item.is_weight_item:
        if delta < 0:
            order_item.delete()
        else:
            return JsonResponse({
                'success': True,
                'order_total': order.total,
                'item_total': order_item.total,
            })
    else:
        order_item.quantity += delta
        if order_item.quantity <= 0:
            order_item.delete()
        else:
            order_item.save()

    if order.items.count() == 0:
        order.delete()
        return JsonResponse({'success': True, 'order_total': 0, 'deleted': True})

    return JsonResponse({
        'success': True,
        'order_total': order.total,
        'item_total': order_item.total if hasattr(order_item, 'total') else 0,
    })


@login_required
def save_order(request, order_id):
    try:
        if request.user.userprofile.role != 'waiter':
            return redirect('admin_dashboard')
    except UserProfile.DoesNotExist:
        return redirect('login')

    with transaction.atomic():
        order = get_object_or_404(
            Order.objects.select_related('table', 'waiter').prefetch_related('items', 'items__menu_item'),
            id=order_id,
            status='active',
        )
        order.status = 'completed'
        order.save()
        save_receipt_snapshot(order)

    messages.success(request, f'Stol #{order.table.number} zakazi saqlandi!')
    return redirect('waiter_dashboard')


@login_required
def clear_order(request, order_id):
    try:
        profile = get_or_create_user_profile(request.user)
    except UserProfile.DoesNotExist:
        return redirect('login')

    if profile.role not in ('waiter', 'admin'):
        return redirect('login')

    order = get_object_or_404(Order, id=order_id, status='active')
    if request.method == 'POST':
        order.status = 'cancelled'
        order.save()
        messages.success(request, 'Zakaz tozalandi')
        if profile.role == 'admin':
            return redirect('admin_orders')
        return redirect('waiter_dashboard')

    return render(request, 'pos/clear_confirm.html', {
        'order': order,
        'is_admin': profile.role == 'admin',
    })


@login_required
def print_check(request, order_id):
    try:
        if request.user.userprofile.role != 'waiter':
            return redirect('admin_dashboard')
    except UserProfile.DoesNotExist:
        return redirect('login')

    order = get_object_or_404(Order, id=order_id)
    tax_rate = get_tax_rate()
    return render(request, 'pos/check_modal.html', {
        'order': order,
        'tax_rate': tax_rate,
    })


@login_required
def scale_weight(request):
    try:
        if request.user.userprofile.role != 'waiter':
            return JsonResponse({'success': False, 'error': 'Ruxsat yo\'q'})
    except UserProfile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Profil topilmadi'})

    return JsonResponse({'success': False, 'error': 'Taroza tizimi hozircha yoqilmagan'})


# ============== ADMIN VIEWS ==============

@login_required
def admin_dashboard(request):
    try:
        if request.user.userprofile.role != 'admin':
            return redirect('waiter_dashboard')
    except UserProfile.DoesNotExist:
        return redirect('login')

    return redirect('admin_orders')


@login_required
def admin_orders(request):
    try:
        if request.user.userprofile.role != 'admin':
            return redirect('waiter_dashboard')
    except UserProfile.DoesNotExist:
        return redirect('login')

    active_orders = Order.objects.filter(status='active').select_related('table', 'waiter')
    return render(request, 'pos/admin_orders.html', {'orders': active_orders})


@login_required
def admin_menu(request):
    try:
        if request.user.userprofile.role != 'admin':
            return redirect('waiter_dashboard')
    except UserProfile.DoesNotExist:
        return redirect('login')

    menu_items = MenuItem.objects.all().select_related('category')
    return render(request, 'pos/admin_menu.html', {'menu_items': menu_items})


@login_required
def menu_add(request):
    try:
        if request.user.userprofile.role != 'admin':
            return redirect('waiter_dashboard')
    except UserProfile.DoesNotExist:
        return redirect('login')

    if request.method == 'POST':
        form = MenuItemForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Taom qo\'shildi!')
            return redirect('admin_menu')
    else:
        form = MenuItemForm()

    return render(request, 'pos/menu_form.html', {
        'form': form,
        'title': 'Yangi taom qo\'shish',
        'editing': False,
    })


@login_required
def menu_edit(request, item_id):
    try:
        if request.user.userprofile.role != 'admin':
            return redirect('waiter_dashboard')
    except UserProfile.DoesNotExist:
        return redirect('login')

    item = get_object_or_404(MenuItem, id=item_id)
    if request.method == 'POST':
        form = MenuItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Taom tahrirlandi!')
            return redirect('admin_menu')
    else:
        form = MenuItemForm(instance=item)

    return render(request, 'pos/menu_form.html', {
        'form': form,
        'title': 'Taomni tahrirlash',
        'editing': True,
        'item': item,
    })


@login_required
def menu_delete(request, item_id):
    try:
        if request.user.userprofile.role != 'admin':
            return redirect('waiter_dashboard')
    except UserProfile.DoesNotExist:
        return redirect('login')

    item = get_object_or_404(MenuItem, id=item_id)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Taom o\'chirildi!')
        return redirect('admin_menu')

    return render(request, 'pos/menu_delete.html', {'item': item})


@login_required
def admin_tables(request):
    try:
        if request.user.userprofile.role != 'admin':
            return redirect('waiter_dashboard')
    except UserProfile.DoesNotExist:
        return redirect('login')

    tables = Table.objects.all().order_by('number')
    active_count = tables.filter(is_active=True).count()

    if request.method == 'POST':
        count = int(request.POST.get('count', 20))
        current_max = Table.objects.count()

        if count > current_max:
            for i in range(current_max + 1, count + 1):
                Table.objects.get_or_create(number=i)
        elif count < current_max:
            Table.objects.filter(number__gt=count).delete()

        messages.success(request, f'Stollar soni: {count}')
        return redirect('admin_tables')

    return render(request, 'pos/admin_tables.html', {
        'tables': tables,
        'active_count': active_count,
        'total_count': tables.count(),
    })


@login_required
def admin_users(request):
    try:
        if request.user.userprofile.role != 'admin':
            return redirect('waiter_dashboard')
    except UserProfile.DoesNotExist:
        return redirect('login')

    for user in User.objects.filter(userprofile__isnull=True):
        get_or_create_user_profile(user)

    users = User.objects.all().select_related('userprofile')
    return render(request, 'pos/admin_users.html', {'users': users})


@login_required
def user_add(request):
    try:
        if request.user.userprofile.role != 'admin':
            return redirect('waiter_dashboard')
    except UserProfile.DoesNotExist:
        return redirect('login')

    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data.get('password')
            if password:
                user.set_password(password)
            user.save()

            role = request.POST.get('role', 'waiter')
            UserProfile.objects.create(user=user, role=role)

            messages.success(request, 'Xodim qo\'shildi!')
            return redirect('admin_users')
    else:
        form = UserForm()

    return render(request, 'pos/user_form.html', {
        'form': form,
        'title': 'Yangi xodim',
        'editing': False,
    })


@login_required
def user_edit(request, user_id):
    try:
        if request.user.userprofile.role != 'admin':
            return redirect('waiter_dashboard')
    except UserProfile.DoesNotExist:
        return redirect('login')

    user = get_object_or_404(User, id=user_id)
    profile = get_or_create_user_profile(user)
    if request.method == 'POST':
        current_password = user.password
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data.get('password')
            if password:
                user.set_password(password)
            else:
                user.password = current_password
            user.save()

            role = request.POST.get('role', 'waiter')
            profile.role = role
            profile.save()

            messages.success(request, 'Xodim tahrirlandi!')
            return redirect('admin_users')
    else:
        form = UserForm(instance=user)

    return render(request, 'pos/user_form.html', {
        'form': form,
        'title': 'Xodimni tahrirlash',
        'editing': True,
        'user_obj': user,
    })


@login_required
def user_delete(request, user_id):
    try:
        if request.user.userprofile.role != 'admin':
            return redirect('waiter_dashboard')
    except UserProfile.DoesNotExist:
        return redirect('login')

    user = get_object_or_404(User, id=user_id)
    if user == request.user:
        messages.error(request, 'O\'zingizni o\'chirib bo\'lmaydi!')
        return redirect('admin_users')

    if request.method == 'POST':
        user.delete()
        messages.success(request, 'Xodim o\'chirildi!')
        return redirect('admin_users')

    return render(request, 'pos/user_delete.html', {'user_obj': user})


@login_required
def admin_reports(request):
    try:
        if request.user.userprofile.role != 'admin':
            return redirect('waiter_dashboard')
    except UserProfile.DoesNotExist:
        return redirect('login')

    today = timezone.now().date()
    today_orders = Order.objects.filter(
        status='completed',
        created_at__date=today
    ).prefetch_related('items')
    today_total = sum(order.total for order in today_orders)
    today_count = today_orders.count()

    all_orders = Order.objects.filter(status='completed').prefetch_related('items')
    all_total = sum(order.total for order in all_orders)
    all_count = all_orders.count()
    kg_sold_total = sum(
        float(item.weight_kg)
        for order in all_orders
        for item in order.items.all()
        if item.is_weight_item
    )

    tax_rate = get_tax_rate()

    return render(request, 'pos/admin_reports.html', {
        'today_total': today_total,
        'today_count': today_count,
        'all_total': all_total,
        'all_count': all_count,
        'tax_rate': tax_rate,
        'kg_sold_total': kg_sold_total,
    })


@login_required
def clear_history(request):
    try:
        if request.user.userprofile.role != 'admin':
            return redirect('waiter_dashboard')
    except UserProfile.DoesNotExist:
        return redirect('login')

    if request.method == 'POST':
        SavedReceipt.delete_expired()

        with transaction.atomic():
            # Barcha completed order'larni chek'ni saklash oldin o'chirish
            completed_orders = (
                Order.objects
                .filter(status='completed')
                .select_related('table', 'waiter')
                .prefetch_related('items', 'items__menu_item')
            )
            orders_count = completed_orders.count()
            expires_at = SavedReceipt.expiry_time()

            for order in completed_orders:
                if not hasattr(order, 'saved_receipt'):
                    save_receipt_snapshot(order, expires_at=expires_at)

            # Endi o'chirish
            completed_orders.delete()

        messages.success(request, f'{orders_count} zakaz tarixga saqlandi va o\'chirildi!')
        return redirect('admin_reports')

    return redirect('admin_reports')


@login_required
def saved_receipts(request):
    """Admin - 3 kunlik saqlangan cheklar"""
    try:
        if request.user.userprofile.role != 'admin':
            return redirect('waiter_dashboard')
    except UserProfile.DoesNotExist:
        return redirect('login')

    now = timezone.now()
    SavedReceipt.delete_expired(now)
    ensure_recent_receipt_snapshots(now)

    # Faqat hali ham aktual cheklar
    receipts = SavedReceipt.objects.filter(expires_at__gt=now).order_by('-created_at')

    return render(request, 'pos/saved_receipts.html', {
        'receipts': receipts,
    })


@login_required
def receipt_detail(request, receipt_id):
    """Saqlangan chekni ko'rish"""
    try:
        if request.user.userprofile.role != 'admin':
            return redirect('waiter_dashboard')
    except UserProfile.DoesNotExist:
        return redirect('login')
    
    now = timezone.now()
    SavedReceipt.delete_expired(now)

    receipt = get_object_or_404(SavedReceipt, id=receipt_id, expires_at__gt=now)
    tax_rate = get_tax_rate()
    
    return render(request, 'pos/receipt_detail.html', {
        'receipt': receipt,
        'tax_rate': tax_rate,
    })

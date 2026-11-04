from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Count, Prefetch, ProtectedError, Sum
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status as http_status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from restaurant.models import (
    Category, MenuItem, Order, OrderItem, OrderStatusEvent, Profile, Reservation,
    RestaurantSettings, Table,
)
from .models import Book
from .permissions import (
    IsAdminOrReadOnly, IsAdminRole, IsKitchenStaff, OrderPermission, ReservationPermission, get_role,
)
from .serializers import (
    BookSerializer, CategorySerializer, DailyReportQuerySerializer, DailyReportSerializer,
    MenuCategorySerializer, MenuItemSerializer, OrderSerializer, OrderStatusEventSerializer,
    OrderStatusSerializer, ProfileSerializer, ReservationSerializer, RestaurantSettingsSerializer,
    TableAvailabilityQuerySerializer, TableSerializer,
)

# Oshpaz faqat shu holatdagi buyurtmalarni ko'radi.
CHEF_VISIBLE_STATUSES = (Order.NEW, Order.COOKING, Order.READY)
# Oshpaz faqat shu holatlarga o'tkaza oladi.
CHEF_TARGET_STATUSES = (Order.COOKING, Order.READY)


class ProtectedDestroyMixin:
    """Bog'langan yozuv borligi sababli o'chirib bo'lmasa, 500 o'rniga 400 qaytaradi."""
    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {'detail': 'Bu yozuvni o‘chirib bo‘lmaydi: unga bog‘langan boshqa yozuvlar bor.'},
                status=http_status.HTTP_400_BAD_REQUEST,
            )


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.order_by('id')   # sahifalash barqaror bo'lishi uchun tartib shart
    serializer_class = BookSerializer
    filterset_fields = ['author']
    search_fields = ['title', 'author']
    ordering_fields = ['price', 'created_at']


# ---------- Ochiq ma'lumotlar: o'qish hammaga, yozish adminga ----------

class RestaurantSettingsView(generics.RetrieveUpdateAPIView):
    serializer_class = RestaurantSettingsSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_object(self):
        return RestaurantSettings.load()


class CategoryViewSet(ProtectedDestroyMixin, viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ['active']
    search_fields = ['name']
    ordering_fields = ['order', 'name']


class MenuItemViewSet(ProtectedDestroyMixin, viewsets.ModelViewSet):
    queryset = MenuItem.objects.select_related('category')
    serializer_class = MenuItemSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ['category', 'available', 'is_vegetarian', 'spicy']
    search_fields = ['name', 'description', 'category__name']
    ordering_fields = ['name', 'price', 'preparation_minutes']


class MenuView(generics.ListAPIView):
    """Faol kategoriyalar ichida mavjud taomlar."""
    serializer_class = MenuCategorySerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None
    filter_backends = []

    def get_queryset(self):
        available = MenuItem.objects.filter(available=True).select_related('category')
        return Category.objects.filter(active=True).prefetch_related(
            Prefetch('items', queryset=available, to_attr='available_items'),
        )


class TableViewSet(ProtectedDestroyMixin, viewsets.ModelViewSet):
    queryset = Table.objects.all()
    serializer_class = TableSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ['location', 'active', 'seats']
    search_fields = ['number']
    ordering_fields = ['number', 'seats']

    @extend_schema(parameters=[TableAvailabilityQuerySerializer], responses=TableSerializer(many=True))
    @action(detail=False, methods=['get'], pagination_class=None, filter_backends=[])
    def available(self, request):
        query = TableAvailabilityQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        start = query.validated_data['start']

        restaurant = RestaurantSettings.load()
        error = restaurant.booking_error(start)
        if error:
            raise ValidationError({'start': [error]})

        busy = Reservation.objects.filter(
            start__lt=restaurant.reservation_end(start), end__gt=start,
        ).exclude(status__in=Reservation.FREE_STATUSES).values('table')
        tables = Table.objects.filter(
            active=True, seats__gte=query.validated_data['guests'],
        ).exclude(pk__in=busy).order_by('seats', 'number')
        return Response(self.get_serializer(tables, many=True).data)


# ---------- Bron ----------

class ReservationViewSet(ProtectedDestroyMixin, viewsets.ModelViewSet):
    queryset = Reservation.objects.select_related('table', 'customer', 'created_by')
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated, ReservationPermission]
    filterset_fields = ['table', 'status', 'customer']
    search_fields = ['name', 'phone', 'note']
    ordering_fields = ['start', 'end', 'status', 'created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        role = get_role(self.request.user)
        if role in (Profile.ADMIN, Profile.WAITER):
            return queryset
        if role == Profile.CUSTOMER:
            return queryset.filter(customer=self.request.user)
        return queryset.none()

    def perform_create(self, serializer):
        user = self.request.user
        customer = serializer.validated_data.get('customer') or user
        serializer.save(customer=customer, created_by=user)

    @extend_schema(request=None, responses=ReservationSerializer)
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        reservation = self.get_object()
        if reservation.status not in Reservation.CANCELLABLE_STATUSES:
            raise ValidationError({'status': ['Bu holatdagi bronni bekor qilib bo‘lmaydi.']})
        reservation.status = Reservation.CANCELLED
        reservation.save(update_fields=['status', 'updated_at'])
        return Response(self.get_serializer(reservation).data)


# ---------- Buyurtma ----------

class OrderViewSet(ProtectedDestroyMixin, viewsets.ModelViewSet):
    queryset = Order.objects.select_related('table').prefetch_related('items__menu_item')
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, OrderPermission]
    filterset_fields = ['status', 'order_type', 'table', 'customer', 'waiter']
    search_fields = ['note', 'items__menu_item__name']
    ordering_fields = ['created_at', 'total', 'status']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        role = get_role(user)
        if role in (Profile.ADMIN, Profile.WAITER):
            return queryset
        if role == Profile.CHEF:
            return queryset.filter(status__in=CHEF_VISIBLE_STATUSES)
        if role == Profile.CUSTOMER:
            return queryset.filter(customer=user)
        return queryset.none()

    def perform_create(self, serializer):
        user = self.request.user
        role = get_role(user)
        if role == Profile.CUSTOMER:
            serializer.save(customer=user, waiter=None)
        elif role == Profile.WAITER:
            serializer.save(waiter=user)
        else:
            serializer.save()

    @extend_schema(request=OrderStatusSerializer, responses=OrderSerializer)
    @action(detail=True, methods=['post'], url_path='set-status', serializer_class=OrderStatusSerializer)
    def set_status(self, request, pk=None):
        order = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data['status']

        if get_role(request.user) == Profile.CHEF and new_status not in CHEF_TARGET_STATUSES:
            raise PermissionDenied('Oshpaz holatni faqat «cooking» yoki «ready» ga o‘zgartira oladi.')
        try:
            order.change_status(new_status, request.user)
        except DjangoValidationError as error:
            raise ValidationError({'status': error.messages})
        return Response(OrderSerializer(order, context=self.get_serializer_context()).data)

    @extend_schema(responses=OrderSerializer(many=True))
    @action(
        detail=False, methods=['get'], pagination_class=None, filter_backends=[],
        permission_classes=[permissions.IsAuthenticated, IsKitchenStaff],
    )
    def kitchen(self, request):
        orders = self.get_queryset().filter(status__in=(Order.NEW, Order.COOKING)).order_by('created_at', 'id')
        return Response(self.get_serializer(orders, many=True).data)


class OrderStatusEventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = OrderStatusEvent.objects.select_related('order', 'actor')
    serializer_class = OrderStatusEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['order', 'status', 'actor']
    ordering_fields = ['changed_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        role = get_role(user)
        if role in (Profile.ADMIN, Profile.WAITER):
            return queryset
        if role == Profile.CHEF:
            return queryset.filter(order__status__in=CHEF_VISIBLE_STATUSES)
        if role == Profile.CUSTOMER:
            return queryset.filter(order__customer=user)
        return queryset.none()


# ---------- Admin ----------

class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.select_related('user')
    serializer_class = ProfileSerializer
    permission_classes = [IsAdminRole]
    filterset_fields = ['role']
    search_fields = ['user__username', 'phone']
    ordering_fields = ['user__username', 'role', 'created_at']


class DailyReportView(APIView):
    permission_classes = [IsAdminRole]

    @extend_schema(parameters=[DailyReportQuerySerializer], responses=DailyReportSerializer)
    def get(self, request):
        query = DailyReportQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        day = query.validated_data.get('date') or timezone.localdate()

        paid = Order.objects.filter(status=Order.PAID, paid_at__date=day).aggregate(
            count=Count('id'), total=Sum('total', default=Decimal('0')),
        )
        top_items = (
            OrderItem.objects.filter(order__status=Order.PAID, order__paid_at__date=day)
            .values('menu_item', 'menu_item__name')
            .annotate(sold=Sum('quantity'), revenue=Sum('line_total'))
            .order_by('-sold', 'menu_item__name')[:5]
        )
        report = {
            'date': day,
            'orders_count': Order.objects.filter(created_at__date=day).count(),
            'paid_orders_count': paid['count'],
            'paid_total': paid['total'],
            'top_items': [
                {
                    'menu_item': row['menu_item'],
                    'name': row['menu_item__name'],
                    'quantity': row['sold'],
                    'revenue': row['revenue'],
                }
                for row in top_items
            ],
        }
        return Response(DailyReportSerializer(report).data)

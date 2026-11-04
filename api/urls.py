from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    BookViewSet, CategoryViewSet, DailyReportView, MenuItemViewSet, MenuView, OrderStatusEventViewSet,
    OrderViewSet, ProfileViewSet, ReservationViewSet, RestaurantSettingsView, TableViewSet,
)

router = DefaultRouter()
router.register('books', BookViewSet)
router.register('categories', CategoryViewSet)
router.register('menu-items', MenuItemViewSet)
router.register('tables', TableViewSet)
router.register('reservations', ReservationViewSet)
router.register('orders', OrderViewSet)
router.register('profiles', ProfileViewSet)
router.register('order-events', OrderStatusEventViewSet)

urlpatterns = [
    path('settings/', RestaurantSettingsView.as_view()),
    path('menu/', MenuView.as_view()),
    path('reports/daily/', DailyReportView.as_view()),
] + router.urls

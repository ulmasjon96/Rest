from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    BookViewSet, CategoryViewSet, ChangePasswordAPIView, DailyReportView, LogoutView, MenuItemViewSet, MenuView,
    MyProductViewSet, OrderStatusEventViewSet, OrderViewSet, ProductViewSet, ProfileViewSet, RegisterAPIView, ReservationViewSet,
    RestaurantSettingsView, TableViewSet, UserDetailAPIView, UserListAPIView, UserUpdateAPIView,
)

router = DefaultRouter()
router.register('books', BookViewSet)
router.register('products', ProductViewSet)
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
    path('auth/register/', RegisterAPIView.as_view()),
    path('auth/logout/', LogoutView.as_view()),
    path('auth/change-password/', ChangePasswordAPIView.as_view()),
    path('users/', UserListAPIView.as_view()),
    path('users/me/', UserUpdateAPIView.as_view()),
    path('users/me/products/', MyProductViewSet.as_view({'get': 'list'})),
    path('users/me/products/<int:pk>/', MyProductViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'})),
    path('users/<int:pk>/', UserDetailAPIView.as_view()),
] + router.urls

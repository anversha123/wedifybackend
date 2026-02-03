from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'planners', views.PlannerViewSet, basename='planner')
router.register(r'bookings', views.BookingRequestViewSet, basename='booking')

urlpatterns = [
    path('create-payment-intent/', views.create_payment_intent, name='create-payment-intent'),
    path('login/planner/', views.planner_login, name='planner-login'),
    path('login/admin/', views.admin_login, name='admin-login'),
    path('login/user/', views.user_login, name='user-login'),
    path('signup/user/', views.user_signup, name='user-signup'),
    path('', include(router.urls)),
]


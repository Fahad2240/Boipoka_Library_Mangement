from django.urls import path
from .import views
from django.contrib.auth import views as auth_views
from .forms import *
app_name = 'boipoka_app'

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('book_list/',views.book_list, name='book_list'),
    path('books/<int:pk>/', views.book_details, name='book_details'),
    path('create-subscription/<int:pk>/', views.create_subscription, name='create-subscription'),
    path('change_subscription',views.change_subscription, name='change_subscription'),
    path('borrow/<int:pk>/', views.borrow_book, name='borrow_book'),
    path('return-book/<int:pk>/', views.return_book, name='return_book'),
    path('add_book/', views.add_book, name='add_book'),
    path('edit_book/<int:pk>/', views.edit_book, name='edit_book'),
    path('delete_book/<int:pk>/', views.delete_book, name='delete_book'),
    path('user_details/<int:pk>/', views.user_details, name='user_details'),
    path('user/send_reminder/<int:pk>/', views.send_reminder, name='send_reminder'),
    path('user/edit_user/<int:pk>/', views.edit_user, name='edit_user'),
    path('user/delete_user/<int:pk>/', views.delete_user, name='delete_user'),
    path('users',views.users,name='users'),
    path('user/update_due_date/<int:pk>/', views.update_due_date, name='update_due_date'),
    path('subscription/',views.subscription, name='subscription'),
    path('new_subscription_creation/',views.new_subscription_creation, name='new_subscription_creation'),	
    path('subscription/renew/', views.renew_subscription, name='renew_subscription'),
    path('user/delete_subscription/<int:pk>/', views.delete_subscription, name='delete_subscription'),
    path('manage_subscriptions_starting/<int:pk>/', views.manage_subscriptions_starting, name='manage_subscriptions_starting'),
    path('manage_subscriptions_ending/<int:pk>/', views.manage_subscriptions_ending, name='manage_subscriptions_ending'),
    path('user/delete_subscription/<int:pk>/', views.delete_subscription, name='delete_subscription'),
    # path('book_details/<int:pk>', views.book_details, name='book_details'),
    # path('add_book/', views.add_book, name='add_book'),
]
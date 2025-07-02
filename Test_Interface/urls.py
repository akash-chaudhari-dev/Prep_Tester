# Test_Interface/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Authentication URLs (from your previous login/signup setup)
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),

    # Core Portal URLs
    path('', views.dashboard_view, name='dashboard'), # This is now the main entry point after auth
    path('branch-selection/', views.branch_selection_view, name='branch_selection'),

    # Test related URLs
    path('test/start/<int:test_id>/', views.start_test, name='start_test'),
    path('test/<int:test_id>/q/<int:q_index>/', views.question_view, name='question_view'),
    path('test/<int:test_id>/result/', views.display_test_result, name='display_test_result'),

    # User History URL
    path('history/', views.user_history_view, name='user_history'),

    # Note: The 'subject_list' URL is effectively replaced by 'dashboard'
    # If you still want a separate subject list page, you'd need a new view for it.
]

# Test_Interface/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Core Portal URLs
    path('', views.dashboard_view, name='dashboard'), # This is now the main entry point after auth
    path('branch-selection/', views.branch_selection_view, name='branch_selection'),

    # Test related URLs
    path('test/start/<int:test_id>/', views.start_test, name='start_test'),
    path('test/<int:test_id>/question/<int:q_index>/', views.question_partial_view, name='question_partial'),
    path('test/<int:test_id>/q/<int:q_index>/', views.question_view, name='question_view'),
    path('test/<int:test_id>/result/', views.display_test_result, name='display_test_result'),

    # User History URL
    path('history/', views.user_history_view, name='user_history'),

    path('dashboard/', views.user_profile_view, name='user_dashboard'),

    path('about/', views.about_view, name='about'),
    path('terms-and-conditions/', views.terms_and_conditions_view, name='terms_and_conditions'),

]

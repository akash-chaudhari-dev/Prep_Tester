# Test_Interface/admin.py

from django.contrib import admin
from .models import Branch, Subject, Test, Question, UserAttempt, UserProfile

# Inline for Questions within Test Admin
class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1 # Number of empty forms to display
    fields = ['text', 'option1', 'option2', 'option3', 'option4', 'correct_option', 'solution']

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'branch')
    list_filter = ('branch',)
    search_fields = ('name', 'branch__name')
    raw_id_fields = ('branch',) # Improve widget for selecting branch if many

@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'duration_minutes', 'total_marks', 'created_at')
    list_filter = ('subject__branch', 'subject') # Filter by subject and its branch
    search_fields = ('name', 'subject__name', 'subject__branch__name')
    raw_id_fields = ('subject',)
    inlines = [QuestionInline] # Add questions directly when creating/editing a test

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'test', 'correct_option')
    list_filter = ('test__subject__branch', 'test__subject', 'test')
    search_fields = ('text', 'test__name')
    raw_id_fields = ('test',)

@admin.register(UserAttempt)
class UserAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'selected_option', 'is_correct', 'attempted_at')
    list_filter = ('user', 'is_correct', 'question__test__subject__branch', 'question__test')
    search_fields = ('user__username', 'question__text')
    raw_id_fields = ('user', 'question')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'branch')
    list_filter = ('branch',)
    search_fields = ('user__username', 'branch__name')
    raw_id_fields = ('user', 'branch') # Improve widget for selecting user/branch if many


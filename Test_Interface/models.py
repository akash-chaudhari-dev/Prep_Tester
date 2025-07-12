# Test_Interface/models.py

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Branch(models.Model):
    """
    Represents an engineering branch (e.g., Computer Science, Electronics).
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Branches"
        ordering = ['name'] # Order branches alphabetically

    def __str__(self):
        return self.name

class Subject(models.Model):
    """
    Represents a subject under a specific branch.
    """
    name = models.CharField(max_length=200)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='subjects')
    description = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('name', 'branch') # A subject name must be unique within a branch
        ordering = ['branch__name', 'name'] # Order by branch then subject name

    def __str__(self):
        return f"{self.name} ({self.branch.name})"

class Test(models.Model):
    """
    Represents a specific test paper for a subject.
    """
    name = models.CharField(max_length=255)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='tests')
    duration_minutes = models.IntegerField(default=60, help_text="Duration of the test in minutes")
    total_marks = models.IntegerField(default=100, help_text="Total marks for the test")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('name', 'subject') # Test name must be unique within a subject
        ordering = ['subject__name', 'name'] # Order by subject then test name

    def __str__(self):
        return f"{self.name} ({self.subject.name})"

class Question(models.Model):
    """
    Represents a single question within a test.
    """
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    option1 = models.CharField(max_length=500)
    option2 = models.CharField(max_length=500)
    option3 = models.CharField(max_length=500)
    option4 = models.CharField(max_length=500)
    correct_option = models.IntegerField(
        choices=[(1, 'Option 1'), (2, 'Option 2'), (3, 'Option 3'), (4, 'Option 4')]
    )
    solution = models.TextField(blank=True, null=True, help_text="Detailed explanation for the correct answer")

    class Meta:
        ordering = ['id'] # Order questions by their creation order (default ID)

    def __str__(self):
        return f"Q{self.id}: {self.text[:50]}..." # Show first 50 chars of question text

class UserAttempt(models.Model):
    """
    Records a user's attempt for a specific question in a test.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attempts')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    reviewed = models.BooleanField(default=False)
    selected_option = models.IntegerField(
        choices=[(1, 'Option 1'), (2, 'Option 2'), (3, 'Option 3'), (4, 'Option 4')]
    )
    is_correct = models.BooleanField(default=False)
    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # A user can only attempt a specific question once per test session.
        # For a full test history, we'd need a 'TestSession' model.
        # For simplicity here, we assume one attempt per question per test.
        unique_together = ('user', 'question')
        ordering = ['attempted_at']

    def __str__(self):
        return f"{self.user.username}'s attempt on Q{self.question.id} ({'Correct' if self.is_correct else 'Incorrect'})"

class UserProfile(models.Model):
    """
    Extends Django's built-in User model to store additional information,
    like the user's selected branch and profile picture URL.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True,
                               help_text="The user's selected engineering branch.")
    # New field to store the URL of the externally hosted profile picture
    profile_picture_url = models.URLField(max_length=500, blank=True, null=True,
                                        help_text="URL of the user's profile picture hosted externally.")
    academic_year = models.CharField(max_length=10, blank=True, null=True,
                            help_text="The academic year of the user (e.g., 2023-2024).")
    mobile_number = models.CharField(max_length=15, blank=True, null=True,
                                      help_text="User's mobile number (e.g., +919876543210).")

    def __str__(self):
        return f"{self.user.username}'s Profile"

# Signal to create or update UserProfile whenever a User is created/saved
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    instance.profile.save() # Ensure profile is always saved/updated

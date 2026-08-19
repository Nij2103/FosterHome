"""
apps.core.models

Stores contact form submissions received from users.
Only accessible to superusers/administrators in the Django Admin panel.
"""

from django.db import models


class ContactMessage(models.Model):
    SUBJECT_CHOICES = [
        ("technical", "Technical Support"),
        ("training", "Training & Onboarding"),
        ("data", "Data & Privacy"),
        ("access", "Account Access"),
        ("feedback", "Feedback & Suggestions"),
        ("other", "Other"),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    organization = models.CharField(max_length=200, blank=True)
    subject = models.CharField(max_length=50, choices=SUBJECT_CHOICES, default="other")
    message = models.TextField()
    is_read = models.BooleanField(default=False, help_text="Mark whether admin has reviewed this message.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email}) - {self.get_subject_display()}"

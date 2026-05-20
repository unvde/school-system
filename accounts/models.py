from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    ROLE_PRINCIPAL = 'principal'
    ROLE_CAMPUS_MANAGER = 'campus_manager'
    ROLE_TEACHER = 'teacher'

    ROLE_CHOICES = [
        (ROLE_PRINCIPAL, '校长'),
        (ROLE_CAMPUS_MANAGER, '校区长'),
        (ROLE_TEACHER, '教师'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    campus = models.ForeignKey(
        'organization.Campus',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_profiles',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.username} - {self.get_role_display()}'

from django.db import models
from django.contrib.auth.models import User
from datetime import date


class Decision(models.Model):
    RESULT_CHOICES = [
        ('DO IT', 'DO IT'),
        ('DO SMALL VERSION', 'DO SMALL VERSION'),
        ('DELAY', 'DELAY'),
        ('SKIP', 'SKIP'),
    ]
    ENERGY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    PRIORITY_CHOICES = [
        ('study', 'Study'),
        ('health', 'Health'),
        ('work', 'Work'),
        ('fun', 'Fun'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    task = models.CharField(max_length=255)

    q1 = models.BooleanField(default=False)
    q2 = models.BooleanField(default=False)
    q3 = models.BooleanField(default=False)
    q4 = models.BooleanField(default=False)
    q5 = models.BooleanField(default=False)

    result = models.CharField(max_length=20, choices=RESULT_CHOICES)
    energy = models.CharField(max_length=10, choices=ENERGY_CHOICES)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='other')
    is_quick = models.BooleanField(default=False)
    notes = models.TextField(blank=True, default='')
    bookmarked = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.task} → {self.result}"


class Streak(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    count = models.IntegerField(default=0)
    last_used = models.DateField(default=date.today)
    best_streak = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username}: {self.count} day streak"


class Goal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.CharField(max_length=200)
    completed = models.BooleanField(default=False)
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.text
from django.db import models


class Registration(models.Model):
    email = models.EmailField(max_length=254, unique=True)
    name = models.CharField(max_length=100, blank=True)
    interest = models.CharField(max_length=10, choices=[('reader', 'Reader'), ('researcher', 'Researcher / contributor'), ('both', 'Both')])
    privacy_version = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)


class CollectionState(models.Model):
    # Singleton seeded by migration; locked before every collection mutation.
    id = models.PositiveSmallIntegerField(primary_key=True, default=1)
    paused = models.BooleanField(default=True)
    retained_count = models.PositiveIntegerField(default=0)
    minute = models.BigIntegerField(default=0)
    minute_attempts = models.PositiveIntegerField(default=0)
    day = models.BigIntegerField(default=0)
    day_attempts = models.PositiveIntegerField(default=0)


class AddressBudget(models.Model):
    key = models.CharField(max_length=64, primary_key=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    expires_at = models.DateTimeField(db_index=True)


class Erasure(models.Model):
    key = models.CharField(max_length=64, primary_key=True)
    expires_at = models.DateTimeField(db_index=True)


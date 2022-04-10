from click import group
from django.db import models
from django.utils.crypto import get_random_string

GROUP_CHOICES = [
    ("A", "A"),
    ("B", "B"),
    ("C", "C"),
    ("D", "D"),
    ("E", "E"),
    ("F", "F"),
    ("G", "G"),
    ("H", "H"),
    ("I", "I"),
    ("J", "J"),
    ("K", "K"),
    ("L", "L"),
    ("M", "M"),
    ("N", "N"),
    ("O", "O"),
    ("P", "P"),
    ("Q", "Q"),
    ("R", "R"),
    ("S", "S"),
    ("T", "T"),
    ("U", "U"),
    ("V", "V"),
    ("W", "W"),
    ("CC1", "CC1"),
]


def generate_random_token():
    return get_random_string(length=32)


class Subscriber(models.Model):
    email = models.EmailField()
    group = models.CharField(max_length=5, choices=GROUP_CHOICES)
    unsubscribe_token = models.CharField(max_length=32, default=generate_random_token)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email


class Fetch(models.Model):
    group = models.CharField(max_length=200)
    date = models.DateField()
    hash = models.CharField(max_length=32)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.group} {self.date}"

from django.forms import ValidationError
from django.utils import timezone
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import User
# Create your models here.

#Book Model

class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    image=models.ImageField(upload_to='book_images',blank=True,null=True)
    availability_status = models.BooleanField(default=True)  # True if available for borrowing
    total_copies = models.IntegerField(default=1)
    available_copies = models.IntegerField(default=1)
    
    def __str__(self):
        return f"{self.title} by {self.author}"
    


# Subscription Model
class Subscription(models.Model):
    TIER_CHOICES = [
        ('Basic', 'Basic'),
        ('Premium', 'Premium'),
        ('VIP', 'VIP'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    subscription_type = models.CharField(max_length=10, choices=TIER_CHOICES, default='Basic')
    # The `max_books` field in the `Subscription` model is determining the maximum number of books a
    # user can borrow based on their subscription tier.
    max_books = models.IntegerField(default=2)  # Default to Basic
    subscription_start = models.DateTimeField(default=timezone.now)
    subscription_end = models.DateTimeField()


    def save(self, *args, **kwargs):
        # Set subscription duration (e.g., 30 days)
        if not self.subscription_end:
            self.subscription_end = self.subscription_start + timedelta(days=30)

        # Set max_books based on subscription tier
        if self.subscription_type == 'Basic':
            self.max_books = 2
        elif self.subscription_type == 'Premium':
            self.max_books = 5
        elif self.subscription_type == 'VIP':
            self.max_books = 10
        
        super(Subscription, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.subscription_type}"
    @property
    def borrowing_set(self):
        return Borrowing.objects.filter(subscription=self) 


class Borrowing(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    borrowed_on = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)  # Add due date field
    returned_at = models.DateTimeField(null=True, blank=True)  # Track when the book was returned
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='borrowings')
    
    def save(self, *args, **kwargs):
        # Check if the user has a subscription
        # Proceed to set the due date if not already set
        if not self.due_date:
            if self.borrowed_on is None:
                self.borrowed_on = timezone.now()
            elif self.borrowed_on.tzinfo is None:
                self.borrowed_on = timezone.make_aware(self.borrowed_on)
        
            self.due_date = self.borrowed_on + timedelta(days=14)
            
        # Decrease available copies of the book

        super(Borrowing, self).save(*args, **kwargs)

    def return_book(self):
        # Mark the book as returned
        self.returned_at = timezone.now()
        self.book.available_copies += 1  # Increase the available copies
        self.book.save()
        self.save()
    def __str__(self):
        return f"{self.user.username} borrowed {self.book.title} on {self.borrowed_on} by {self.subscription}"

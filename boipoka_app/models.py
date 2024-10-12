from django.utils import timezone  # Importing timezone to manage date and time
from datetime import timedelta  # Importing timedelta for date arithmetic
from django.db import models  # Importing models for database models
from django.contrib.auth.models import User  # Importing User model for authentication
# Create your models here.

# Book Model
class Book(models.Model):  # Defining a model for books
    title = models.CharField(max_length=255)  # Field for book title
    author = models.CharField(max_length=255)  # Field for book author
    description = models.TextField(blank=True, null=True)  # Optional field for book description
    image = models.ImageField(upload_to='book_images', blank=True, null=True)  # Optional field for book image upload
    availability_status = models.BooleanField(default=True)  # True if available for borrowing
    total_copies = models.IntegerField(default=1)  # Total number of copies of the book
    available_copies = models.IntegerField(default=1)  # Number of copies currently available for borrowing
    is_suspended = models.BooleanField(default=False)

    def __str__(self):  # String representation of the Book model
        return f"{self.title} by {self.author}"  # Returns title and author for easy identification

# Subscription Model
class Subscription(models.Model):  # Defining a model for user subscriptions
    TIER_CHOICES = [  # Choices for subscription tiers
        ('Basic', 'Basic'),  # Basic tier
        ('Premium', 'Premium'),  # Premium tier
        ('VIP', 'VIP'),  # VIP tier
    ]
    # tier = models.CharField(max_length=20, choices=TIER_CHOICES)  # (Commented out) Field for subscription tier
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')  # One-to-one relationship with User model
    subscription_type = models.CharField(max_length=10, choices=TIER_CHOICES, default='Basic')  # Type of subscription chosen by user
    # The `max_books` field in the `Subscription` model is determining the maximum number of books a
    # user can borrow based on their subscription tier.
    max_books = models.IntegerField(default=2)  # Default to Basic subscription (2 books)
    subscription_start = models.DateTimeField(default=timezone.now)  # Subscription start time
    subscription_end = models.DateTimeField()  # Subscription end time
    is_active = models.BooleanField(default=True)
    
    def save(self, *args, **kwargs):  # Overriding the save method to customize saving behavior
        # Set subscription duration (e.g., 30 days)
        if not self.subscription_end:  # Check if subscription_end is not set
            self.subscription_end = self.subscription_start + timedelta(days=30)  # Set end date to 30 days after start

        # Set max_books based on subscription tier
        if self.subscription_type == 'Basic':  # If subscription is Basic
            self.max_books = 2  # Set max books to 2
        elif self.subscription_type == 'Premium':  # If subscription is Premium
            self.max_books = 5  # Set max books to 5
        elif self.subscription_type == 'VIP':  # If subscription is VIP
            self.max_books = 10  # Set max books to 10
        
        super(Subscription, self).save(*args, **kwargs)  # Call the original save method

    def __str__(self):  # String representation of the Subscription model
        return f"{self.user.username} - {self.subscription_type}"  # Returns the username and subscription type

    @property  # Decorator to create a read-only property
    def borrowing_set(self):  # Property to get borrowings related to the subscription
        return Borrowing.objects.filter(subscription=self)  # Returns all borrowings for this subscription


class Borrowing(models.Model):  # Defining a model for book borrowing
    book = models.ForeignKey(Book, on_delete=models.CASCADE)  # Foreign key to Book model
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)  # Foreign key to Subscription model
    borrowed_on = models.DateTimeField(auto_now_add=True)  # Timestamp for when the book was borrowed
    due_date = models.DateTimeField(null=True, blank=True)  # Field for due date of the borrowed book
    returned_at = models.DateTimeField(null=True, blank=True)  # Track when the book was returned
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='borrowings')  # Foreign key to User model
    reissue_state=models.BooleanField(default=False)
    marked_as_unread=models.BooleanField(default=False)
    is_damagedorlost=models.BooleanField(default=False)
    damagedlostat=models.DateTimeField(null=True, blank=True)
    fine_paid=models.BooleanField(default=False)
    fine_paid_approved=models.BooleanField(default=False)
    fine_paid_at=models.DateTimeField(null=True, blank=True)
    def save(self, *args, **kwargs):  # Overriding the save method for Borrowing
        # Check if the user has a subscription
        # Proceed to set the due date if not already set
        if not self.due_date:  # Check if due_date is not set
            if self.borrowed_on is None:  # If borrowed_on is not set
                self.borrowed_on = timezone.now()  # Set borrowed_on to the current time
            elif self.borrowed_on.tzinfo is None:  # If borrowed_on is naive (not timezone-aware)
                self.borrowed_on = timezone.make_aware(self.borrowed_on)  # Make it timezone-aware
        
            self.due_date = self.borrowed_on + timedelta(days=14)  # Set due date to 14 days after borrowed_on
        
        ## Set damagedlostat to the current time if the book is marked as damaged or lost
        if self.is_damagedorlost and not self.damagedlostat:
            self.damagedlostat = timezone.now()
        elif not self.is_damagedorlost:
            self.damagedlostat = None

        # Set fine_paid_at to the current time if the fine is marked as paid and fine_paid_at is not already set
        if self.fine_paid and not self.fine_paid_at:
            self.fine_paid_at = timezone.now()
        elif not self.fine_paid:
            self.fine_paid_at = None  # Reset if the status is changed back to unpaid

        super(Borrowing, self).save(*args, **kwargs)  # Call the original save method

    def return_book(self):  # Method to handle returning a book
        self.returned_at = timezone.now()  # Mark the returned_at field with current time
        self.book.available_copies += 1  # Increase the available copies of the book by 1
        self.book.save()  # Save the updated book instance
        self.save()  # Save the updated borrowing instance
    def reissue(self):
        self.reissue_state=True
        self.save()
        
    def readcheck(self):
        self.marked_as_unread=True
        self.save()
    def __str__(self):  # String representation of the Borrowing model
        return f"{self.user.username} borrowed {self.book.title} on {self.borrowed_on} by {self.subscription}"  # Returns borrowing details

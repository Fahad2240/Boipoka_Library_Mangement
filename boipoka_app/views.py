from datetime import datetime  # Import datetime for date manipulations
from django.core.mail import EmailMessage  # Import EmailMessage for sending emails
import logging  # Import logging for logging errors and information
from smtplib import SMTPException  # Import SMTPException to handle email sending errors
import threading  # Import threading for sending emails in separate threads
from django.shortcuts import get_object_or_404, render, redirect  # Import necessary functions for view handling
from django.contrib.auth import login, authenticate, logout  # Import authentication functions
import requests  # Import requests for making API calls
from boipoka import settings  # Import project settings
from boipoka_app.utils import get_user_subscription  # Import utility function to get user subscription
from .forms import *  # Import all forms from the current package
from .models import *  # Import all models from the current package
from django.contrib.auth.decorators import login_required, user_passes_test  # Import decorators for access control
from django.contrib import messages  # Import messages framework for user feedback
from django.core.mail import send_mail  # Import send_mail function for sending emails
from django.core.files.base import ContentFile  # Import ContentFile for handling file content
from urllib.parse import urlparse  # Import urlparse for URL manipulation
from django.contrib.auth import get_user_model  # Import function to get User model

def index(request):
    return render(request,'boipoka_app/index.html')

def register(request):
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # Save the user to the database
            login(request, user)  # Automatically log the user in
            return redirect('/login/')  # Redirect to home page or any other page
    else:
        form = CustomUserCreationForm()
    return render(request, 'boipoka_app/register.html', {'form': form})


def fetch_books_data(start_index=0, max_results=10):
    api_key = settings.GOOGLE_BOOKS_API_KEY
    url = f"https://www.googleapis.com/books/v1/volumes?q=subject:fiction&startIndex={start_index}&maxResults={max_results}&key={api_key}"
    
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        books = []
        
        if "items" in data:
            for item in data["items"]:
                volume_info = item.get("volumeInfo", {})
                image_url = volume_info.get("imageLinks", {}).get("thumbnail", "")
                image_content = None

                # Fetch image content if available
                if image_url:
                    img_response = requests.get(image_url)
                    if img_response.status_code == 200:
                        image_content = ContentFile(img_response.content, name=urlparse(image_url).path.split('/')[-1])
                
                books.append({
                    "title": volume_info.get("title", ""),
                    "author": ', '.join(volume_info.get("authors", [])),
                    "description": volume_info.get("description", ""),
                    "image": image_content,  # This will be a ContentFile
                    "availability_status": True,
                    "total_copies": 1,
                    "available_copies": 1,
                })
        return books
    return []

def create_books_in_db(book_list):
    for book_data in book_list:
        # Create or update the Book instance in the database
        Book.objects.get_or_create(
            title=book_data['title'],
            defaults={
                'author': book_data['author'],
                'description': book_data['description'],
                'image': book_data['image'],  # This will save the image file correctly
                'availability_status': book_data['availability_status'],
                'total_copies': book_data['total_copies'],
                'available_copies': book_data['available_copies'],
            }
        )

@login_required
def book_list(request):
    # Retrieve all available books
    books = Book.objects.filter(available_copies__gte=0)  # Get books that are available
    book_availability = {}
    borrow_info={}
    create_books_in_db(fetch_books_data(0,10))
    for book in books:
        # Check if the user has borrowed this book
        is_borrowed = Borrowing.objects.filter(user=request.user, book=book).exists()
        book_availability[book.pk] = not is_borrowed  # True if available
        borrow_info[book.pk] = is_borrowed
        if book.available_copies == 0:
            book_availability[book.pk] = False
    return render(request, 'boipoka_app/book_list.html', {'books': books, 'book_availability': book_availability,'borrow_info':borrow_info})

@login_required
def book_details(request, pk):
    book = get_object_or_404(Book, pk=pk)
    subscription = get_user_subscription(request.user)  # Ensure this retrieves the correct subscription
    
    # Count how many books the user has currently borrowed and not returned
    borrowed_books_count = Borrowing.objects.filter(user=request.user, returned_at__isnull=True).count()
    book_due_info = None  
    # Check if the user has borrowed this specific book
    is_borrowed = Borrowing.objects.filter(user=request.user, book=book, returned_at__isnull=True).exists()
    if is_borrowed:
        borrowing_record = Borrowing.objects.filter(user=request.user, book=book, returned_at__isnull=True).first()
        if borrowing_record:
            book_due_info = borrowing_record.due_date

    # Get user's subscription information
    # subscription = Subscription.objects.filter(user=request.user).first()

    # Determine availability: A book is available if it is not borrowed by the user
    availability = not is_borrowed 

    context = {
        'book': book,
        'borrowed_books_count': borrowed_books_count,
        'subscription': subscription,
        'availability': availability,
        'is_borrowed': is_borrowed,
        'book_due_info': book_due_info
    }
    return render(request, 'boipoka_app/book_details.html', context)

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('boipoka_app:book_list')  # Redirect to book_list
        else:
            # Handle invalid login and pass 'error' to the template
            return render(request, 'boipoka_app/login.html', {'error': 'Invalid credentials'})
    
    return render(request, 'boipoka_app/login.html')

def logout_view(request):
    logout(request)
    return redirect('boipoka_app:index') 

@login_required
def create_subscription(request,pk):
    book = get_object_or_404(Book, pk=pk)
    existing_subscription = Subscription.objects.filter(user=request.user)
    
    if existing_subscription:
        messages.warning(request, "You already have an active subscription.")
        return redirect('boipoka_app:book_details', pk=existing_subscription.book.pk)   # Redirect to the book details

    if request.method == "POST":
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            subscription = form.save(commit=False)
            subscription.user = request.user
            subscription.subscription_start = timezone.now()
            subscription.subscription_end = subscription.subscription_start + timedelta(days=30)  # Set end date for 30 days
            subscription.save()
            # messages.success(request, "Your subscription has been created successfully.")
        return redirect('boipoka_app:book_details', pk=book.pk)  # Redirect to the specific book details
    else:
        form = SubscriptionForm()

    return render(request, 'boipoka_app/create_subscription.html', {'form': form})


@login_required
def borrow_book(request, pk):
    # Get the book to borrow
    book = get_object_or_404(Book, pk=pk)
    subscription = get_user_subscription(request.user)  # Ensure this retrieves the correct subscription
    
    borrowed_books_count = Borrowing.objects.filter(user=request.user, returned_at__isnull=True).count()
    print(borrowed_books_count)
    print(subscription.max_books)
    # Check subscription and borrowing limits
    if borrowed_books_count == subscription.max_books:
        # borrowed_books_count+=1
        messages.error(request, "Sorry, you have reached the limit of borrowed books for your subscription.")
        return redirect('boipoka_app:book_details', pk=book.pk)

    if book.available_copies <= 0:
        messages.error(request, "No copies of the book are available to borrow.")
        return redirect('boipoka_app:book_details', pk=book.pk)

    # Proceed to create the borrowing record
    Borrowing.objects.create(
        book=book,
        user=request.user,
        subscription=subscription,
    )
    book.available_copies -= 1
    book.save()

    messages.success(request, "You have successfully borrowed the book.")
    return redirect('boipoka_app:book_details', pk=book.pk)  # Redirect back to the book details page

@login_required
def change_subscription(request):
    # Get the subscription object for the logged-in user
    subscription = get_object_or_404(Subscription, user=request.user)

    if request.method == 'POST':
        # Get the new subscription type from the submitted form
        new_subscription_type = request.POST.get('subscription_type')

        # Validate that the submitted subscription type is valid
        if new_subscription_type in dict(Subscription.TIER_CHOICES):
            subscription.subscription_type = new_subscription_type
            
            # Update max_books based on the selected subscription type
            if new_subscription_type == 'Basic':
                subscription.max_books = 2
            elif new_subscription_type == 'Premium':
                subscription.max_books = 5
            elif new_subscription_type == 'VIP':
                subscription.max_books = 10

            # Save the updated subscription
            subscription.save()
            # messages.success(request, "Subscription updated successfully.")
            next_url=request.POST.get('next','boipoka_app:book_list')
            return redirect(next_url)
        else:
            messages.error(request, "Invalid subscription type.")
    
    # Pass the current subscription and available choices to the template
    context = {
        'subscription': subscription,
        'tier_choices': Subscription.TIER_CHOICES,
    }
    return render(request, 'boipoka_app/change_subscription.html', context)


@login_required
def return_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    borrowing=get_object_or_404(Borrowing,book=book,user=request.user,returned_at__isnull=True)
    if request.method == 'POST':
        borrowing.return_book()
        borrowing.delete()
        # messages.success(request, 'You have successfully returned this book.')
        redirect_to = request.POST.get('next', 'boipoka_app:book_list')
        return redirect(redirect_to)
    return render(request, 'boipoka_app/return_book.html', {'book': book,'borrowing':borrowing})
    
    
# Check if the user is an admin
def is_admin(user):
    """
    Check if the given user is an admin.

    Args:
    user (User): The user object to be checked.

    Returns:
    bool: True if the user is an admin, False otherwise.
    """
    return user.is_staff

# Admin: Add a new book
@user_passes_test(is_admin)
def add_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            # messages.success(request, 'Book added successfully.')
            return redirect('boipoka_app:book_list')  # Redirect to book list after successful upload
    else:
        form = BookForm()
    return render(request, 'boipoka_app/add_book.html', {'form': form})


# Admin: Edit an existing book
@user_passes_test(is_admin)
def edit_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            form.save()
            # messages.success(request, 'Book updated successfully.')
            return redirect('boipoka_app:book_list')  # Redirect to book list after successful edit
    else:
        form = BookForm(instance=book)
    return render(request, 'boipoka_app/edit_book.html', {'form': form, 'book': book})

# Admin: Delete a book
@user_passes_test(is_admin)
def delete_book(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        book.delete()
        # messages.success(request, 'Book deleted successfully.')
        return redirect('boipoka_app:book_list')  # Redirect to book list after successful deletion
    return render(request, 'boipoka_app/delete_book.html', {'book': book})


@user_passes_test(is_admin)
def users(request):
    users = User.objects.filter(is_superuser=False)
    return render(request, 'boipoka_app/users.html', {'users': users})

@user_passes_test(is_admin)
def user_details(request,pk):
    user = get_object_or_404(User, pk=pk)

    subscription = Subscription.objects.filter(user=user)
    borrowings = Borrowing.objects.filter(user=user)
    overdue_books = borrowings.filter(due_date__lt=timezone.now(), returned_at__isnull=True)
    # print(overdue_books)
    context={
        'user': user,
        'subscription': subscription,
        'borrowings': borrowings,
        'overdue_books': overdue_books,
    }

    return render(request, 'boipoka_app/user_details.html', {'context': context})

@user_passes_test(is_admin)
def update_due_date(request, pk):
    """Update the due date of a specific borrowing."""
    borrowing = get_object_or_404(Borrowing, pk=pk)
    user = borrowing.user
    
    if request.method == 'POST':
        new_due_date_str = request.POST.get('due_date')
        # print(new_due_date_str)  # Debug: print the due date string received

        # Parse the incoming date string in the format "2024-09-02T20:27"
        new_due_date = datetime.strptime(new_due_date_str, '%Y-%m-%dT%H:%M')
        
        # If the new due date is naive (without timezone info), make it timezone-aware
        if timezone.is_naive(new_due_date):
            new_due_date = timezone.make_aware(new_due_date, timezone.get_current_timezone())
        
        # Update the borrowing due date and save
        borrowing.due_date = new_due_date
        borrowing.save()
        
        messages.success(request, f'Due date for "{borrowing.book.title}" updated successfully.')
    
    return redirect('boipoka_app:user_details', pk=user.pk)
        # return redirect('boipoka_app:user_details', pk=borrowing.user.pk)

logger = logging.getLogger(__name__)

def send_email_threaded(subject: str, message: str, sender_email: str, toaddr: list, reply_to: list = None):
    """Send emails asynchronously in a separate thread with a reply-to address."""
    try:
        # Create an EmailMessage instance
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=sender_email,
            to=toaddr,
            reply_to=reply_to  # Adding reply_to field here
        )
        email.send(fail_silently=False)  # Send the email
        logger.info(f"Email sent to {toaddr} with subject: '{subject}'")
    except SMTPException as e:
        logger.error(f"Failed to send email: {str(e)}")
    except Exception as e:
        logger.error(f"An error occurred while sending email: {str(e)}")
        raise Exception("Something went wrong with sending email.")

@user_passes_test(is_admin)
def send_reminder(request, pk):
    """Send a reminder to a specific user about their overdue book asynchronously."""
    user = get_object_or_404(User, pk=pk)
    borrowings = Borrowing.objects.filter(user=user, returned_at__isnull=True, due_date__lt=timezone.now())
    subscription = get_object_or_404(Subscription, user=user)
            
    if not borrowings.exists():
        messages.warning(request, f'No overdue books found for user ID {pk}.')
        return redirect('boipoka_app:user_details')
    
    penalty_rate = 0
    if subscription:
        if subscription.subscription_type == 'Basic':
            penalty_rate = 2
        elif subscription.subscription_type == 'Premium':
            penalty_rate = 5
        elif subscription.subscription_type == 'VIP':
            penalty_rate = 10
    for borrowing in borrowings:
        # Prepare the email
        due_date = borrowing.due_date
        time_now = timezone.now()
        difference = (time_now - due_date).days+10  # Calculate the difference in days
        penalty = penalty_rate * difference if difference > 0 else 0  # Apply penalty only if overdue
        
        subject = f'Reminder: Overdue Book - {borrowing.book.title}'
        message = (
            f'Dear {borrowing.user.username},\n\n'
            f'This is a reminder that the book "{borrowing.book.title}" is overdue. '
            f'Please return it as soon as possible.\n\n'
            f'Penalty for overdue: {penalty} tk (based on your {subscription.subscription_type} subscription).\n\n'
        )
        recipient_list = [borrowing.user.email]
        reply_to_address = ['boipoka_admin@boipoka.com']
        # Create a separate thread to send the email
        separate_thread = threading.Thread(
            target=send_email_threaded,
            args=(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list,reply_to_address)
        )
        separate_thread.start()

    messages.success(request, f'Reminder(s) sent to {", ".join([b.user.username for b in borrowings])} for their overdue books.')
    return redirect('boipoka_app:user_details', pk=pk)
@user_passes_test(is_admin)
def edit_user(request, pk):
    user = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        user.username = request.POST.get('username', user.username)
        user.email = request.POST.get('email', user.email)
        user.save()
        messages.success(request, f'User {user.username} updated successfully.')
        return redirect('boipoka_app:user_details',pk=pk)

    return render(request, 'boipoka_app/edit_user.html', {'user': user})

@user_passes_test(is_admin)
def delete_user(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.delete()
    messages.success(request, f'User {user.username} deleted successfully.')
    return redirect('boipoka_app:users')
@user_passes_test(is_admin)
def delete_subscription(request, pk):
    user = get_object_or_404(User, pk=pk)
    subscription = get_object_or_404(Subscription, user=user)
    # Get all borrowed books for the user
    borrowed_books = Borrowing.objects.filter(user=user,subscription=subscription)
    for borrowed in borrowed_books:
        # Retrieve the book
        book = get_object_or_404(Book, pk=borrowed.book.pk)
        # Increment the available copies
        book.available_copies += 1
        # Save the updated book
        book.save()

    # Delete the subscription
    subscription.delete()

    
    return redirect('boipoka_app:user_details',pk=user.pk)

@user_passes_test(is_admin)
def manage_subscriptions_starting(request,pk):
    subscription = get_object_or_404(Subscription, pk=pk)
    user=subscription.user
    if request.method == 'POST':
        new_subscription_startdate_str = request.POST.get('start-date')
        new_subscription_startdate = datetime.strptime(new_subscription_startdate_str, '%Y-%m-%dT%H:%M')  # Adjust the format to match your input format
        # If the due_date is naive (without timezone info), mak it timezone-aware
        if timezone.is_naive(new_subscription_startdate):
            new_subscription_startdate = timezone.make_aware(new_subscription_startdate, timezone.get_current_timezone())
        subscription.subscription_start = new_subscription_startdate
        subscription.save()
    return redirect('boipoka_app:user_details', pk=user.pk)
@user_passes_test(is_admin)
def manage_subscriptions_ending(request,pk):
    subscription = get_object_or_404(Subscription, pk=pk)
    user=subscription.user
    if request.method == 'POST':
        new_subscription_enddate_str = request.POST.get('expire-date')
        new_subscription_enddate = datetime.strptime(new_subscription_enddate_str, '%Y-%m-%dT%H:%M')  # Adjust the format to match your input format
        # If the due_date is naive (without timezone info), mak it timezone-aware
        if timezone.is_naive( new_subscription_enddate):
            new_subscription_enddate = timezone.make_aware(new_subscription_enddate, timezone.get_current_timezone())
        subscription.subscription_end =  new_subscription_enddate
        subscription.save()

    return redirect('boipoka_app:user_details', pk=user.pk)

@login_required
def renew_subscription(request):
    subscription = get_object_or_404(Subscription, user=request.user)

    if request.method == 'POST':
        # Extend the subscription period by 30 days
        subscription.subscription_end += timedelta(days=30)
        subscription.save()
        request.user = get_user_model().objects.get(pk=request.user.pk)
        # print(subscription.subscription_end)
        
        # messages.success(request, "Your subscription has been renewed successfully.")
        return redirect('boipoka_app:book_list')

    return render(request, 'boipoka_app/renew_subscription.html', {'subscription': subscription})


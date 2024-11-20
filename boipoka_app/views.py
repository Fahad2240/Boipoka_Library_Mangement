from datetime import datetime  # Import datetime for date manipulations
from django.core.mail import EmailMessage  # Import EmailMessage for sending emails
import logging  # Import logging for logging errors and information
from smtplib import SMTPException  # Import SMTPException to handle email sending errors
import threading  # Import threading for sending emails in separate threads
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render, redirect  # Import necessary functions for view handling
from django.contrib.auth import login, authenticate, logout  # Import authentication functions
from django.urls import reverse
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
import pytz

def is_admin(user):
    """
    Check if the given user is an admin.

    Args:
    user (User): The user object to be checked.

    Returns:
    bool: True if the user is an admin, False otherwise.
    """
    return user.is_staff
def is_not_admin(user):
    """
    Check if the given user is not an admin.

    Args:
    user (User): The user object to be checked.

    Returns:
    bool: False if the user is an admin, True otherwise.
    """
    return not user.is_staff

@login_required
def notify_user(request):
    """
    Handle notifications for a regular user.
    Only accessible if the user is logged in.
    """
    # Fetch all notifications where the subscriber is the current logged-in user
    notifications = Notifications.objects.filter(subscriber=request.user)
    
    # Dictionary to track if notifications are clickable or not
    unclickable = {}
    for notify in notifications:
        # If the notification is read, set its clickable status to False; otherwise, set to True
        if notify.is_read == True:
            unclickable[notify.pk] = False
        else:
            unclickable[notify.pk] = True
    
    # Render the notification template and pass notifications and clickable status used as context
    return render(request, 'boipoka_app/notification.html', {'notifications': notifications, 'unclickable': unclickable})

def index(request):
    return render(request,'boipoka_app/index.html')

@login_required
def makeunread(request, pk):
    # Retrieve the notification object by its primary key (pk) for the logged-in user, or return a 404 error if not found
    notification = get_object_or_404(Notifications, pk=pk)
    
    if notification.subscriber != request.user:
        return HttpResponseForbidden("You are not allowed to access this notification.")
    
    # Mark the notification as read
    notification.is_read = True
    notification.save()
    
    # Redirect the user back to the notifications page
    return redirect('boipoka_app:notifications')

@login_required
def deletenotifcation(request, pk):
    # Retrieve the notification object by its primary key (pk) for the logged-in user, or return a 404 error if not found
    notification = get_object_or_404(Notifications, pk=pk)
    
    # Ensure the notification belongs to the logged-in user
    if notification.subscriber != request.user:
        return HttpResponseForbidden("You are not allowed to access this notification.")
    # Delete the notification from the database
    notification.delete()
    
    # Redirect the user back to the notifications page
    return redirect('boipoka_app:notifications')

def register(request):
    
    # If the request method is POST, process the registration form
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # Save the new user to the database
            login(request, user)  # Log the new user in automatically
            return redirect('/login/')  # Redirect to the login page or another page after registration
        else:
            # If the form is invalid, render the same page with the form errors
            return render(request, 'boipoka_app/register.html', {'form': form})
    else:
        # If the request method is GET, display an empty registration form
        form = CustomUserCreationForm()
    
    # Render the registration template with the form context
    return render(request, 'boipoka_app/register.html', {'form': form})


def fetch_books_data(start_index=0, max_results=10):
    """
    Fetch books data from the Google Books API.

    Parameters:
        start_index (int): The index from which to start fetching books (default is 0).
        max_results (int): The maximum number of books to fetch (default is 10).
    
    Returns:
        list: A list of dictionaries containing book details like title, author, 
            description, image, availability status, total copies, and available copies.
    """
    api_key = settings.GOOGLE_BOOKS_API_KEY
    url = f"https://www.googleapis.com/books/v1/volumes?q=subject:fiction&startIndex={start_index}&maxResults={max_results}&key={api_key}"
    
    # Send a GET request to the Google Books API
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        books = []
        
        if "items" in data:
            for item in data["items"]:
                # Extract volume information and image links from each item
                volume_info = item.get("volumeInfo", {})
                image_url = volume_info.get("imageLinks", {}).get("thumbnail", "")
                image_content = None

                # Fetch image content if available
                if image_url:
                    img_response = requests.get(image_url)
                    if img_response.status_code == 200:
                        # Convert the image response content into a ContentFile
                        image_content = ContentFile(
                            img_response.content, 
                            name=urlparse(image_url).path.split('/')[-1]
                        )
                
                # Append the book's details as a dictionary to the books list
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
    
    # Return an empty list if the API call fails or no books are found
    return []

def create_books_in_db(book_list):
    """
    Create or update Book instances in the database based on the given book list.

    Parameters:
        book_list (list): A list of dictionaries, where each dictionary contains details
                        about a book such as title, author, description, image, 
                        availability status, total copies, and available copies.

    For each book in the list:
        - The function checks if a Book instance with the same title already exists in the database.
        - If it exists, it does nothing (leaves the existing record unchanged).
        - If it does not exist, it creates a new Book instance using the provided details.
    """
    for book_data in book_list:
        # Create or update the Book instance in the database
        Book.objects.get_or_create(
            title=book_data['title'],  # Check for an existing book with the same title
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
    """
    View to display the list of books available for the user.

    - Retrieves the user's subscription information.
    - If the user is not an admin and does not have an active subscription, redirects them to the subscription page.
    - Fetches available books and updates their status based on borrowing and damage history.
    - Suspends the user's subscription if there are unpaid fines for damaged or lost books.

    Parameters:
        request (HttpRequest): The HTTP request object containing metadata about the request.

    Returns:
        HttpResponse: The rendered HTML page displaying the list of books along with their statuses and user-related information.
    """
    # Retrieve the user's subscription
    subscription = Subscription.objects.filter(user=request.user).first()
    
    # If the user is not an admin and does not have a subscription, redirect them to the subscription page
    if is_not_admin(request.user):
        if subscription is None:
            return redirect('boipoka_app:subscription')

    # Get all available books
    books = Book.objects.filter(available_copies__gte=0)
    
    # Dictionaries to track book statuses and other related information
    book_availability = {}
    borrow_info = {}
    isreported = {}
    paidlist = {}
    borrowedornot = {}
    book_due_near = {}

    # Create or update books in the database from an external source
    create_books_in_db(fetch_books_data(0, 10))

    for book in books:
        # Fetch the specific borrowed book record which is reported as damaged/lost by the user
        reported_issue = Borrowing.objects.filter(user=request.user, book=book, is_damagedorlost=True).first()
        
        # Fetch the history of damaged/lost instances for this book and user.
        # This includes past borrowing records that may have been deleted but are kept in this history.
        damagedhistory = DamagedorLostHistory.objects.filter(user=request.user, book=book).first()
        
        # If the book has a reported issue but no existing damaged history, create a new history entry
        if reported_issue is not None:
            if damagedhistory is None:
                DamagedorLostHistory.objects.create(
                    book=reported_issue.book,
                    user=request.user,
                    fine_paid=reported_issue.fine_paid,
                    fine_paid_approved=reported_issue.fine_paid_approved,
                    fine_paid_at=reported_issue.fine_paid_at
                )
            # If there's an existing damaged history, update it if the fine is approved
            if reported_issue.fine_paid_approved and damagedhistory is not None:
                damagedhistory.fine_paid_approved = reported_issue.fine_paid_approved
                damagedhistory.isdeleted = True  # Mark the history as deleted after fine approval
                damagedhistory.save()

                # Print statements for debugging
                print(damagedhistory.book.title)
                print(damagedhistory.fine_paid_approved)
                print(damagedhistory.isdeleted)
                
                # Delete the reported issue after updating the history
                reported_issue.delete()
                if reported_issue is not None:
                    print('hey')

        # If the book has been marked as damaged/lost for more than a day and the fine is not paid
        if reported_issue:
            print(timezone.now() > reported_issue.damagedlostat + timedelta(days=1))
            if timezone.now() > reported_issue.damagedlostat + timedelta(days=1):
                if not reported_issue.fine_paid_at or reported_issue.fine_paid_at >= reported_issue.damagedlostat + timedelta(days=1):
                    if subscription is not None:
                        # Suspend the subscription due to unpaid fines
                        subscription.is_active = False
                        subscription.save()
                        subject = f'Subscription Suspended: Your Subscription Has been Suspended'
                        message = (
                            f'Dear {subscription.user.username},\n\n'
                            f'Your subscription plan {subscription.subscription_type} has been temporarily suspended due to unpaid fines.\n'
                            f'To reactivate your subscription, please pay the unpaid fines as soon as possible.\n\n'
                            f'Thank you very much.\n\n'
                            f'Best regards,\n\nBoipoka Admin\n\n'
                        )
                        recipient = subscription.user.email
                        reply_to_address = ['boipoka_admin@boipoka.com']
                        
                        # Send email notification in a separate thread
                        separate_thread = threading.Thread(
                            target=send_email_threaded_single,
                            args=(subject, message, settings.DEFAULT_FROM_EMAIL, recipient, reply_to_address)
                        )
                        separate_thread.start()

                        # Create an in-app notification
                        message = f'Your subscription plan {subscription.subscription_type} has been temporarily suspended due to unpaid fine.'
                        Notifications.objects.create(
                            subscriber=request.user,
                            message=message,
                            timestamp=timezone.now(),
                        )
                        print(subscription.is_active)
                else:
                    if subscription is not None:
                        # Reactivate the subscription if the fine is paid
                        subscription.is_active = True
                        subscription.save()
            else:
                if subscription is not None:
                    # Ensure the subscription remains active if within the time limit
                    subscription.is_active = True
                    subscription.save()

            if reported_issue.fine_paid:
                paidlist[book.pk] = True
            else:
                paidlist[book.pk] = False

        # Check if the user has borrowed this book
        is_borrowed = Borrowing.objects.filter(user=request.user, returned_at__isnull=True, book=book).exists()
        if is_borrowed:
            borrowed = Borrowing.objects.filter(user=request.user, book=book).first()
            temp = borrowed.due_date < (timezone.now() + timedelta(days=1))
            borrowedornot[book.pk] = True
            book_due_near[book.pk] = temp
            isreported[book.pk] = borrowed.is_damagedorlost
        else:
            book_due_near[book.pk] = False
            borrowedornot[book.pk] = False
            isreported[book.pk] = False  # Default value if the book is not borrowed

        # Determine if the book is available
        book_availability[book.pk] = not is_borrowed  # True if available
        borrow_info[book.pk] = is_borrowed

        # Update availability if no copies are left
        if book.available_copies == 0:
            book_availability[book.pk] = False

    return render(request, 'boipoka_app/book_list.html', {
        'books': books,
        'book_availability': book_availability,
        'borrow_info': borrow_info,
        'isreported': isreported,
        'paidlist': paidlist,
        'borrowedornot': borrowedornot,
        'book_due_near': book_due_near
    })


@login_required
def report_lost_or_damaged(request, pk):
    """
    Handle the reporting of a lost or damaged book by a user.
    This function updates the borrowing instance to mark the book 
    as lost or damaged, applies a fine, and handles subscription 
    suspensions if necessary.
    """
    
    # Fetch the borrowing instance for the specified book
    borrowing = Borrowing.objects.filter(user=request.user, book__pk=pk).first()
    # Retrieve the user's subscription status
    subscription = get_user_subscription(request.user)
    
    # Handle the case where no borrowing record is found
    if not borrowing:
        messages.error(request, "No borrowing record found for this book.")
        return redirect('boipoka_app:book_list')
    
    # Mark the book as damaged or lost
    borrowing.is_damagedorlost = True
    borrowing.save()  # Save the changes to the borrowing instance
    
    # Create a notification message for the user about the reported book
    message = f'The book "{borrowing.book.title}" has been reported as lost/damaged. A fine of 500 BDT has been applied.'
    Notifications.objects.create(
        subscriber=request.user,
        message=message,
        timestamp=timezone.now(),
    )
    
    # Check the number of lost/damaged reports for the user
    incident_count = Borrowing.objects.filter(user=request.user, is_damagedorlost=True).count() 
    
    # Suspend subscription if the number of incidents is 3 or more
    if incident_count >= 3:
        if subscription:
            # Suspend the user's subscription
            subscription.is_active = False  # Update subscription status
            subscription.save()  # Save the updated subscription status
            
            # Prepare an email notification for the user regarding the suspension
            subject = f'Subscription Suspended: Your Subscription Has been Suspended'
            message = (
                f'Dear {subscription.user.username},\n\n'
                f'Your subscription plan {subscription.subscription_type} has been suspended due to multiple lost/damaged reports.\n'
                f'Now, you cannot access the login session. To reactivate your subscription, please contact the Boipoka admin as soon as possible.\n\n'
                f'Thank you very much.\n\n'
                f'\n\n Best regards, \n\n Boipoka Admin\n\n'
            )
            recipient = subscription.user.email
            reply_to_address = ['boipoka_admin@boipoka.com']
            
            # Send an email notification in a separate thread to avoid blocking the request
            separate_thread = threading.Thread(
                target=send_email_threaded_single,
                args=(subject, message, settings.DEFAULT_FROM_EMAIL, recipient, reply_to_address)
            )
            separate_thread.start()
            
            # Create a notification for the user about the subscription suspension
            message = f'Your subscription has been suspended due to multiple lost/damaged reports. Please contact the Boipoka admin as soon as possible.'
            Notifications.objects.create(
                subscriber=request.user,
                message=message,
                timestamp=timezone.now(),
            )
            
            # Redirect the user to the login page if subscription is suspended
            return redirect('boipoka_app:login')

    # Display a success message to the user and redirect back to the book list
    messages.success(request, f"The book '{borrowing.book.title}' has been reported as lost/damaged. A fine of 500 BDT has been applied.")
    return redirect('boipoka_app:book_list')

@login_required
def manage_fines(request, pk):
    """
    Manages the fine payment process for a user-reported damaged or lost book.
    
    - Fetches the specific borrowing record for the currently logged-in user where the book has been reported as damaged/lost.
    - Marks the fine as paid for the reported borrowing instance.
    - Sends a notification to the user confirming the receipt of the fine payment and informing them to wait for admin approval.
    - Redirects the user back to the book list page.
    """
    # Fetch the borrowing instance where the book is reported as damaged/lost for the logged-in user
    reported = get_object_or_404(Borrowing, user=request.user, is_damagedorlost=True, book__pk=pk)
    
    # Mark the fine as paid
    reported.fine_paid = True
    reported.save()
    
    # Send a notification to the user about the fine payment
    message = f'We have successfully received the fine for the damage/loss of the book "{reported.book.title}". Please wait for the approval.'
    Notifications.objects.create(
        subscriber=request.user,
        message=message,
        timestamp=timezone.now(),
    )
    
    # Redirect the user back to the book list page
    return redirect('boipoka_app:book_list')


@user_passes_test(is_admin)
def manage_fineapprove(request, pk):
    """
    Allows an admin to approve the fine payment for a reported damaged or lost book.
    
    - Fetches the specific borrowing record based on the provided primary key (pk).
    - Marks the fine as approved by the admin.
    - Sends a notification to the user indicating that the fine payment has been approved.
    - Redirects the admin to the user details page after approval.
    """
    # Fetch the borrowing instance by primary key (pk)
    borrowing = get_object_or_404(Borrowing, pk=pk)
    user = borrowing.user  # Get the user associated with the borrowing record
    
    # Process the approval when the form is submitted via POST
    if request.method == 'POST':
        # Mark the fine as approved by the admin
        borrowing.fine_paid_approved = True
        borrowing.save()
        
        # Send a notification to the user about the fine approval
        message = f'Your payment for the damage/loss of the book "{borrowing.book.title}" has been approved.'
        Notifications.objects.create(
            subscriber=user,
            message=message,
            timestamp=timezone.now(),
        )
    
    # Redirect to the user details page for the admin view
    return redirect('boipoka_app:user_details', pk=user.pk)
@login_required
def book_details(request, pk):
    """
    Displays the details of a specific book based on its primary key (pk). 
    
    - Fetches the book details and retrieves the user's subscription information.
    - Counts the number of books the user has currently borrowed and not returned.
    - Checks if the user has borrowed this specific book and if its due date is near.
    - Flags whether the user has reached their borrowing limit based on their subscription.
    - Prepares the context data and renders the book details template.
    """
    
    # Fetch the book record based on the provided primary key (pk)
    book = get_object_or_404(Book, pk=pk)
    
    # Retrieve the user's current subscription information
    subscription = get_user_subscription(request.user)  # Ensure this retrieves the correct subscription
    
    # Count how many books the user has currently borrowed and not returned
    borrowed_books_count = Borrowing.objects.filter(user=request.user, returned_at__isnull=True).count()
    
    # Placeholder for storing information about the book's due date if it is borrowed
    book_due_info = None  
    
    # Check if the user has reissued the current book
    check = Borrowing.objects.filter(user=request.user, book=book, reissue_state=True).exists()
    
    # Flag to indicate if the user has reached the maximum borrowing limit
    flag = 0
    if borrowed_books_count is not None and subscription is not None:
        if borrowed_books_count >= subscription.max_books:
            flag = 1  # Set the flag if the user has reached their borrowing limit
    
    # Check if the user has currently borrowed this specific book and not yet returned it
    is_borrowed = Borrowing.objects.filter(user=request.user, book=book, returned_at__isnull=True).exists()
    
    # Flag to indicate if the due date for the borrowed book is near
    book_due_near = False
    if is_borrowed:
        # Retrieve the borrowing record for this specific book if it is borrowed
        borrowing_record = Borrowing.objects.filter(user=request.user, book=book, returned_at__isnull=True).first()
        if borrowing_record:
            # Get the due date for the borrowed book
            book_due_info = borrowing_record.due_date  # Consider formatting if needed
            
            # Check if the due date is within the next day (due date is near)
            book_due_near = borrowing_record.due_date < (timezone.now() + timedelta(days=1))
    
    # Determine availability: A book is available if it is not currently borrowed by the user
    availability = not is_borrowed 

    # Prepare context data to pass to the template
    context = {
        'book': book,
        'borrowed_books_count': borrowed_books_count,
        'subscription': subscription,
        'availability': availability,
        'is_borrowed': is_borrowed,
        'book_due_info': book_due_info,
        'book_due_near': book_due_near,
        'flag': flag,  # Indicates if borrowing limit is reached
        'check': check,  # Indicates if the book has been reissued by the user
    }
    
    # Render the 'book_details' template with the prepared context data
    return render(request, 'boipoka_app/book_details.html', context)

@login_required
def new_subscription_creation(request):
    """
    This view function handles the creation of a new subscription for the user.
    It responds to both POST and GET requests:
    - For POST: It processes the submitted form data and creates a subscription if valid.
    - For GET: It renders the subscription form for user input.
    """

    if request.method == "POST":
        # If the request is a POST, the form is initialized with the posted data.
        form = SubscriptionForm(request.POST)
        
        """
        Check if the form data is valid:
        - If valid, proceed to check if the user already has an active subscription.
        - If an existing subscription is found, redirect to the book list page.
        - Otherwise, create a new subscription and set relevant details.
        """
        if form.is_valid():
            existing_subscription = Subscription.objects.filter(user=request.user).first()
            if existing_subscription:
                # If the user already has a subscription, redirect to prevent duplicate subscriptions.
                return redirect('boipoka_app:book_list')
            
            # Prepare the subscription without saving to assign additional details.
            subscription = form.save(commit=False)
            subscription.user = request.user  # Associate the subscription with the current user.
            subscription.subscription_start = timezone.now()  # Set the current time as the start time.
            """
            Set the subscription end date:
            - Adds 30 days from the start date as the duration of the subscription.
            """
            subscription.subscription_end = subscription.subscription_start + timedelta(days=30)
            subscription.save()  # Save the subscription details in the database.
            
            # Retrieve the subscription type to include it in the notification message.
            subtype = subscription.subscription_type
            
            """
            Timezone and date formatting:
            - Convert the end date to Dhaka timezone for accurate user display.
            - Format the end date as a readable string (e.g., "Jan. 01, 2025, 01:00 PM").
            """
            dhaka_timezone = pytz.timezone('Asia/Dhaka')
            end_date = subscription.subscription_end.astimezone(dhaka_timezone)
            end_date = end_date.strftime('%b. %d, %Y, %I:%M %p')
            
            """
            Create and send a notification to the user:
            - The notification informs the user of their subscription start and end details.
            - The timestamp records when the notification is created.
            """
            message = f'Your subscription of {subtype} plan has been created susccessfully \n.It will end on {end_date}.'
            Notifications.objects.create(
                subscriber=request.user,
                message=message,
                timestamp=timezone.now(),
            )
        
        # After processing the subscription, redirect the user to the book list.
        return redirect('boipoka_app:book_list')
    else:
        # If the request is not POST (e.g., GET), display an empty subscription form.
        form = SubscriptionForm()
    
    """
    Render the subscription creation template:
    - Pass the form context to display the subscription form for user input.
    """
    return render(request, 'boipoka_app/new_subscription_creation.html', {'form': form})
@login_required
def subscription(request):
    """
    This view renders the subscription page for the user.
    - The @login_required decorator ensures that only authenticated users can access this page.
    - It returns the rendered subscription template.
    """
    return render(request, 'boipoka_app/subscription.html')


def login_view(request):
    """
    This view handles user login.
    - If the request is POST, it processes login credentials (username and password) and authenticates the user.
    - If authentication is successful, it checks for subscription status and redirects appropriately.
    - If the login is invalid, it renders the login page with an error message.
    """

    if request.method == 'POST':
        # Fetch username and password from the POST request.
        username = request.POST['username']
        password = request.POST['password']
        # Attempt to authenticate the user.
        user = authenticate(request, username=username, password=password)
        subscription = Subscription.objects.filter(user=user).first()

        """
        If the user has a subscription:
        - Check if the subscription is inactive. If it is, verify if the user has 3 or more damaged/lost incidents.
        - If true, display a warning message and redirect back to the login page to prevent access.
        """
        if subscription is not None:
            if subscription.is_active == False:
                borrowing = Borrowing.objects.filter(user=user, is_damagedorlost=True).count()
                if borrowing >= 3:
                    messages.warning(request, "Your account has been suspended. Please contact the Admin.")
                    return redirect('boipoka_app:login')
        
        """
        If the user is successfully authenticated:
        - Log the user in and check if they have a subscription or are an admin.
        - Redirect to the book list if they do, otherwise redirect them to the subscription page.
        """
        if user is not None:
            login(request, user)
            print(is_admin(user))
            if subscription or is_admin(user):
                return redirect('boipoka_app:book_list')  # Redirect to the book list
            else:
                return redirect('boipoka_app:subscription')
        else:
            # Render the login page with an error if credentials are invalid.
            return render(request, 'boipoka_app/login.html', {'error': 'Invalid credentials'})
    
    # If the request method is GET, render the login page.
    return render(request, 'boipoka_app/login.html')


def logout_view(request):
    """
    This view handles user logout.
    - Logs out the user and redirects them to the index page.
    - No login is required to access this view.
    """
    logout(request)
    return redirect('boipoka_app:index')


@login_required
def create_subscription(request, pk):
    """
    This view allows a user to create a subscription for a specific book.
    - It checks if the user already has an existing subscription before proceeding.
    - If a POST request is made with valid form data, it saves the new subscription and redirects to the book details page.
    - If a GET request is made, it renders the subscription creation form.
    """

    # Fetch the book associated with the given primary key (pk).
    book = get_object_or_404(Book, pk=pk)
    existing_subscription = Subscription.objects.filter(user=request.user)

    """
    If the user already has a subscription:
    - Redirect to the details page of the book associated with their existing subscription.
    """
    if existing_subscription:
        # Redirect to the book details if the user already has an active subscription.
        return redirect('boipoka_app:book_details', pk=existing_subscription.book.pk)

    if request.method == "POST":
        # If the request is POST, initialize the form with the submitted data.
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            # Prepare the subscription object without saving it yet.
            subscription = form.save(commit=False)
            subscription.user = request.user  # Associate the subscription with the logged-in user.
            subscription.subscription_start = timezone.now()  # Set the current time as the start time.
            """
            Set the subscription duration:
            - The subscription end date is set to 30 days from the start date.
            """
            subscription.subscription_end = subscription.subscription_start + timedelta(days=30)
            subscription.save()  # Save the new subscription in the database.
        
        # Redirect to the book details page for the selected book after subscription creation.
        return redirect('boipoka_app:book_details', pk=book.pk)
    else:
        # If the request is not POST (e.g., GET), initialize an empty subscription form.
        form = SubscriptionForm()

    """
    Render the subscription creation template:
    - Pass the form context to display the form for user input.
    """
    return render(request, 'boipoka_app/create_subscription.html', {'form': form})



@login_required
def borrow_book(request, pk):
    # Get the book to borrow
    book = get_object_or_404(Book, pk=pk)
    subscription = get_user_subscription(request.user)  # Ensure this retrieves the correct subscription

    # Count the number of books currently borrowed by the user and not returned
    borrowed_books_count = Borrowing.objects.filter(user=request.user, returned_at__isnull=True).count()
    
    # Check if the user has reached the maximum limit of borrowed books allowed by their subscription
    if borrowed_books_count == subscription.max_books:
        """
        If the user has already borrowed the maximum number of books allowed, 
        a notification is created informing them that they have reached their limit. 
        The function then redirects to the book details page without proceeding further.
        """
        message = f'Sorry, you have reached the limit of borrowed books for your subscription'
        Notifications.objects.create(
            subscriber=request.user,
            message=message,
            timestamp=timezone.now(),
        )
        return redirect('boipoka_app:book_details', pk=book.pk)
    
    # Check if there are any available copies of the book
    if book.available_copies <= 0:
        # Display an error message if no copies of the book are available for borrowing
        messages.error(request, "No copies of the book are available to borrow.")
        return redirect('boipoka_app:book_details', pk=book.pk)

    """
    If the user has not reached their limit and the book is available,
    create a new borrowing record for the user.
    """
    Borrowing.objects.create(
        book=book,
        user=request.user,
        subscription=subscription,
    )
    
    # Reduce the available copies count for the book and save the update
    book.available_copies -= 1
    book.save()

    # Retrieve borrowing and due date information for the specific borrowing record
    borrow_time = Borrowing.objects.filter(book=book, user=request.user, subscription=subscription).first().borrowed_on
    due_time = Borrowing.objects.filter(book=book, user=request.user, subscription=subscription).first().due_date

    # Convert the times to the Dhaka timezone for consistency
    dhaka_timezone = pytz.timezone('Asia/Dhaka')
    due_time = due_time.astimezone(dhaka_timezone)
    due_time = due_time.strftime("%b. %d, %Y, %I:%M %p")  # Format the due date
    borrow_time = borrow_time.astimezone(dhaka_timezone)
    borrow_time = borrow_time.strftime("%b. %d, %Y, %I:%M %p")  # Format the borrow time
    
    # Get the current time in Dhaka timezone and format it
    current_time_in_dhaka = timezone.now()
    current_time_in_dhaka = current_time_in_dhaka.astimezone(dhaka_timezone)
    formatted_time = current_time_in_dhaka.strftime("%b. %d, %Y, %I:%M %p")

    """
    Send a notification to the user indicating that they have successfully borrowed the book.
    The notification includes the borrow time and the due date. 
    It also warns the user about the fine if the book is not returned on time.
    """
    message = f'You have successfully borrowed the book {book.title} at {borrow_time}\n.Your have to return this book within {due_time}\n.Otherwise, you will be fined .'
    Notifications.objects.create(
        subscriber=request.user,
        message=message,
        timestamp=formatted_time,
    )

    # Redirect back to the book details page after borrowing
    return redirect('boipoka_app:book_details', pk=book.pk)


@user_passes_test(is_not_admin)
def reading_history(request):
    """
    View function to display the user's reading history.
    
    This function retrieves the borrowing history of the logged-in user and provides
    functionalities for searching and filtering the history based on book titles 
    and borrowing dates.
    """
    history = Borrowing.objects.filter(user=request.user).order_by('-borrowed_on')

    # Handling search functionality
    search_query = request.GET.get('search', '')  # Get the search query from the request
    start_date = request.GET.get('start_date', '')  # Get the start date from the request
    end_date = request.GET.get('end_date', '')  # Get the end date from the request

    # Process start_date to make it timezone-aware if provided
    if start_date: 
        start_date = datetime.strptime(start_date, '%Y-%m-%dT%H:%M')
        if timezone.is_naive(start_date):
            start_date = timezone.make_aware(start_date, timezone.get_current_timezone())
    
    # Process end_date to make it timezone-aware if provided
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%dT%H:%M')
        if timezone.is_naive(end_date):
            end_date = timezone.make_aware(end_date, timezone.get_current_timezone())
    
    # Filter the history based on the search query if provided
    if search_query:
        history = history.filter(book__title__icontains=search_query)

    # Filter the history based on the date range if both start_date and end_date are provided
    if start_date and end_date:
        history = history.filter(borrowed_on__range=[start_date, end_date])
    
    # Create a dictionary to track which entries are marked as unread
    incomplete = {}
    for entry in history:
        if entry.marked_as_unread:
            incomplete[entry.pk] = 1  # Mark entry as unread
        else:
            incomplete[entry.pk] = 0  # Mark entry as read
    
    # Render the reading history template with the context
    return render(request, 'boipoka_app/readlist.html', {
        'history': history,
        'search_query': search_query,
        'start_date': start_date,
        'end_date': end_date,
        'incomplete': incomplete
    })
    
@user_passes_test(is_not_admin)
def mark_unread(request, pk):
    """
    View function to mark a specific book entry as unread.
    
    This function retrieves the borrowing entry by its primary key (pk)
    and marks it as unread, allowing users to keep track of books they need 
    to revisit.
    """
    entry = get_object_or_404(Borrowing, pk=pk, user=request.user)  # Get the borrowing entry
    print(entry)  # Debugging output
    entry.readcheck()  # Mark as unread  
    print(entry.marked_as_unread)  # Debugging output
    # messages.success(request, "Book marked as unread successfully.")
    return redirect('boipoka_app:reading_history')  # Redirect back to the reading history

@login_required
def change_subscription(request):
    """
    View function to change the subscription of the logged-in user.

    This function allows users to change their subscription type based on the 
    predefined subscription tiers. It checks for the number of currently borrowed 
    books and ensures that users meet the requirements for downgrading or changing 
    their subscription.
    """
    # Get the subscription object for the logged-in user
    subscription = get_object_or_404(Subscription, user=request.user)
    borrowed_books_count = Borrowing.objects.filter(user=request.user, returned_at__isnull=True).count()
    print(borrowed_books_count)  # Debugging output for borrowed books count

    if request.method == 'POST':
        # Get the new subscription type from the submitted form
        new_subscription_type = request.POST.get('subscription_type')

        # Validate that the submitted subscription type is valid
        if new_subscription_type in dict(Subscription.TIER_CHOICES):
            
            # Update max_books based on the selected subscription type
            if new_subscription_type == 'Basic':
                new_max_books = 2
            elif new_subscription_type == 'Premium':
                new_max_books = 5
            elif new_subscription_type == 'VIP':
                new_max_books = 10
            
            oldsubtype = subscription.subscription_type
            newtype = new_subscription_type
            info = ''
            if new_max_books < subscription.max_books:
                info = 'downgraded'
            elif new_max_books > subscription.max_books:
                info = 'upgraded'
            
            # Check if the user has too many borrowed books to downgrade
            if new_max_books <= borrowed_books_count:
                books_to_return = (borrowed_books_count - new_max_books) + 1
                messages.error(
                    request,
                    f"You need to return {books_to_return} book(s) to downgrade to the {new_subscription_type} plan."
                )
                
                message = f'You cannot downgrade your subscription from {oldsubtype} to {newtype} until you return at least {books_to_return} books.'
                current_time_in_dhaka = timezone.now()
                dhaka_timezone = pytz.timezone('Asia/Dhaka')
                current_time_in_dhaka = current_time_in_dhaka.astimezone(dhaka_timezone)
                formatted_time = current_time_in_dhaka.strftime("%b. %d, %Y, %I:%M %p")
                Notifications.objects.create(
                    subscriber=request.user,
                    message=message,
                    timestamp=formatted_time,
                )
                next_url = request.POST.get('next', 'boipoka_app:book_list')
                return redirect(next_url)

            # Check if the user is trying to select the same subscription type
            if new_subscription_type == subscription.subscription_type:
                messages.error(request, "You are already using the selected subscription type.")
                message = f'You are already using the selected subscription type.'
                current_time_in_dhaka = timezone.now()
                dhaka_timezone = pytz.timezone('Asia/Dhaka')
                current_time_in_dhaka = current_time_in_dhaka.astimezone(dhaka_timezone)
                formatted_time = current_time_in_dhaka.strftime("%b. %d, %Y, %I:%M %p")
                Notifications.objects.create(
                    subscriber=request.user,
                    message=message,
                    timestamp=formatted_time,
                )
                
                next_url = request.POST.get('next', 'boipoka_app:book_list')
                return redirect(next_url)

            # Update the subscription details and save
            subscription.subscription_type = new_subscription_type
            subscription.max_books = new_max_books
            subscription.save()  # Save the updated subscription

            message = f'Your subscription has been {info} from {oldsubtype} to {newtype} successfully.'
            current_time_in_dhaka = timezone.now()
            dhaka_timezone = pytz.timezone('Asia/Dhaka')
            current_time_in_dhaka = current_time_in_dhaka.astimezone(dhaka_timezone)
            formatted_time = current_time_in_dhaka.strftime("%b. %d, %Y, %I:%M %p")
            Notifications.objects.create(
                subscriber=request.user,
                message=message,
                timestamp=formatted_time,
            )
            
            print(formatted_time)  # Debugging output for formatted time
            # messages.success(request, "Subscription updated successfully.")
            next_url = request.POST.get('next', 'boipoka_app:book_list')
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
    """
    View function to handle book return for the logged-in user.
    
    Retrieves the book and associated borrowing record for the current user, allowing them
    to mark the book as returned. If the request method is POST, the book is marked as returned,
    a notification is created, and the user is redirected.
    """
    # Retrieve the book and the borrowing record for the user
    book = get_object_or_404(Book, pk=pk)
    borrowing = Borrowing.objects.filter(book=book, user=request.user, returned_at__isnull=True).first()

    if request.method == 'POST':
        borrowing.return_book()  # Mark the book as returned
        borrowing.save()
        # messages.success(request, 'You have successfully returned this book.')
        
        # Get current time in Dhaka timezone
        dhaka_timezone = pytz.timezone('Asia/Dhaka')
        current_time_in_dhaka = timezone.now()
        current_time_in_dhaka = current_time_in_dhaka.astimezone(dhaka_timezone)
        formatted_time = current_time_in_dhaka.strftime("%b. %d, %Y, %I:%M %p")
        
        # Create a notification for the user
        message = f'You have successfully returned the book {book.title} at {formatted_time}'
        Notifications.objects.create(
            subscriber=request.user,
            message=message,
            timestamp=formatted_time,
        )
        
        # Redirect to the next page or the book list if not specified
        redirect_to = request.POST.get('next', 'boipoka_app:book_list')
        return redirect(redirect_to)

    # Render the return book template
    return render(request, 'boipoka_app/return_book.html', {'book': book, 'borrowing': borrowing})

@user_passes_test(is_admin)
def reissue_grant(request, pk):
    """
    Admin-only view function to grant a reissue request for a book borrowing record.
    
    This function extends the due date by 14 days, updates the borrowing state,
    and sends a notification to the user. It also sends an email to the user confirming the change.
    """
    borrowing = get_object_or_404(Borrowing, pk=pk)
    user = borrowing.user

    if request.method == 'POST':
        # Extend the due date by 14 days
        borrowing.borrowed_on=timezone.now()
        borrowing.due_date = borrowing.borrowed_on + timedelta(days=14)
        borrowing.reissue_state = False
        borrowing.save()
        
        # Get current time in Dhaka timezone
        dhaka_timezone = pytz.timezone('Asia/Dhaka')
        current_time_in_dhaka = timezone.now()
        current_time_in_dhaka = current_time_in_dhaka.astimezone(dhaka_timezone)
        formatted_time = current_time_in_dhaka.strftime("%b. %d, %Y, %I:%M %p")
        
        # Format and store the new due date
        borrowing.due_date = borrowing.due_date.astimezone(dhaka_timezone)
        borrowing.due_date = borrowing.due_date.strftime("%b. %d, %Y, %I:%M %p")
        
        #Format and store the new borrowing issued date
        
        borrowing.borrowed_on = borrowing.borrowed_on.astimezone(dhaka_timezone)
        borrowing.borrowed_on = borrowing.borrowed_on.strftime("%b. %d, %Y, %I:%M %p")
        
        # Update the borrowing state and save
        
        
        # Create a notification for the user
        message = f'Your reissue request for the book "{borrowing.book.title}" has successfully been granted.\nYour new due date is {borrowing.due_date}.'
        Notifications.objects.create(
            subscriber=user,
            message=message,
            timestamp=formatted_time,
        )

        # Prepare the email details
        subject = f'Reissue Request Grant Accpetance : "{borrowing.book.title}" Reissued on {borrowing.borrowed_on} '
        message = (
            f'Dear {borrowing.user.username},\n\n'
            f'Your reissue request for the book "{borrowing.book.title}" has successfully been granted.\nYour new due date is {borrowing.due_date}.\n'
            f'Thank you very much.\n\n'
            f'Best regards,\n\nBoipoka Admin\n\n'
        )
        recipient = borrowing.user.email
        reply_to_address = ['boipoka_admin@boipoka.com']

        # Send the email in a separate thread
        separate_thread = threading.Thread(
            target=send_email_threaded_single,
            args=(subject, message, settings.DEFAULT_FROM_EMAIL, recipient, reply_to_address)
        )
        separate_thread.start()
        
    return redirect('boipoka_app:user_details', pk=user.pk)

@login_required
def reissue_book(request, pk):
    """
    View function to handle a user's request to reissue a book.
    
    Retrieves the book and borrowing record for the current user, allowing them
    to send a reissue request. If the request method is POST, a notification is created,
    and the user is redirected to the book details page.
    """
    book = get_object_or_404(Book, pk=pk)
    user = request.user
    
    # Retrieve the user's borrowing record for the specific book
    borrowing = get_object_or_404(Borrowing, book=book, user=user, returned_at__isnull=True)

    if request.method == 'POST':
        # Logic to extend the due date (customize the extension period if needed)
        borrowing.reissue()
        
        # Create a notification for the user
        message = f'Your reissue request for the book "{borrowing.book.title}" has been successfully sent to the Admin.'
        dhaka_timezone = pytz.timezone('Asia/Dhaka')
        current_time_in_dhaka = timezone.now()
        current_time_in_dhaka = current_time_in_dhaka.astimezone(dhaka_timezone)
        formatted_time = current_time_in_dhaka.strftime("%b. %d, %Y, %I:%M %p")
        
        Notifications.objects.create(
            subscriber=request.user,
            message=message,
            timestamp=formatted_time,
        )

    return redirect("boipoka_app:book_details", pk=book.pk)


# Check if the user is an admin


# Admin: Add a new book
@user_passes_test(is_admin)
def add_book(request):
    """
    View function for adding a new book. Restricted to admin users only.
    """
    if request.method == 'POST':  # Check if the request method is POST (form submission)
        form = BookForm(request.POST, request.FILES)  # Create a form instance with the submitted data and files
        if form.is_valid():  # Validate the form data
            form.save()  # Save the new book to the database
            # messages.success(request, 'Book added successfully.')  # Optionally, display a success message
            return redirect('boipoka_app:book_list')  # Redirect to the book list page after successful addition
    else:
        form = BookForm()  # If GET request, create an empty form instance
    return render(request, 'boipoka_app/add_book.html', {'form': form})  # Render the add_book template with the form

# Admin: Edit an existing book
@user_passes_test(is_admin)
def edit_book(request, pk):
    """
    View function for editing an existing book. Restricted to admin users only.
    """
    book = get_object_or_404(Book, pk=pk)  # Retrieve the book based on the primary key (pk), or return a 404 if not found
    if request.method == 'POST':  # Check if the request method is POST (form submission)
        form = BookForm(request.POST, request.FILES, instance=book)  # Create a form instance with the submitted data and files for the specific book instance
        if form.is_valid():  # Validate the form data
            form.save()  # Save the updates to the book in the database
            # messages.success(request, 'Book updated successfully.')  # Optionally, display a success message
            return redirect('boipoka_app:book_list')  # Redirect to the book list page after successful update
    else:
        form = BookForm(instance=book)  # If GET request, create a form instance pre-filled with the book's current data
    return render(request, 'boipoka_app/edit_book.html', {'form': form, 'book': book})  # Render the edit_book template with the form and book information

# Admin: Delete a book
@user_passes_test(is_admin)
def delete_book(request, pk):
    """
    View function for deleting a book. Restricted to admin users only.
    """
    book = get_object_or_404(Book, pk=pk)  # Retrieve the book based on the primary key (pk), or return a 404 if not found
    if request.method == 'POST':  # Check if the request method is POST (confirmation submission)
        book.delete()  # Delete the book from the database
        # messages.success(request, 'Book deleted successfully.')  # Optionally, display a success message
        return redirect('boipoka_app:book_list')  # Redirect to the book list page after successful deletion
    return render(request, 'boipoka_app/delete_book.html', {'book': book})  # Render the delete_book template with the book information



@user_passes_test(is_admin)
def users(request):
    """
    View function to list all users who are not superusers. 
    Restricted to admin users only.
    """
    users = User.objects.filter(is_superuser=False)  # Query to get all users excluding superusers
    return render(request, 'boipoka_app/users.html', {'users': users})  # Render the users template with the list of users

@user_passes_test(is_admin)
def user_details(request, pk):
    """
    View function to display details of a specific user. 
    Restricted to admin users only.
    """
    user = get_object_or_404(User, pk=pk)  # Retrieve the user based on the primary key (pk), or return a 404 if not found
    borrowings = Borrowing.objects.filter(user=user)  # Retrieve all borrowing records associated with the user
    notreturnedbooks = borrowings.filter(returned_at__isnull=True)  # Filter borrowings for books not yet returned
    returned_books = borrowings.filter(returned_at__isnull=False)  # Filter borrowings for books that have been returned
    subscription = Subscription.objects.filter(user=user).first()  # Get the user's subscription details, if any
    overdue_books = borrowings.filter(due_date__lt=timezone.now(), returned_at__isnull=True)  # Find overdue books
    damaged_books = Borrowing.objects.filter(user=user, is_damagedorlost=True)  # Find borrowings marked as damaged or lost
    damaged_history = DamagedorLostHistory.objects.filter(user=user, isdeleted=True)  # Retrieve history of damaged or lost items
    reissue_requests = Borrowing.objects.filter(reissue_state=True, user=user)  # Retrieve reissue requests made by the user

    # Prepare the context dictionary to pass to the template
    context = {
        'user': user,
        'subscription': subscription,
        'borrowings': borrowings,
        'overdue_books': overdue_books,
        'returned_books': returned_books,
        'notreturnedbooks': notreturnedbooks,
        'damaged_books': damaged_books,
        'damaged_history': damaged_history,
        'reissue_requests': reissue_requests
    }

    return render(request, 'boipoka_app/user_details.html', {'context': context})  # Render the user_details template with the context

@user_passes_test(is_admin)
def reactivesubscription(request, pk):
    """
    View function to reactivate a user's subscription. 
    Restricted to admin users only.
    """
    subscription = get_object_or_404(Subscription, pk=pk)  # Retrieve the subscription based on the primary key (pk), or return a 404 if not found
    if request.method == 'POST':  # Check if the request method is POST (form submission)
        subscription.is_active = True  # Reactivate the subscription
        subscription.save()  # Save the updated subscription status
        
        # Prepare the email subject and message
        subject = f'Subscritpion Reactivation : {subscription.user.username}\'s Subscription Has been Activated'
        message = (
            f'Dear {subscription.user.username},\n\n'
            f'We have reactivated your subscription plan {subscription.subscription_type} successfully.\n'
            f'From now, you can have full access to the "Boipoka Book Borrowing System".\n\n'
            f'Thank you very much.\n\n'
            f'\n\n Best regards, \n\n Boipoka Admin\n\n'
        )
        recipient_list = [subscription.user.email]  # Set the recipient's email address
        reply_to_address = ['boipoka_admin@boipoka.com']  # Set the reply-to address
        
        # Create a separate thread to send the email
        separate_thread = threading.Thread(
            target=send_email_threaded,  # Function to send email
            args=(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list, reply_to_address)  # Arguments for the email function
        )
        separate_thread.start()  # Start the email sending thread

        # Create a notification for the user about the reactivation
        message = f'Your subscription of {subscription} plan has been successfully reactivated by Admin.\n.'
        Notifications.objects.create(  # Create a new notification entry
            subscriber=subscription.user,  # Set the user as the subscriber
            message=message,  # Set the notification message
            timestamp=timezone.now(),  # Set the current timestamp
        )
        # logger.info(f'Activated the subscription for user {subscription.user.username}')  # Log the activation (commented out)
    
    return redirect('boipoka_app:user_details', pk=subscription.user.pk)  # Redirect to the user details page after reactivation




@user_passes_test(is_admin)
def update_due_date(request, pk):
    """Update the due date of a specific borrowing."""
    borrowing = get_object_or_404(Borrowing, pk=pk)  # Retrieve the borrowing record based on the primary key (pk) or return a 404 if not found
    user = borrowing.user  # Get the user associated with this borrowing record
    
    if request.method == 'POST':  # Check if the request method is POST (indicating form submission)
        new_due_date_str = request.POST.get('due_date')  # Retrieve the new due date from the submitted form data
        # print(new_due_date_str)  # Debug: print the due date string received for verification

        # Parse the incoming date string in the format "2024-09-02T20:27" into a datetime object
        new_due_date = datetime.strptime(new_due_date_str, '%Y-%m-%dT%H:%M')
        
        # If the new due date is naive (i.e., it does not contain timezone information), make it timezone-aware
        if timezone.is_naive(new_due_date):
            new_due_date = timezone.make_aware(new_due_date, timezone.get_current_timezone())  # Attach current timezone to the naive datetime
        
        # Update the borrowing's due date with the new value and save the changes to the database
        borrowing.due_date = new_due_date  # Set the new due date
        borrowing.save()  # Save the updated borrowing record
        
        # Display a success message indicating the due date has been updated
        messages.success(request, f'Due date for "{borrowing.book.title}" updated successfully.')
    
    # Redirect the user back to the details page of the associated user after updating the due date
    return redirect('boipoka_app:user_details', pk=user.pk)

# Initialize a logger for the current module to log events
logger = logging.getLogger(__name__)

def send_email_threaded(subject: str, message: str, sender_email: str, toaddr: list, reply_to: list = None):
    """Send emails asynchronously in a separate thread with a reply-to address."""
    try:
        # Create an EmailMessage instance with the provided parameters
        email = EmailMessage(
            subject=subject,  # Set the email subject
            body=message,  # Set the email body/message
            from_email=sender_email,  # Set the sender's email address
            to=toaddr,  # Set the list of recipient email addresses
            reply_to=reply_to  # Include a reply-to address if provided
        )
        email.send(fail_silently=False)  # Send the email and raise an error if it fails
        logger.info(f"Email sent to {toaddr} with subject: '{subject}'")  # Log that the email was sent successfully
    except SMTPException as e:
        logger.error(f"Failed to send email: {str(e)}")  # Log an error if sending the email fails
    except Exception as e:
        logger.error(f"An error occurred while sending email: {str(e)}")  # Log any other exceptions that occur
        raise Exception("Something went wrong with sending email.")  # Raise a generic error for further handling
    
def send_email_threaded_single(subject: str, message: str, sender_email: str, toaddr, reply_to: list = None):
    """Send emails asynchronously in a separate thread with a reply-to address for a single recipient."""
    try:
        # Create an EmailMessage instance for a single recipient
        email = EmailMessage(
            subject=subject,  # Set the email subject
            body=message,  # Set the email body/message
            from_email=sender_email,  # Set the sender's email address
            to=[toaddr] if isinstance(toaddr, str) else toaddr,  # Convert toaddr to a list if it's a single string
            reply_to=reply_to  # Include a reply-to address if provided
        )
        email.send(fail_silently=False)  # Send the email and raise an error if it fails
        logger.info(f"Email sent to {toaddr} with subject: '{subject}'")  # Log that the email was sent successfully
    except SMTPException as e:
        logger.error(f"Failed to send email: {str(e)}")  # Log an error if sending the email fails
    except Exception as e:
        logger.error(f"An error occurred while sending email: {str(e)}")  # Log any other exceptions that occur
        raise Exception("Something went wrong with sending email.")  # Raise a generic error for further handling


@user_passes_test(is_admin)
def send_reminder(request, pk):
    """Send a reminder to a specific user about their overdue book asynchronously."""
    # Retrieve the user based on the primary key (pk) or return a 404 if not found
    user = get_object_or_404(User, pk=pk)
    
    # Get all borrowings for the user that are not returned and are overdue
    borrowings = Borrowing.objects.filter(user=user, returned_at__isnull=True, due_date__lt=timezone.now())
    
    # Retrieve the user's subscription details, or return a 404 if not found
    subscription = get_object_or_404(Subscription, user=user)
            
    # If there are no overdue borrowings, redirect to the user's details page
    if not borrowings.exists():
        # messages.warning(request, f'No overdue books found for user ID {pk}.')
        return redirect('boipoka_app:user_details', pk=user.pk)
    
    # Determine the penalty rate based on the user's subscription type
    penalty_rate = 0
    if subscription:
        if subscription.subscription_type == 'Basic':
            penalty_rate = 2  # Basic subscription penalty rate
        elif subscription.subscription_type == 'Premium':
            penalty_rate = 5  # Premium subscription penalty rate
        elif subscription.subscription_type == 'VIP':
            penalty_rate = 10  # VIP subscription penalty rate
    
    # Iterate through each overdue borrowing to prepare and send reminders
    for borrowing in borrowings:
        due_date = borrowing.due_date  # Get the due date of the borrowing
        time_now = timezone.now()  # Get the current time
        difference = (time_now - due_date).days + 10  # Calculate the difference in days (adding grace period of 10 days)
        penalty = penalty_rate * difference if difference > 0 else 0  # Calculate penalty only if the book is overdue
        
        # Prepare the email subject and message for the reminder
        subject = f'Reminder: Overdue Book - {borrowing.book.title}'
        message = (
            f'Dear {borrowing.user.username},\n\n'
            f'This is a reminder that the book "{borrowing.book.title}" is overdue. '
            f'Please return it as soon as possible.\n\n'
            f'Penalty for overdue: {penalty} tk (based on your {subscription.subscription_type} subscription).\n\n'
        )
        
        recipient_list = [borrowing.user.email]  # List of recipient email addresses
        reply_to_address = ['boipoka_admin@boipoka.com']  # Reply-to email address
        
        # Create a separate thread to send the email asynchronously
        separate_thread = threading.Thread(
            target=send_email_threaded,
            args=(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list, reply_to_address)
        )
        separate_thread.start()  # Start the thread to send the email asynchronously

    # messages.success(request, f'Reminder(s) sent to {", ".join([b.user.username for b in borrowings])} for their overdue books.')
    # Redirect to the user's details page after sending reminders
    return redirect('boipoka_app:user_details', pk=pk)


@user_passes_test(is_admin)
def send_returned_notifications(request, pk):
    """Send notifications to a specific user about successfully returned books."""
    user = get_object_or_404(User, pk=pk)  # Retrieve the user based on the primary key (pk)
    
    # Get all borrowings for the user that have been returned
    returnedbooks = Borrowing.objects.filter(user=user, returned_at__isnull=False)
    
    # If there are no returned books, redirect to the user's details page
    if not returnedbooks.exists():
        return redirect('boipoka_app:user_details', pk=user.pk)
    
    # Iterate through each returned book to prepare and send notifications
    for item in returnedbooks:
        due_date = item.due_date  # Get the due date of the borrowing
        returntime = item.returned_at  # Get the time the book was returned
        
        # Prepare the email subject and message for the returned book notification
        subject = f'Returned Successfully: {item.book.title}'
        message = (
            f'Dear {item.user.username},\n\n'
            f'You have successfully returned the book "{item.book.title}" at {returntime} which is within your due date {due_date}. '
            f'Thank you very much.\n\n'
            f'Best regards,\n\nBoipoka Admin\n\n'
        )
        
        recipient_list = [item.user.email]  # List of recipient email addresses
        reply_to_address = ['boipoka_admin@boipoka.com']  # Reply-to email address
        
        # Create a separate thread to send the email asynchronously
        separate_thread = threading.Thread(
            target=send_email_threaded,
            args=(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list, reply_to_address)
        )
        separate_thread.start()  # Start the thread to send the email asynchronously
        
    # Redirect to the user's details page after sending notifications
    return redirect('boipoka_app:user_details', pk=user.pk)  


@user_passes_test(is_admin)
def send_borrowed_notifications(request, pk):
    """Send notifications to a specific user about successfully borrowed books."""
    user = get_object_or_404(User, pk=pk)  # Retrieve the user based on the primary key (pk)
    
    # Get all borrowings for the user that have not been returned
    borrowings = Borrowing.objects.filter(user=user, returned_at__isnull=True)

    # If there are no borrowed books, redirect to the user's details page
    if not borrowings.exists():
        return redirect('boipoka_app:user_details', pk=user.pk)
    
    # Iterate through each borrowed book to prepare and send notifications
    for item in borrowings:
        due_date = item.due_date  # Get the due date of the borrowing
        
        # Prepare the email subject and message for the borrowed book notification
        subject = f'Borrowed Book Info Registered: {item.book.title}'
        message = (
            f'Dear {item.user.username},\n\n'
            f'You have successfully borrowed the book "{item.book.title}" on your {item.subscription} plan at {item.borrowed_on}. Your due date is {due_date}. '
            f'Please try to return the book as early as possible within your due time.\n\n'
            f'Thank you very much.\n\n'
            f'Best regards,\n\nBoipoka Admin\n\n'
        )
        
        recipient_list = [item.user.email]  # List of recipient email addresses
        reply_to_address = ['boipoka_admin@boipoka.com']  # Reply-to email address
        
        # Create a separate thread to send the email asynchronously
        separate_thread = threading.Thread(
            target=send_email_threaded,
            args=(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list, reply_to_address)
        )
        separate_thread.start()  # Start the thread to send the email asynchronously
        
    # Redirect to the user's details page after sending notifications
    return redirect('boipoka_app:user_details', pk=user.pk)  


    


@user_passes_test(is_admin)
def edit_user(request, pk):
    """Edit the details of a specific user identified by their primary key (pk)."""
    user = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        # Update username and email from the form data
        user.username = request.POST.get('username', user.username)
        user.email = request.POST.get('email', user.email)
        user.save()  # Save the updated user information
        # Optionally, add a success message (commented out)
        # messages.success(request, f'User {user.username} updated successfully.')
        return redirect('boipoka_app:user_details', pk=pk)

    # Render the edit user form with the current user details
    return render(request, 'boipoka_app/edit_user.html', {'user': user})

@user_passes_test(is_admin)
def send_payment_needed(request, pk):
    """Send notification to a user about payment required for damaged/lost books."""
    user = get_object_or_404(User, pk=pk)
    reported = Borrowing.objects.filter(user=user, is_damagedorlost=True, fine_paid=False)  # Get reported borrowings
    dhaka_timezone = pytz.timezone('Asia/Dhaka')

    if not reported.exists():
        return redirect('boipoka_app:user_details', pk=user.pk)  # No reported items, redirect

    for item in reported:
        # Format the report time in the desired timezone
        reporttime = item.damagedlostat.astimezone(dhaka_timezone).strftime("%b. %d, %Y, %I:%M %p")
        subject = f'Reminder - Payment Needed for Prohibiting the Subscription Being Suspended for Damaged/Lost Event of the Book: {item.book.title}'
        message = (
            f'Dear {item.user.username},\n\n'
            f'Attention! It is mandatory to pay 500 TK within 1 day from the reported time {reporttime} for being damaged or lost of the book "{item.book.title}".'
            f'Otherwise, we will be very strict to make your subscription suspended until you pay for it.\n\n'
            f'Thank you very much.\n\n'
            f'Best regards,\n\nBoipoka Admin\n\n'
        )
        recipient_list = [item.user.email]  # List of recipients
        reply_to_address = ['boipoka_admin@boipoka.com']  # Reply-to address
        
        # Send email asynchronously using a separate thread
        separate_thread = threading.Thread(
            target=send_email_threaded,
            args=(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list, reply_to_address)
        )
        separate_thread.start()
        
    return redirect('boipoka_app:user_details', pk=user.pk)    

@user_passes_test(is_admin)
def send_payment_approval(request, pk):
    """Send notification to a user confirming payment approval for damaged/lost books."""
    user = get_object_or_404(User, pk=pk)
    approved = Borrowing.objects.filter(user=user, is_damagedorlost=True, fine_paid_approved=True)  # Get approved borrowings

    if not approved.exists():
        return redirect('boipoka_app:user_details', pk=user.pk)  # No approved items, redirect

    for item in approved:
        subject = f'Payment Successfully Approved - Payment Approved for the Damaged/Lost Event of the Book: {item.book.title}'
        message = (
            f'Dear {item.user.username},\n\n'
            f'We have received 500 TK as your payment for the damaged/lost event of the book "{item.book.title}" on {item.fine_paid_at} and approved it.'
            f'If you are suspended, we will reactivate your subscription very soon.\n\n'
            f'Thank you very much.\n\n'
            f'Best regards,\n\nBoipoka Admin\n\n'
        )
        recipient_list = [item.user.email]  # List of recipients
        reply_to_address = ['boipoka_admin@boipoka.com']  # Reply-to address
        
        # Send email asynchronously using a separate thread
        separate_thread = threading.Thread(
            target=send_email_threaded,
            args=(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list, reply_to_address)
        )
        separate_thread.start()
        
    return redirect('boipoka_app:user_details', pk=user.pk)    

@user_passes_test(is_admin)
def delete_user(request, pk):
    """Delete a specific user identified by their primary key (pk)."""
    user = get_object_or_404(User, pk=pk)
    user.delete()  # Delete the user record
    # Optionally, add a success message (commented out)
    # messages.success(request, f'User {user.username} deleted successfully.')
    return redirect('boipoka_app:users')

@user_passes_test(is_admin)
def delete_subscription(request, pk):
    """Delete a user's subscription if it exists."""
    user = get_object_or_404(User, pk=pk)
    subscription = Subscription.objects.filter(user=user).first()  # Get the user's subscription

    if subscription:
        subscription.delete()  # Delete the subscription if it exists
    
    return redirect('boipoka_app:user_details', pk=user.pk)

@user_passes_test(is_admin)
def manage_subscriptions_starting(request, pk):
    """Manage the starting date of a subscription identified by its primary key (pk)."""
    subscription = get_object_or_404(Subscription, pk=pk)  # Retrieve the subscription or return a 404 error
    user = subscription.user  # Get the user associated with the subscription

    if request.method == 'POST':
        # Retrieve the new starting date from the form
        new_subscription_startdate_str = request.POST.get('start-date')
        new_subscription_startdate = datetime.strptime(new_subscription_startdate_str, '%Y-%m-%dT%H:%M')  # Parse the input date string
        
        # If the new start date is naive (without timezone info), make it timezone-aware
        if timezone.is_naive(new_subscription_startdate):
            new_subscription_startdate = timezone.make_aware(new_subscription_startdate, timezone.get_current_timezone())
        
        subscription.subscription_start = new_subscription_startdate  # Update the subscription start date
        subscription.save()  # Save the updated subscription

    return redirect('boipoka_app:user_details', pk=user.pk)  # Redirect to the user details page


@user_passes_test(is_admin)
def manage_subscriptions_ending(request, pk):
    """Manage the ending date of a subscription identified by its primary key (pk)."""
    subscription = get_object_or_404(Subscription, pk=pk)  # Retrieve the subscription or return a 404 error
    user = subscription.user  # Get the user associated with the subscription

    if request.method == 'POST':
        # Retrieve the new ending date from the form
        new_subscription_enddate_str = request.POST.get('expire-date')
        new_subscription_enddate = datetime.strptime(new_subscription_enddate_str, '%Y-%m-%dT%H:%M')  # Parse the input date string
        
        # If the new end date is naive (without timezone info), make it timezone-aware
        if timezone.is_naive(new_subscription_enddate):
            new_subscription_enddate = timezone.make_aware(new_subscription_enddate, timezone.get_current_timezone())
        
        subscription.subscription_end = new_subscription_enddate  # Update the subscription end date
        subscription.save()  # Save the updated subscription

    return redirect('boipoka_app:user_details', pk=user.pk)  # Redirect to the user details page


@login_required
def renew_subscription(request):
    """Renew the subscription of the logged-in user by extending the end date by 30 days."""
    subscription = get_object_or_404(Subscription, user=request.user)  # Retrieve the user's subscription or return a 404 error

    if request.method == 'POST':
        # Extend the subscription period by 30 days
        subscription.subscription_end += timedelta(days=30)  # Increase the end date
        subscription.save()  # Save the updated subscription
        request.user = get_user_model().objects.get(pk=request.user.pk)  # Refresh the user instance
        
        # Optionally, add a success message (commented out)
        # messages.success(request, "Your subscription has been renewed successfully.")
        return redirect('boipoka_app:book_list')  # Redirect to the book list page

    # Render the renewal form with the current subscription details
    return render(request, 'boipoka_app/renew_subscription.html', {'subscription': subscription})



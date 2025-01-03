# Importing timedelta for handling time intervals
from datetime import timedelta

# Importing timezone utility from Django
from django.utils import timezone

# Importing Mock and patch to mock objects and functions during testing
from unittest.mock import Mock, patch

# Importing Django's TestCase class to create unit tests
from django.test import TestCase

# Importing reverse to retrieve URLs by their names
from django.urls import reverse

# Importing the custom user creation form from forms module
from boipoka_app.forms import CustomUserCreationForm

# Importing the Django function to get the custom user model
from django.contrib.auth import get_user_model

# Importing the Book, Borrowing, and Subscription models
from .models import Book, Borrowing, Subscription,Notifications,DamagedorLostHistory

# Importing fetch_books_data and create_books_in_db functions from views
from .views import fetch_books_data, create_books_in_db,notify_user

# Importing json for handling JSON data
import json

from django.test import Client

# Getting the custom User model
User = get_user_model()



# class NotifyUserViewTest(TestCase):
#     def setUp(self):
#         # Set up a client and create a user
#         self.client = Client()
#         self.user = User.objects.create_user(username='testuser', password='testpass')
#         self.url = reverse('boipoka_app:notifications')  # Replace with the actual name of the URL pattern for 'notify_user'
#         self.other_user = User.objects.create_user(username='otheruser', password='otherpass')
#         # Create a notification for self.user
#         self.notification = Notifications.objects.create(subscriber=self.user, is_read=False)

#         # URLs for the views, assuming you have named the URL patterns properly
#         self.makeunread_url = reverse('boipoka_app:makeunread', args=[self.notification.pk])
#         self.deletenotification_url = reverse('boipoka_app:deletenotification', args=[self.notification.pk])
#     def test_redirect_anonymous_user(self):
#         """Test that anonymous users are redirected to the login page"""
#         response = self.client.get(self.url)
#         self.assertEqual(response.status_code, 302)
#         self.assertIn('/login/', response.url)

#     def test_logged_in_user_no_notifications(self):
#         """Test that a logged-in user with no notifications sees an empty list"""
#         self.client.login(username='testuser', password='testpass')
#         # Clear any existing notifications for self.user
#         Notifications.objects.filter(subscriber=self.user).delete()
#         response = self.client.get(self.url)
#         self.assertEqual(response.status_code, 200)
#         self.assertTemplateUsed(response, 'boipoka_app/notification.html')
#         self.assertEqual(list(response.context['notifications']), [])
#         self.assertEqual(response.context['unclickable'], {})


#     def test_logged_in_user_with_unread_notifications(self):
#         """Test that a logged-in user with unread notifications sees clickable notifications"""
#         self.client.login(username='testuser', password='testpass')
        
#         # Clear existing notifications for the user
#         Notifications.objects.filter(subscriber=self.user).delete()
        
#         # Create an unread notification for the user
#         unread_notification = Notifications.objects.create(subscriber=self.user, is_read=False)
        
#         response = self.client.get(self.url)
#         self.assertEqual(response.status_code, 200)
#         self.assertTemplateUsed(response, 'boipoka_app/notification.html')
#         self.assertEqual(response.context['unclickable'], {unread_notification.pk: True})

#     def test_logged_in_user_with_read_notifications(self):
#         """Test that a logged-in user with read notifications sees non-clickable notifications"""
#         self.client.login(username='testuser', password='testpass')
        
#         # Clear existing notifications for the user
#         Notifications.objects.filter(subscriber=self.user).delete()
        
#         # Create a read notification for the user
#         read_notification = Notifications.objects.create(subscriber=self.user, is_read=True)
        
#         response = self.client.get(self.url)
#         self.assertEqual(response.status_code, 200)
#         self.assertTemplateUsed(response, 'boipoka_app/notification.html')
#         self.assertEqual(response.context['unclickable'], {read_notification.pk: False})

#     def test_logged_in_user_with_mixed_notifications(self):
#         """Test that a logged-in user with both read and unread notifications sees the correct clickable statuses"""
#         self.client.login(username='testuser', password='testpass')
#         # Clear any existing notifications for self.user before creating new ones
#         Notifications.objects.filter(subscriber=self.user).delete()

#         # Create both read and unread notifications for the user
#         unread_notification = Notifications.objects.create(subscriber=self.user, is_read=False)
#         read_notification = Notifications.objects.create(subscriber=self.user, is_read=True)
        
#         response = self.client.get(self.url)
#         self.assertEqual(response.status_code, 200)
#         self.assertTemplateUsed(response, 'boipoka_app/notification.html')
#         notifications = list(response.context['notifications'])

#         self.assertEqual(len(notifications), 2)  # Ensure only these two are considered
#         self.assertIn(read_notification, notifications)
#         self.assertIn(unread_notification, notifications)
#         self.assertEqual(
#             response.context['unclickable'],
#             {
#                 read_notification.pk: False,
#                 unread_notification.pk: True
#             }
#         )

    
    
#     def test_makeunread_redirects_anonymous_user(self):
#         """Test that an anonymous user is redirected when accessing the makeunread view"""
#         response = self.client.get(self.makeunread_url)
#         self.assertEqual(response.status_code, 302)
#         self.assertIn('/login/', response.url)

#     def test_deletenotification_redirects_anonymous_user(self):
#         """Test that an anonymous user is redirected when accessing the deletenotification view"""
#         response = self.client.get(self.deletenotification_url)
#         self.assertEqual(response.status_code, 302)
#         self.assertIn('/login/', response.url)

#     def test_makeunread_marks_notification_as_read(self):
#         """Test that a logged-in user can mark a notification as read"""
#         self.client.login(username='testuser', password='testpass')
#         response = self.client.get(self.makeunread_url)
#         self.assertEqual(response.status_code, 302)
#         self.assertRedirects(response, reverse('boipoka_app:notifications'))

#         # Refresh the notification from the database to check its state
#         self.notification.refresh_from_db()
#         self.assertTrue(self.notification.is_read)

#     def test_deletenotification_deletes_notification(self):
#         """Test that a logged-in user can delete a notification"""
#         self.client.login(username='testuser', password='testpass')
#         response = self.client.get(self.deletenotification_url)
#         self.assertEqual(response.status_code, 302)
#         self.assertRedirects(response, reverse('boipoka_app:notifications'))

#         # Check that the notification no longer exists
#         with self.assertRaises(Notifications.DoesNotExist):
#             Notifications.objects.get(pk=self.notification.pk)

#     def test_makeunread_nonexistent_notification(self):
#         """Test that a 404 is returned if the notification does not exist"""
#         self.client.login(username='testuser', password='testpass')
#         invalid_url = reverse('boipoka_app:makeunread', args=[9999])
#         response = self.client.get(invalid_url)
#         self.assertEqual(response.status_code, 404)

#     def test_deletenotification_nonexistent_notification(self):
#         """Test that a 404 is returned if the notification does not exist"""
#         self.client.login(username='testuser', password='testpass')
#         invalid_url = reverse('boipoka_app:deletenotification', args=[9999])
#         response = self.client.get(invalid_url)
#         self.assertEqual(response.status_code, 404)

#     def test_makeunread_other_user_notification(self):
#         """Test that a user cannot access another user's notification to mark it as read"""
#         # Create a notification for another user
#         other_notification = Notifications.objects.create(subscriber=self.other_user, is_read=False)
#         self.client.login(username='testuser', password='testpass')
#         response = self.client.get(reverse('boipoka_app:makeunread', args=[other_notification.pk]))
#         self.assertEqual(response.status_code, 403)

#     def test_deletenotification_other_user_notification(self):
#         """Test that a user cannot access another user's notification to delete it"""
#         # Create a notification for another user
#         other_notification = Notifications.objects.create(subscriber=self.other_user, is_read=False)
#         self.client.login(username='testuser', password='testpass')
#         response = self.client.get(reverse('boipoka_app:deletenotification', args=[other_notification.pk]))
#         self.assertEqual(response.status_code, 403)


# class RegisterViewTest(TestCase):

#     def test_post_empty_form(self):
#         response = self.client.post(reverse('boipoka_app:register'), {})
#         # Ensure the status code is 200
#         self.assertEqual(response.status_code, 200)
#         # Retrieve the form from the context
#         form = response.context.get('form')
#         self.assertIsNotNone(form)  # Ensure the form exists in the context
#         # Check each field for the required validation message
#         self.assertFormError(form, 'username', 'This field is required.')
#         self.assertFormError(form,  'email', 'This field is required.')
#         self.assertFormError(form,  'password1', 'This field is required.')
#         self.assertFormError(form, 'password2', 'This field is required.')

#     def test_post_invalid_data_returns_form(self):
#         response = self.client.post(reverse('boipoka_app:register'), {
#             'username': 'testuser',
#             'email': 'test@example.com',
#             'password1': 'password123',
#             'password2': 'differentpassword',  # Passwords don't match
#         })
#         # Ensure the status code is 200
#         self.assertEqual(response.status_code, 200)
#         # Retrieve the form from the context
#         form = response.context.get('form')
#         self.assertIsNotNone(form)  # Ensure the form exists in the context
#         # Check if the password mismatch error is present
#         self.assertFormError(form, 'password2', 'The two password fields didn’t match.')

#     def test_post_missing_email(self):
#         response = self.client.post(reverse('boipoka_app:register'), {
#             'username': 'testuser',
#             'password1': 'password123',
#             'password2': 'password123',
#         })
#         # Ensure the status code is 200
#         self.assertEqual(response.status_code, 200)
#         # Retrieve the form from the context
#         form = response.context.get('form')
#         self.assertIsNotNone(form)  # Ensure the form exists in the context
#         # Check if the email field has the required error
#         self.assertFormError(form, 'email', 'This field is required.')

#     def test_post_valid_form(self):
#         response = self.client.post(reverse('boipoka_app:register'), {
#             'username': 'validuser',
#             'email': 'validuser@example.com',
#             'password1': 'validpassword123',
#             'password2': 'validpassword123',
#         })
#         # Check for a redirect (successful registration usually redirects)
#         self.assertEqual(response.status_code, 302)
#         # Ensure the user was created
#         self.assertTrue(User.objects.filter(username='validuser').exists())




class LoginViewTest(TestCase):

    def setUp(self):
        # Set up a test user and an admin user
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.admin_user = User.objects.create_superuser(username='adminuser', password='adminpass')
        
        # URL for the login view
        self.url = reverse('boipoka_app:login')
    
    def test_login_with_active_subscription(self):
        # Create an active subscription for the user
        Subscription.objects.create(user=self.user, is_active=True)
        
        response = self.client.post(self.url, {'username': 'testuser', 'password': 'password123'})
        
        self.assertEqual(response.status_code, 302)  # Redirect expected
        self.assertRedirects(response, reverse('boipoka_app:book_list'))
    
    def test_login_with_no_subscription(self):
        # User with no subscription
        response = self.client.post(self.url, {'username': 'testuser', 'password': 'password123'})
        
        self.assertEqual(response.status_code, 302)  # Redirect expected
        self.assertRedirects(response, reverse('boipoka_app:subscription'))
    
    def test_login_with_inactive_subscription_less_than_3_incidents(self):
        # Create an inactive subscription and fewer than 3 incidents
        subscription = Subscription.objects.create(
            user=self.user,
            is_active=False
        )
        book = Book.objects.create(
            title="Test Book",
            author="Author"
        )
        damaged_or_lost_at = timezone.now()  # Example datetime value
        fine_paid = False
        fine_paid_at = damaged_or_lost_at + timedelta(days=2)  # Example value

        # Condition: if fine_paid is False or fine_paid_at is greater than damaged_or_lost_at + 1 day
        if not fine_paid or fine_paid_at > damaged_or_lost_at + timedelta(days=1):
            Borrowing.objects.create(
                user=self.user,
                book=book,
                is_damagedorlost=True,
                damagedlostat=damaged_or_lost_at,  # Adjusted field name to match model
                fine_paid=fine_paid,
                fine_paid_at=fine_paid_at,
                subscription=subscription
            )

        response = self.client.post(
            self.url,
            {'username': 'testuser', 'password': 'password123'}
        )
        
        self.assertEqual(response.status_code, 302)  # Redirect expected
        self.assertRedirects(response, reverse('boipoka_app:subscription'))
    
    def test_login_with_inactive_subscription_3_or_more_incidents(self):
        # Create an inactive subscription and 3 incidents
        subscription = Subscription.objects.create(user=self.user, is_active=False)
        book = Book.objects.create(title="Test Book", author="Author")
        Borrowing.objects.create(user=self.user,book=book, is_damagedorlost=True,subscription=subscription)
        Borrowing.objects.create(user=self.user,book=book, is_damagedorlost=True,subscription=subscription)
        Borrowing.objects.create(user=self.user,book=book, is_damagedorlost=True,subscription=subscription)
        
        response = self.client.post(self.url, {'username': 'testuser', 'password': 'password123'})
        
        self.assertEqual(response.status_code, 302)  # Redirect expected back to login due to suspension
        self.assertRedirects(response, self.url)
        self.assertContains(response, "Your account has been suspended. Please contact the Admin.")
    
    # @patch('boipoka_app.views.is_admin', return_value=True)
    # def test_login_as_admin_user(self, mock_is_admin):
    #     # Admin user login
    #     response = self.client.post(self.url, {'username': 'adminuser', 'password': 'adminpass'})
        
    #     self.assertEqual(response.status_code, 302)  # Redirect expected
    #     self.assertRedirects(response, reverse('boipoka_app:book_list'))
    
    # def test_login_with_invalid_credentials(self):
    #     # Attempt to login with wrong credentials
    #     response = self.client.post(self.url, {'username': 'testuser', 'password': 'wrongpassword'})
        
    #     self.assertEqual(response.status_code, 200)  # Should return login page
    #     self.assertTemplateUsed(response, 'boipoka_app/login.html')
    #     self.assertContains(response, 'Invalid credentials', html=True)
    
    # def test_get_request_to_login_page(self):
    #     # Test a GET request to ensure login page is rendered
    #     response = self.client.get(self.url)
        
    #     self.assertEqual(response.status_code, 200)  # Page should load successfully
    #     self.assertTemplateUsed(response, 'boipoka_app/login.html')

























# Defining test cases for the Boipoka app
# class BoipokaAppTests(TestCase):

#     # Test case for the 'index' view
#     def test_index_view(self):
#         """
#         Test the index view returns a 200 status code and the correct template.
#         """
#         # Reverse the URL for the 'index' view and send a GET request
#         response = self.client.get(reverse('boipoka_app:index'))
        
#         # Check if the status code is 200 (OK)
#         self.assertEqual(response.status_code, 200)
        
#         # Ensure the correct template is used
#         self.assertTemplateUsed(response, 'boipoka_app/index.html')

#     # Test case for the 'register' view when accessed via GET request
#     def test_register_view_get(self):
#         """
#         Test the register view with a GET request returns a 200 status code
#         and the registration form.
#         """
#         # Reverse the URL for the 'register' view and send a GET request
#         response = self.client.get(reverse('boipoka_app:register'))
        
#         # Check if the status code is 200 (OK)
#         self.assertEqual(response.status_code, 200)
        
#         # Ensure the correct template is used
#         self.assertTemplateUsed(response, 'boipoka_app/register.html')
        
#         # Check if the form in the response context is an instance of CustomUserCreationForm
#         self.assertIsInstance(response.context['form'], CustomUserCreationForm)

#     # Test case for the 'register' view when invalid data is submitted via POST request
#     def test_register_view_post_invalid(self):
#         # Create invalid form data with missing username, invalid password, and email
#         form_data = {
#             'username': '',  # Invalid data
#             'password1': 'short',  # Invalid password
#             'password2': 'short',
#             'email': '',  # Invalid email
#         }
        
#         # Send a POST request with invalid data
#         response = self.client.post(reverse('boipoka_app:register'), form_data)

#         # Print status code and response content for debugging purposes
#         print(f'Status Code: {response.status_code}')
#         print(f'Response Content: {response.content.decode()}')

#         # Check if there's a redirect (in case of 302)
#         if response.status_code == 302:
#             # Follow the redirect and print status
#             response = self.client.get(response.url)
#             print("Redirect detected. Following the redirect...")

#         # Check if the response is still 200 (form should be re-rendered with errors)
#         self.assertEqual(response.status_code, 200)

#         # Get the form from the response context
#         form = response.context.get('form')
        
#         # Ensure the form is in the context
#         self.assertIsNotNone(form, "Form not found in response context.")

#         # Assert specific errors on form fields
#         self.assertFormError(response, 'form', 'username', 'This field is required.')
#         self.assertFormError(response, 'form', 'email', 'This field is required.')
#         self.assertFormError(response, 'form', 'password1', 'This password is too short. It must contain at least 8 characters.')

#     # Test case for the 'register' view when valid data is submitted via POST request
#     def test_register_view_post_valid(self):
#         # Create valid form data
#         form_data = {
#             'username': 'testuser',
#             'password1': 'secure_password',
#             'password2': 'secure_password',
#             'email': 'testuser@example.com',  # Ensure email is included
#         }
#         # Send a POST request with valid data
#         response = self.client.post(reverse('boipoka_app:register'), data=form_data)

#         # Check if the user was successfully created in the database
#         self.assertTrue(User.objects.filter(username='testuser').exists(), "User was not created.")
        
#         # Ensure the user is redirected to the login page after successful registration
#         self.assertRedirects(response, reverse('boipoka_app:login'))

#     # Test case for the 'register' view when a required field is missing in the POST request
#     def test_register_view_post_missing_field(self):
#         """
#         Test the register view with a POST request where a required field is missing.
#         It should not create a user and should show form validation errors.
#         """
#         # Create form data with missing username field
#         form_data = {
#             'username': '',  # Missing username
#             'password1': 'TestPassword123',
#             'password2': 'TestPassword123',
#         }
#         # Send a POST request with incomplete data
#         response = self.client.post(reverse('boipoka_app:register'), form_data)

#         # Ensure no user was created due to missing field
#         self.assertFalse(User.objects.filter(username='').exists())

#         # Check that the form is re-rendered with validation errors
#         self.assertEqual(response.status_code, 200)
#         self.assertTemplateUsed(response, 'boipoka_app/register.html')
#         self.assertIsInstance(response.context['form'], CustomUserCreationForm)
#         self.assertTrue(response.context['form'].errors)

#     # Test case for the 'register' view when a user is already authenticated
#     def test_register_view_authenticated_user(self):
#         """
#         Test the register view when the user is already authenticated.
#         The user should be redirected away from the registration page.
#         """
#         # Create and log in a test user
#         user = User.objects.create_user(username='testuser', password='TestPassword123')
#         self.client.login(username='testuser', password='TestPassword123')

#         # Try accessing the register page while logged in
#         response = self.client.get(reverse('boipoka_app:register'))

#         # Ensure the user is redirected away since they are already authenticated
#         self.assertRedirects(response, '/')

# # Define test cases for the login view
# class LoginViewTests(TestCase):
    
#     def setUp(self):
#         # Create a test user for login tests
#         self.username = 'testuser'
#         self.password = 'testpassword'
#         self.user = User.objects.create_user(username=self.username, password=self.password)

#     # Test case for successful login
#     def test_login_view_success(self):
#         """Test that a user can log in successfully."""
#         # Send POST request with valid login credentials
#         response = self.client.post(reverse('boipoka_app:login'), {
#             'username': self.username,
#             'password': self.password
#         })
#         # Ensure the user is redirected to the book list view
#         self.assertRedirects(response, reverse('boipoka_app:book_list'))
#         # Verify that the user is authenticated
#         self.assertTrue(response.wsgi_request.user.is_authenticated)

#     # Test case for login with invalid credentials
#     def test_login_view_invalid_credentials(self):
#         """Test that login fails with invalid credentials."""
#         # Send POST request with invalid credentials
#         response = self.client.post(reverse('boipoka_app:login'), {
#             'username': 'wronguser',
#             'password': 'wrongpassword'
#         })
#         # Ensure the response is 200 and the form re-renders with an error
#         self.assertEqual(response.status_code, 200)
#         self.assertContains(response, 'Invalid credentials')
#         # Ensure the user is not authenticated
#         self.assertFalse(response.wsgi_request.user.is_authenticated)

#     # Test case to check the GET request for login page
#     def test_login_view_get(self):
#         """Test that GET requests return the login page."""
#         # Send a GET request to the login page
#         response = self.client.get(reverse('boipoka_app:login'))
#         # Check if the response status code is 200
#         self.assertEqual(response.status_code, 200)
#         # Ensure the correct template is used
#         self.assertTemplateUsed(response, 'boipoka_app/login.html')

# # Define test cases for the logout view
# class LogoutViewTests(TestCase):
    
#     def setUp(self):
#         """Create a user and log them in for testing."""
#         self.username = 'testuser'
#         self.password = 'testpassword'
#         self.user = User.objects.create_user(username=self.username, password=self.password)
#         # Log in the user
#         self.client.login(username=self.username, password=self.password)

#     # Test case to ensure the user can log out
#     def test_logout_view(self):
#         """Test that the user can log out successfully."""
#         # Send a GET request to the logout view
#         response = self.client.get(reverse('boipoka_app:logout'))
#         # Ensure the user is redirected to the index page after logout
#         self.assertRedirects(response, reverse('boipoka_app:index'))
#         # Verify that the user is no longer authenticated
#         self.assertFalse(response.wsgi_request.user.is_authenticated)



# class BookDataTests(TestCase):
#     """Test cases for fetching and creating book data."""

#     @patch('boipoka_app.views.requests.get')
#     def test_fetch_books_data_success(self, mock_get):
#         """Test fetch_books_data for a successful API call."""
#         # Mocking the API response with successful status code (200)
#         mock_get.return_value.status_code = 200
#         # Mocking the JSON response for the books data
#         mock_get.return_value.json.return_value = {
#             "items": [
#                 {
#                     "volumeInfo": {
#                         "title": "Test Book",
#                         "authors": ["Author One", "Author Two"],
#                         "description": "A test description.",
#                         "imageLinks": {
#                             "thumbnail": "http://example.com/test_book_thumbnail.jpg"
#                         }
#                     }
#                 }
#             ]
#         }

#         # Mocking the image response for the book cover thumbnail
#         mock_image_response = Mock()
#         mock_image_response.status_code = 200
#         # Mocking the image content as bytes (representing an image)
#         mock_image_response.content = b'This is a mock image content'
        
#         # Patching 'requests.get' to return both the mocked JSON data and image response
#         with patch('boipoka_app.views.requests.get', side_effect=[mock_get.return_value, mock_image_response]):
#             books = fetch_books_data()
        
#         # Asserting that one book is returned from the API
#         self.assertEqual(len(books), 1)
#         # Asserting the title of the first book
#         self.assertEqual(books[0]['title'], "Test Book")
#         # Asserting that the image content exists in the book data
#         self.assertIn('image', books[0])
#         # Asserting the correct authors are included in the returned data
#         self.assertEqual(books[0]['author'], "Author One, Author Two")

#     @patch('boipoka_app.views.requests.get')
#     def test_fetch_books_data_failure(self, mock_get):
#         """Test fetch_books_data for a failed API call."""
#         # Mocking a failed API response with a 404 status code
#         mock_get.return_value.status_code = 404
        
#         # Calling the fetch_books_data function, which should handle the failure
#         books = fetch_books_data()
        
#         # Asserting that no books are returned when the API call fails
#         self.assertEqual(books, [])

#     def test_create_books_in_db(self):
#         """Test create_books_in_db function."""
#         # Creating a mock list of book data to be inserted into the database
#         book_list = [
#             {
#                 'title': 'Test Book',
#                 'author': 'Test Author',
#                 'description': 'Test Description',
#                 'image': None,  # The image could be mocked or set to None
#                 'availability_status': True,
#                 'total_copies': 1,
#                 'available_copies': 1,
#             }
#         ]

#         # Calling the function to create books in the database
#         create_books_in_db(book_list)
        
#         # Asserting that one book is created in the database
#         self.assertEqual(Book.objects.count(), 1)
#         # Fetching the first book to assert its data
#         book = Book.objects.first()
#         self.assertEqual(book.title, 'Test Book')
#         self.assertEqual(book.author, 'Test Author')


# class BookListViewTests(TestCase):
#     """Test cases for the book_list view."""

#     def setUp(self):
#         """Create a user and log them in for testing."""
#         # Creating a user for testing purposes
#         self.username = 'testuser'
#         self.password = 'testpassword'
#         self.user = User.objects.create_user(username=self.username, password=self.password)
#         # Logging in the created user using Django's test client
#         self.client.login(username=self.username, password=self.password)

#     @patch('boipoka_app.views.fetch_books_data')
#     @patch('boipoka_app.views.create_books_in_db')
#     def test_book_list_view(self, mock_create_books, mock_fetch_books):
#         """Test that the book list view returns the correct response."""
#         # Creating mock book data to simulate the response from fetch_books_data
#         mock_books = [
#             {
#                 'title': 'Mock Book',
#                 'author': 'Mock Author',
#                 'description': 'Mock Description',
#                 'image': 'path/to/mock_image.jpg',  # Simulating an image path
#                 'availability_status': True,
#                 'total_copies': 1,
#                 'available_copies': 1,
#             }
#         ]
        
#         # Mocking the fetch_books_data function to return the mock book data
#         mock_fetch_books.return_value = mock_books
#         # Mocking the create_books_in_db function to do nothing (return None)
#         mock_create_books.return_value = None

#         # Creating a book record in the database using the mock data
#         for book in mock_books:
#             Book.objects.create(**book)

#         # Sending a GET request to the book_list view
#         response = self.client.get(reverse('boipoka_app:book_list'))

#         # Asserting that the response status code is 200 (success)
#         self.assertEqual(response.status_code, 200)
#         # Asserting that the correct template is used for rendering the view
#         self.assertTemplateUsed(response, 'boipoka_app/book_list.html')
#         # Asserting that the mocked book title appears in the rendered HTML
#         self.assertContains(response, 'Mock Book')
#         # Asserting that the mocked author name appears in the rendered HTML
#         self.assertContains(response, 'Mock Author')

#         # Asserting that the image path is included in the rendered HTML
#         self.assertContains(response, 'path/to/mock_image.jpg')

#     @patch('boipoka_app.views.fetch_books_data')
#     @patch('boipoka_app.views.create_books_in_db')
#     def test_book_list_view_no_books(self, mock_create_books, mock_fetch_books):
#         """Test book list view when no books are returned."""
#         # Mocking fetch_books_data to return an empty list (no books)
#         mock_fetch_books.return_value = []
#         # Mocking create_books_in_db to do nothing (return None)
#         mock_create_books.return_value = None

#         # Sending a GET request to the book_list view
#         response = self.client.get(reverse('boipoka_app:book_list'))

#         # Asserting that the response status code is 200 (success)
#         self.assertEqual(response.status_code, 200)
#         # Asserting that the correct template is used for rendering the view
#         self.assertTemplateUsed(response, 'boipoka_app/book_list.html')
#         # Asserting that the 'No books available' message is displayed in the rendered HTML
#         self.assertContains(response, 'No books available')



# class BookDetailsViewTest(TestCase):

#     def setUp(self):
#         # Create a user and a subscription for testing
#         self.user = User.objects.create_user(username='testuser', password='password123')
#         self.subscription = Subscription.objects.create(
#             user=self.user,
#             subscription_type='Basic',  # Use 'subscription_type' instead of 'tier'
#             subscription_start=timezone.now()
#         )
#         self.book = Book.objects.create(title='Test Book', author='Author Name', description='Book Description', available=True)

#         # Create a second user for borrowing scenarios
#         self.second_user = User.objects.create_user(username='anotheruser', password='password456')

#     def test_book_available_not_borrowed(self):
#         self.client.login(username='testuser', password='password123')
#         response = self.client.get(reverse('book_details', args=[self.book.pk]))
        
#         self.assertEqual(response.status_code, 200)
#         self.assertContains(response, self.book.title)
#         self.assertTrue(response.context['availability'])  # Book should be available
#         self.assertFalse(response.context['is_borrowed'])  # User has not borrowed the book

#     def test_book_borrowed_by_user(self):
#         # Simulate borrowing the book
#         Borrowing.objects.create(user=self.user, book=self.book, due_date=timezone.now() + timedelta(days=14))
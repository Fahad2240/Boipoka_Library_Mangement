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
from .models import Book, Borrowing, Subscription

# Importing fetch_books_data and create_books_in_db functions from views
from .views import fetch_books_data, create_books_in_db

# Importing json for handling JSON data
import json

# Getting the custom User model
User = get_user_model()

# Defining test cases for the Boipoka app
class BoipokaAppTests(TestCase):

    # Test case for the 'index' view
    def test_index_view(self):
        """
        Test the index view returns a 200 status code and the correct template.
        """
        # Reverse the URL for the 'index' view and send a GET request
        response = self.client.get(reverse('boipoka_app:index'))
        
        # Check if the status code is 200 (OK)
        self.assertEqual(response.status_code, 200)
        
        # Ensure the correct template is used
        self.assertTemplateUsed(response, 'boipoka_app/index.html')

    # Test case for the 'register' view when accessed via GET request
    def test_register_view_get(self):
        """
        Test the register view with a GET request returns a 200 status code
        and the registration form.
        """
        # Reverse the URL for the 'register' view and send a GET request
        response = self.client.get(reverse('boipoka_app:register'))
        
        # Check if the status code is 200 (OK)
        self.assertEqual(response.status_code, 200)
        
        # Ensure the correct template is used
        self.assertTemplateUsed(response, 'boipoka_app/register.html')
        
        # Check if the form in the response context is an instance of CustomUserCreationForm
        self.assertIsInstance(response.context['form'], CustomUserCreationForm)

    # Test case for the 'register' view when invalid data is submitted via POST request
    def test_register_view_post_invalid(self):
        # Create invalid form data with missing username, invalid password, and email
        form_data = {
            'username': '',  # Invalid data
            'password1': 'short',  # Invalid password
            'password2': 'short',
            'email': '',  # Invalid email
        }
        
        # Send a POST request with invalid data
        response = self.client.post(reverse('boipoka_app:register'), form_data)

        # Print status code and response content for debugging purposes
        print(f'Status Code: {response.status_code}')
        print(f'Response Content: {response.content.decode()}')

        # Check if there's a redirect (in case of 302)
        if response.status_code == 302:
            # Follow the redirect and print status
            response = self.client.get(response.url)
            print("Redirect detected. Following the redirect...")

        # Check if the response is still 200 (form should be re-rendered with errors)
        self.assertEqual(response.status_code, 200)

        # Get the form from the response context
        form = response.context.get('form')
        
        # Ensure the form is in the context
        self.assertIsNotNone(form, "Form not found in response context.")

        # Assert specific errors on form fields
        self.assertFormError(response, 'form', 'username', 'This field is required.')
        self.assertFormError(response, 'form', 'email', 'This field is required.')
        self.assertFormError(response, 'form', 'password1', 'This password is too short. It must contain at least 8 characters.')

    # Test case for the 'register' view when valid data is submitted via POST request
    def test_register_view_post_valid(self):
        # Create valid form data
        form_data = {
            'username': 'testuser',
            'password1': 'secure_password',
            'password2': 'secure_password',
            'email': 'testuser@example.com',  # Ensure email is included
        }
        # Send a POST request with valid data
        response = self.client.post(reverse('boipoka_app:register'), data=form_data)

        # Check if the user was successfully created in the database
        self.assertTrue(User.objects.filter(username='testuser').exists(), "User was not created.")
        
        # Ensure the user is redirected to the login page after successful registration
        self.assertRedirects(response, reverse('boipoka_app:login'))

    # Test case for the 'register' view when a required field is missing in the POST request
    def test_register_view_post_missing_field(self):
        """
        Test the register view with a POST request where a required field is missing.
        It should not create a user and should show form validation errors.
        """
        # Create form data with missing username field
        form_data = {
            'username': '',  # Missing username
            'password1': 'TestPassword123',
            'password2': 'TestPassword123',
        }
        # Send a POST request with incomplete data
        response = self.client.post(reverse('boipoka_app:register'), form_data)

        # Ensure no user was created due to missing field
        self.assertFalse(User.objects.filter(username='').exists())

        # Check that the form is re-rendered with validation errors
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'boipoka_app/register.html')
        self.assertIsInstance(response.context['form'], CustomUserCreationForm)
        self.assertTrue(response.context['form'].errors)

    # Test case for the 'register' view when a user is already authenticated
    def test_register_view_authenticated_user(self):
        """
        Test the register view when the user is already authenticated.
        The user should be redirected away from the registration page.
        """
        # Create and log in a test user
        user = User.objects.create_user(username='testuser', password='TestPassword123')
        self.client.login(username='testuser', password='TestPassword123')

        # Try accessing the register page while logged in
        response = self.client.get(reverse('boipoka_app:register'))

        # Ensure the user is redirected away since they are already authenticated
        self.assertRedirects(response, '/')

# Define test cases for the login view
class LoginViewTests(TestCase):
    
    def setUp(self):
        # Create a test user for login tests
        self.username = 'testuser'
        self.password = 'testpassword'
        self.user = User.objects.create_user(username=self.username, password=self.password)

    # Test case for successful login
    def test_login_view_success(self):
        """Test that a user can log in successfully."""
        # Send POST request with valid login credentials
        response = self.client.post(reverse('boipoka_app:login'), {
            'username': self.username,
            'password': self.password
        })
        # Ensure the user is redirected to the book list view
        self.assertRedirects(response, reverse('boipoka_app:book_list'))
        # Verify that the user is authenticated
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    # Test case for login with invalid credentials
    def test_login_view_invalid_credentials(self):
        """Test that login fails with invalid credentials."""
        # Send POST request with invalid credentials
        response = self.client.post(reverse('boipoka_app:login'), {
            'username': 'wronguser',
            'password': 'wrongpassword'
        })
        # Ensure the response is 200 and the form re-renders with an error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid credentials')
        # Ensure the user is not authenticated
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    # Test case to check the GET request for login page
    def test_login_view_get(self):
        """Test that GET requests return the login page."""
        # Send a GET request to the login page
        response = self.client.get(reverse('boipoka_app:login'))
        # Check if the response status code is 200
        self.assertEqual(response.status_code, 200)
        # Ensure the correct template is used
        self.assertTemplateUsed(response, 'boipoka_app/login.html')

# Define test cases for the logout view
class LogoutViewTests(TestCase):
    
    def setUp(self):
        """Create a user and log them in for testing."""
        self.username = 'testuser'
        self.password = 'testpassword'
        self.user = User.objects.create_user(username=self.username, password=self.password)
        # Log in the user
        self.client.login(username=self.username, password=self.password)

    # Test case to ensure the user can log out
    def test_logout_view(self):
        """Test that the user can log out successfully."""
        # Send a GET request to the logout view
        response = self.client.get(reverse('boipoka_app:logout'))
        # Ensure the user is redirected to the index page after logout
        self.assertRedirects(response, reverse('boipoka_app:index'))
        # Verify that the user is no longer authenticated
        self.assertFalse(response.wsgi_request.user.is_authenticated)



class BookDataTests(TestCase):
    """Test cases for fetching and creating book data."""

    @patch('boipoka_app.views.requests.get')
    def test_fetch_books_data_success(self, mock_get):
        """Test fetch_books_data for a successful API call."""
        # Mocking the API response with successful status code (200)
        mock_get.return_value.status_code = 200
        # Mocking the JSON response for the books data
        mock_get.return_value.json.return_value = {
            "items": [
                {
                    "volumeInfo": {
                        "title": "Test Book",
                        "authors": ["Author One", "Author Two"],
                        "description": "A test description.",
                        "imageLinks": {
                            "thumbnail": "http://example.com/test_book_thumbnail.jpg"
                        }
                    }
                }
            ]
        }

        # Mocking the image response for the book cover thumbnail
        mock_image_response = Mock()
        mock_image_response.status_code = 200
        # Mocking the image content as bytes (representing an image)
        mock_image_response.content = b'This is a mock image content'
        
        # Patching 'requests.get' to return both the mocked JSON data and image response
        with patch('boipoka_app.views.requests.get', side_effect=[mock_get.return_value, mock_image_response]):
            books = fetch_books_data()
        
        # Asserting that one book is returned from the API
        self.assertEqual(len(books), 1)
        # Asserting the title of the first book
        self.assertEqual(books[0]['title'], "Test Book")
        # Asserting that the image content exists in the book data
        self.assertIn('image', books[0])
        # Asserting the correct authors are included in the returned data
        self.assertEqual(books[0]['author'], "Author One, Author Two")

    @patch('boipoka_app.views.requests.get')
    def test_fetch_books_data_failure(self, mock_get):
        """Test fetch_books_data for a failed API call."""
        # Mocking a failed API response with a 404 status code
        mock_get.return_value.status_code = 404
        
        # Calling the fetch_books_data function, which should handle the failure
        books = fetch_books_data()
        
        # Asserting that no books are returned when the API call fails
        self.assertEqual(books, [])

    def test_create_books_in_db(self):
        """Test create_books_in_db function."""
        # Creating a mock list of book data to be inserted into the database
        book_list = [
            {
                'title': 'Test Book',
                'author': 'Test Author',
                'description': 'Test Description',
                'image': None,  # The image could be mocked or set to None
                'availability_status': True,
                'total_copies': 1,
                'available_copies': 1,
            }
        ]

        # Calling the function to create books in the database
        create_books_in_db(book_list)
        
        # Asserting that one book is created in the database
        self.assertEqual(Book.objects.count(), 1)
        # Fetching the first book to assert its data
        book = Book.objects.first()
        self.assertEqual(book.title, 'Test Book')
        self.assertEqual(book.author, 'Test Author')


class BookListViewTests(TestCase):
    """Test cases for the book_list view."""

    def setUp(self):
        """Create a user and log them in for testing."""
        # Creating a user for testing purposes
        self.username = 'testuser'
        self.password = 'testpassword'
        self.user = User.objects.create_user(username=self.username, password=self.password)
        # Logging in the created user using Django's test client
        self.client.login(username=self.username, password=self.password)

    @patch('boipoka_app.views.fetch_books_data')
    @patch('boipoka_app.views.create_books_in_db')
    def test_book_list_view(self, mock_create_books, mock_fetch_books):
        """Test that the book list view returns the correct response."""
        # Creating mock book data to simulate the response from fetch_books_data
        mock_books = [
            {
                'title': 'Mock Book',
                'author': 'Mock Author',
                'description': 'Mock Description',
                'image': 'path/to/mock_image.jpg',  # Simulating an image path
                'availability_status': True,
                'total_copies': 1,
                'available_copies': 1,
            }
        ]
        
        # Mocking the fetch_books_data function to return the mock book data
        mock_fetch_books.return_value = mock_books
        # Mocking the create_books_in_db function to do nothing (return None)
        mock_create_books.return_value = None

        # Creating a book record in the database using the mock data
        for book in mock_books:
            Book.objects.create(**book)

        # Sending a GET request to the book_list view
        response = self.client.get(reverse('boipoka_app:book_list'))

        # Asserting that the response status code is 200 (success)
        self.assertEqual(response.status_code, 200)
        # Asserting that the correct template is used for rendering the view
        self.assertTemplateUsed(response, 'boipoka_app/book_list.html')
        # Asserting that the mocked book title appears in the rendered HTML
        self.assertContains(response, 'Mock Book')
        # Asserting that the mocked author name appears in the rendered HTML
        self.assertContains(response, 'Mock Author')

        # Asserting that the image path is included in the rendered HTML
        self.assertContains(response, 'path/to/mock_image.jpg')

    @patch('boipoka_app.views.fetch_books_data')
    @patch('boipoka_app.views.create_books_in_db')
    def test_book_list_view_no_books(self, mock_create_books, mock_fetch_books):
        """Test book list view when no books are returned."""
        # Mocking fetch_books_data to return an empty list (no books)
        mock_fetch_books.return_value = []
        # Mocking create_books_in_db to do nothing (return None)
        mock_create_books.return_value = None

        # Sending a GET request to the book_list view
        response = self.client.get(reverse('boipoka_app:book_list'))

        # Asserting that the response status code is 200 (success)
        self.assertEqual(response.status_code, 200)
        # Asserting that the correct template is used for rendering the view
        self.assertTemplateUsed(response, 'boipoka_app/book_list.html')
        # Asserting that the 'No books available' message is displayed in the rendered HTML
        self.assertContains(response, 'No books available')



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